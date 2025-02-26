from neo4j import GraphDatabase
from typing import Dict, List, Optional
import logging
import os

logger = logging.getLogger(__name__)

class Neo4jManager:
    def __init__(self):
        self.uri = os.getenv("MCP_NEO4J_URI", "neo4j://neo4j:7687")
        self.user = os.getenv("MCP_NEO4J_USER", "neo4j")
        self.password = os.getenv("MCP_NEO4J_PASSWORD", "password")
        self.driver = None

    def connect(self):
        if not self.driver:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password)
            )
        return self.driver

    def close(self):
        if self.driver:
            self.driver.close()
            self.driver = None

    def save_context(self, session_id: str, context_type: str, content: Dict, timestamp: float):
        with self.connect().session() as session:
            result = session.write_transaction(self._save_context_tx, 
                                            session_id, 
                                            context_type, 
                                            content, 
                                            timestamp)
            return result

    def get_context(self, session_id: str, context_type: Optional[str] = None):
        with self.connect().session() as session:
            result = session.read_transaction(self._get_context_tx,
                                           session_id,
                                           context_type)
            return result

    def get_related_contexts(self, session_id: str, context_type: str, max_depth: int = 2):
        with self.connect().session() as session:
            result = session.read_transaction(self._get_related_contexts_tx,
                                           session_id,
                                           context_type,
                                           max_depth)
            return result

    @staticmethod
    def _save_context_tx(tx, session_id: str, context_type: str, content: Dict, timestamp: float):
        query = """
        MERGE (s:Session {id: $session_id})
        CREATE (c:Context {
            type: $context_type,
            content: $content,
            timestamp: $timestamp
        })
        CREATE (s)-[:HAS_CONTEXT]->(c)
        WITH c
        MATCH (c2:Context)
        WHERE c2.timestamp < c.timestamp
        AND abs(c2.timestamp - c.timestamp) < 300000  // Related within 5 minutes
        CREATE (c)-[:RELATED_TO]->(c2)
        RETURN c
        """
        result = tx.run(query,
                       session_id=session_id,
                       context_type=context_type,
                       content=content,
                       timestamp=timestamp)
        return result.single()

    @staticmethod
    def _get_context_tx(tx, session_id: str, context_type: Optional[str]):
        query = """
        MATCH (s:Session {id: $session_id})-[:HAS_CONTEXT]->(c:Context)
        WHERE $context_type IS NULL OR c.type = $context_type
        RETURN c.type as type, c.content as content, c.timestamp as timestamp
        ORDER BY c.timestamp DESC
        """
        result = tx.run(query,
                       session_id=session_id,
                       context_type=context_type)
        return [record.data() for record in result]

    @staticmethod
    def _get_related_contexts_tx(tx, session_id: str, context_type: str, max_depth: int):
        query = """
        MATCH (s:Session {id: $session_id})-[:HAS_CONTEXT]->(c:Context {type: $context_type})
        CALL apoc.path.subgraphAll(c, {
            relationshipFilter: "RELATED_TO",
            maxLevel: $max_depth
        })
        YIELD nodes, relationships
        RETURN nodes, relationships
        """
        result = tx.run(query,
                       session_id=session_id,
                       context_type=context_type,
                       max_depth=max_depth)
        return [record.data() for record in result]
