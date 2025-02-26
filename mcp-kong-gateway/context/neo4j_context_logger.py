from neo4j import GraphDatabase
import json
import uuid

class Neo4jContextLogger:
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def log_api_interaction(self, service, request, response):
        """Log API interactions to Neo4j knowledge graph"""
        with self._driver.session() as session:
            query = """
            CREATE (interaction:APIInteraction {
                id: ,
                service: ,
                timestamp: datetime(),
                request: ,
                response: 
            })
            """
            
            session.run(query, {
                'interaction_id': str(uuid.uuid4()),
                'service': service,
                'request': json.dumps(request),
                'response': json.dumps(response)
            })
    
    def get_interaction_history(self, service=None):
        """Retrieve interaction history"""
        with self._driver.session() as session:
            query = "MATCH (i:APIInteraction) " +                     ("WHERE i.service =  " if service else "") +                     "RETURN i ORDER BY i.timestamp DESC LIMIT 100"
            
            result = session.run(query, {'service': service} if service else {})
            return [record['i'] for record in result]

# Example Usage
if __name__ == '__main__':
    logger = Neo4jContextLogger("bolt://localhost:7687", "neo4j", "password")
    logger.log_api_interaction('memory-mcp', 
                               {'query': 'retrieve context'}, 
                               {'status': 'success'})
