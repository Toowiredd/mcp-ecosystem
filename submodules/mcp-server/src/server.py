from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from neo4j import GraphDatabase
import asyncio
import json
from typing import Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator, constr
import logging
import os
from uuid import UUID, uuid4

# Rate limiting imports
import aioredis
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Model Context Protocol Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Neo4j configuration
NEO4J_URI = os.getenv("MCP_NEO4J_URI", "neo4j://neo4j:7687")
NEO4J_USER = os.getenv("MCP_NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("MCP_NEO4J_PASSWORD", "password")

# Initialize Neo4j driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Remaining connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                await self.disconnect(connection)

manager = ConnectionManager()

# Custom exceptions
class ContextValidationError(Exception):
    def __init__(self, message: str):
        self.message = message

# Context models
class ContextContent(BaseModel):
    """Validated content model for context updates"""
    @validator('*')
    def no_null_values(cls, v):
        if v is None:
            raise ValueError('null values not allowed')
        return v

    class Config:
        extra = 'forbid'  # Prevent additional fields
        
class ContextUpdate(BaseModel):
    session_id: UUID = Field(default_factory=uuid4)
    context_type: constr(min_length=1, max_length=50) = Field(
        ...,
        description='Type of context being updated'
    )
    content: Dict[str, Union[str, int, float, bool, List, Dict]] = Field(
        ...,
        description='Context content'
    )
    timestamp: float = Field(
        default_factory=lambda: datetime.utcnow().timestamp(),
        description='UTC timestamp of update'
    )

    @validator('content')
    def validate_content(cls, v):
        # Ensure content isn't empty
        if not v:
            raise ValueError('content cannot be empty')
        # Validate nested structure
        ContextContent(**v)
        return v

    @validator('context_type')
    def validate_context_type(cls, v):
        if not v.isalnum() and not '_' in v:
            raise ValueError('context_type must be alphanumeric with optional underscores')
        return v

class QueryContext(BaseModel):
    session_id: UUID
    context_type: Optional[constr(min_length=1, max_length=50)] = Field(
        None,
        description='Optional type of context to query'
    )

    @validator('context_type')
    def validate_context_type(cls, v):
        if v is not None:
            if not v.isalnum() and not '_' in v:
                raise ValueError('context_type must be alphanumeric with optional underscores')
        return v

# Neo4j context operations
def save_context(tx, context: ContextUpdate):
    query = """
    MERGE (s:Session {id: $session_id})
    CREATE (c:Context {
        type: $context_type,
        content: $content,
        timestamp: $timestamp
    })
    CREATE (s)-[:HAS_CONTEXT]->(c)
    RETURN c
    """
    try:
        result = tx.run(
            query,
            session_id=str(context.session_id),  # Convert UUID to string
            context_type=context.context_type,
            content=context.content,
            timestamp=context.timestamp
        )
        record = result.single()
        if not record:
            raise ContextValidationError("Failed to create context")
        return record["c"]  # Return created context node
    except Exception as e:
        raise ContextValidationError(f"Database error: {str(e)}")

def get_context(tx, session_id: UUID, context_type: Optional[str] = None):
    query = """
    MATCH (s:Session {id: $session_id})-[:HAS_CONTEXT]->(c:Context)
    WHERE $context_type IS NULL OR c.type = $context_type
    RETURN c.type as type, c.content as content, c.timestamp as timestamp
    ORDER BY c.timestamp DESC
    """
    try:
        result = tx.run(query, session_id=str(session_id), context_type=context_type)
        return [record.data() for record in result]
    except Exception as e:
        raise ContextValidationError(f"Database error: {str(e)}")

# Exception handlers
@app.exception_handler(ContextValidationError)
async def context_validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Context validation error",
            "detail": exc.message
        }
    )

# API endpoints
@app.post("/context", status_code=status.HTTP_201_CREATED)
@RateLimiter(times=10, seconds=60)  # 10 requests per minute
async def update_context(context: ContextUpdate, request: Request):
    try:
        with driver.session() as session:
            result = session.write_transaction(save_context, context)
            
        # Notify connected clients
        await manager.broadcast({
            "type": "context_update",
            "session_id": str(context.session_id),
            "context_type": context.context_type,
            "timestamp": context.timestamp
        })
        
        return {
            "status": "success",
            "message": "Context updated successfully",
            "session_id": str(context.session_id),
            "context_type": context.context_type
        }
    except Exception as e:
        logger.error(f"Error updating context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/context/{session_id}")
@RateLimiter(times=30, seconds=60)  # 30 requests per minute
async def get_session_context(session_id: UUID, context_type: Optional[str] = None, request: Request):
    try:
        with driver.session() as session:
            contexts = session.read_transaction(get_context, session_id, context_type)
        
        if not contexts:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": "No contexts found",
                    "session_id": str(session_id),
                    "context_type": context_type
                }
            )
            
        return {
            "status": "success",
            "session_id": str(session_id),
            "contexts": contexts
        }
    except Exception as e:
        logger.error(f"Error retrieving context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await manager.connect(websocket)
        while True:
            try:
                data = await websocket.receive_text()
                # Validate incoming data
                try:
                    parsed_data = json.loads(data)
                    if not isinstance(parsed_data, dict):
                        raise ValueError("Message must be a JSON object")
                    if "type" not in parsed_data:
                        raise ValueError("Message must include 'type' field")
                    
                    # Broadcast validated message
                    await manager.broadcast({
                        "type": parsed_data["type"],
                        "data": parsed_data,
                        "timestamp": datetime.utcnow().timestamp()
                    })
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "error": "Invalid JSON format",
                        "timestamp": datetime.utcnow().timestamp()
                    })
                except ValueError as e:
                    await websocket.send_json({
                        "error": str(e),
                        "timestamp": datetime.utcnow().timestamp()
                    })
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                await websocket.send_json({
                    "error": "Internal server error",
                    "timestamp": datetime.utcnow().timestamp()
                })
                break
    finally:
        manager.disconnect(websocket)
        logger.info("WebSocket connection closed")

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    # Initialize rate limiter
    try:
        redis = aioredis.from_url(
            os.getenv("REDIS_URL", "redis://redis:6379"),
            encoding="utf-8",
            decode_responses=True
        )
        await FastAPILimiter.init(redis)
        logger.info("Rate limiter initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize rate limiter: {str(e)}")
        raise e

    # Verify Neo4j connection
    try:
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()["count"]
            logger.info(f"Connected to Neo4j. Database has {count} nodes.")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {str(e)}")
        raise e

@app.on_event("shutdown")
async def shutdown_event():
    driver.close()
    logger.info("Shutting down server")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
