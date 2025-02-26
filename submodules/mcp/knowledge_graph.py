from neo4j import GraphDatabase
import uuid
from datetime import datetime
import json
import logging

class MCPKnowledgeGraph:
    def __init__(self, uri='bolt://0.0.0.0:7687', user='neo4j', password='contextmcp'):
        """
        Initialize Neo4j connection for MCP Knowledge Graph.
        
        Args:
            uri (str): Neo4j connection URI
            user (str): Neo4j username
            password (str): Neo4j password
        """
        try:
            self._driver = GraphDatabase.driver(uri, auth=(user, password))
            logging.info(f"🔗 Connected to Neo4j Knowledge Graph at {uri}")
        except Exception as e:
            logging.error(f"❌ Neo4j Connection Failed: {e}")
            raise
    
    def create_service_node(self, service_name, service_type, capabilities):
        """
        Create a service node in the knowledge graph.
        
        Args:
            service_name (str): Name of the service
            service_type (str): Type of service
            capabilities (list): List of service capabilities
        
        Returns:
            dict: Created service node details
        """
        with self._driver.session() as session:
            try:
                query = '''
                MERGE (s:Service {name: $name})
                SET s.type = $type, 
                    s.capabilities = $capabilities,
                    s.created_at = datetime()
                RETURN s
                '''
                result = session.run(query, {
                    'name': service_name, 
                    'type': service_type, 
                    'capabilities': json.dumps(capabilities)
                })
                node = dict(result.single()[0])
                logging.info(f"✅ Created Service Node: {service_name}")
                return node
            except Exception as e:
                logging.error(f"❌ Service Node Creation Failed: {e}")
                raise
    
    def log_service_interaction(self, service_name, interaction_type, details):
        """
        Log a service interaction in the knowledge graph.
        
        Args:
            service_name (str): Name of the service
            interaction_type (str): Type of interaction
            details (dict): Interaction details
        
        Returns:
            dict: Created interaction node details
        """
        with self._driver.session() as session:
            try:
                interaction_id = str(uuid.uuid4())
                query = '''
                MATCH (s:Service {name: $service_name})
                CREATE (i:Interaction {
                    id: $interaction_id,
                    type: $interaction_type,
                    details: $details,
                    timestamp: datetime()
                })
                CREATE (s)-[:HAS_INTERACTION]->(i)
                RETURN i
                '''
                result = session.run(query, {
                    'service_name': service_name,
                    'interaction_id': interaction_id,
                    'interaction_type': interaction_type,
                    'details': json.dumps(details)
                })
                node = dict(result.single()[0])
                logging.info(f"📝 Logged Interaction: {interaction_type} for {service_name}")
                return node
            except Exception as e:
                logging.error(f"❌ Service Interaction Logging Failed: {e}")
                raise
    
    def get_service_interaction_history(self, service_name, limit=10):
        """
        Retrieve interaction history for a service.
        
        Args:
            service_name (str): Name of the service
            limit (int): Maximum number of interactions to retrieve
        
        Returns:
            list: List of interaction node details
        """
        with self._driver.session() as session:
            try:
                query = '''
                MATCH (s:Service {name: $service_name})-[:HAS_INTERACTION]->(i:Interaction)
                RETURN i
                ORDER BY i.timestamp DESC
                LIMIT $limit
                '''
                result = session.run(query, {
                    'service_name': service_name,
                    'limit': limit
                })
                interactions = [dict(record['i']) for record in result]
                logging.info(f"🔍 Retrieved {len(interactions)} interactions for {service_name}")
                return interactions
            except Exception as e:
                logging.error(f"❌ Interaction History Retrieval Failed: {e}")
                raise
    
    def close(self):
        """Close the Neo4j driver connection."""
        self._driver.close()
        logging.info("🔌 Closed Neo4j Knowledge Graph Connection")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():
    """Demonstration of Knowledge Graph functionality"""
    kg = MCPKnowledgeGraph()
    
    # Create Service Nodes
    memory_mcp = kg.create_service_node(
        'memory-mcp', 
        'context-management', 
        ['memory-storage', 'context-retrieval', 'semantic-linking']
    )
    vision_mcp = kg.create_service_node(
        'vision-mcp', 
        'image-processing', 
        ['object-detection', 'image-analysis', 'visual-context']
    )

    # Log Service Interactions
    interaction1 = kg.log_service_interaction(
        'memory-mcp', 
        'context-retrieval', 
        {'query': 'retrieve project context', 'success': True}
    )
    interaction2 = kg.log_service_interaction(
        'vision-mcp', 
        'object-detection', 
        {'image_source': 'project_diagram', 'detected_objects': 3}
    )

    # Retrieve Interaction History
    memory_interactions = kg.get_service_interaction_history('memory-mcp')
    vision_interactions = kg.get_service_interaction_history('vision-mcp')

    print('\nMemory MCP Interactions:')
    for interaction in memory_interactions:
        print(f'  - Type: {interaction["type"]}, Details: {interaction["details"]}')

    print('\nVision MCP Interactions:')
    for interaction in vision_interactions:
        print(f'  - Type: {interaction["type"]}, Details: {interaction["details"]}')

    kg.close()

if __name__ == '__main__':
    main()
