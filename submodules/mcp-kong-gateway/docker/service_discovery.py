import json
import os
import requests
from typing import Dict, List

class MCPServiceDiscovery:
    def __init__(self, kong_admin_url='http://localhost:8001'):
        self.kong_admin_url = kong_admin_url
        self.services = {}
    
    def register_service(self, name: str, url: str, routes: List[Dict]):
        service_payload = {
            'name': name,
            'url': url
        }
        
        # Register service
        response = requests.post(f'{self.kong_admin_url}/services', json=service_payload)
        
        # Register routes
        for route in routes:
            route_payload = {
                'service': {'name': name},
                **route
            }
            requests.post(f'{self.kong_admin_url}/routes', json=route_payload)
        
        return response.json()

    def list_services(self):
        response = requests.get(f'{self.kong_admin_url}/services')
        return response.json()

# Example Usage
if __name__ == '__main__':
    discovery = MCPServiceDiscovery()
    services = [
        {
            'name': 'memory-mcp',
            'url': 'http://memory-service:8080',
            'routes': [{'paths': ['/memory']}]
        }
    ]
