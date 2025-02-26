import json
import networkx as nx
from typing import Dict, Any

class ContextualRouter:
    def __init__(self):
        self.context_graph = nx.DiGraph()
        self.service_mappings = {}
    
    def register_service_context(self, service_name: str, context_tags: list):
        """Register service with contextual tags"""
        self.service_mappings[service_name] = context_tags
        
        # Create graph connections based on context similarity
        for tag in context_tags:
            self.context_graph.add_node(tag)
    
    def route_request(self, request_context: Dict[str, Any]) -> str:
        """Intelligent routing based on context similarity"""
        best_match = None
        max_similarity = 0
        
        for service, tags in self.service_mappings.items():
            similarity = self._calculate_context_similarity(request_context, tags)
            if similarity > max_similarity:
                max_similarity = similarity
                best_match = service
        
        return best_match
    
    def _calculate_context_similarity(self, request_context: Dict, service_tags: list) -> float:
        """Calculate context similarity using graph-based approach"""
        matching_tags = set(request_context.keys()) & set(service_tags)
        return len(matching_tags) / len(service_tags)

# Example Usage
if __name__ == '__main__':
    router = ContextualRouter()
    router.register_service_context('memory-mcp', ['context', 'storage', 'retrieval'])
    router.register_service_context('vision-mcp', ['image', 'processing', 'analysis'])
    
    sample_request = {'context': True, 'type': 'memory_retrieval'}
    best_service = router.route_request(sample_request)
    print(f"Best matched service: {best_service}")
