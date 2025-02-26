import asyncio
import aiohttp
from typing import Dict, List, Any
from dataclasses import dataclass, field

@dataclass
class ServiceConfig:
    name: str
    base_url: str
    auth_token: str = ''
    retry_limit: int = 3
    timeout: float = 10.0
    dependencies: List[str] = field(default_factory=list)

class ServiceOrchestrator:
    def __init__(self):
        self.services: Dict[str, ServiceConfig] = {}
        self.service_status: Dict[str, bool] = {}
    
    def register_service(self, service: ServiceConfig):
        """Register a service with its configuration"""
        self.services[service.name] = service
        self.service_status[service.name] = False
    
    async def health_check(self, service_name: str) -> bool:
        """Perform health check for a specific service"""
        service = self.services.get(service_name)
        if not service:
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{service.base_url}/health", 
                    timeout=aiohttp.ClientTimeout(total=service.timeout)
                ) as response:
                    self.service_status[service_name] = response.status == 200
                    return response.status == 200
        except Exception:
            self.service_status[service_name] = False
            return False
    
    async def orchestrate_request(self, primary_service: str, request_data: Dict[str, Any]) -> Dict:
        """Orchestrate a request across multiple services"""
        # Validate service dependencies
        primary_service_config = self.services.get(primary_service)
        if not primary_service_config:
            raise ValueError(f"Service {primary_service} not registered")
        
        # Check dependencies health
        for dependency in primary_service_config.dependencies:
            if not await self.health_check(dependency):
                raise RuntimeError(f"Dependency {dependency} is unhealthy")
        
        # Perform primary service request
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{primary_service_config.base_url}/process",
                json=request_data,
                headers={'Authorization': f'Bearer {primary_service_config.auth_token}'},
                timeout=aiohttp.ClientTimeout(total=primary_service_config.timeout)
            ) as response:
                return await response.json()
    
    async def run_comprehensive_health_check(self):
        """Run health checks for all registered services"""
        health_checks = [self.health_check(service) for service in self.services]
        return await asyncio.gather(*health_checks)

# Example Usage
if __name__ == '__main__':
    orchestrator = ServiceOrchestrator()
    
    # Register services
    orchestrator.register_service(ServiceConfig(
        name='memory-mcp',
        base_url='http://memory-service:8080',
        dependencies=['neo4j']
    ))
    
    orchestrator.register_service(ServiceConfig(
        name='neo4j',
        base_url='http://neo4j:7474',
        timeout=5.0
    ))
    
    # Run async health checks
    async def main():
        health_results = await orchestrator.run_comprehensive_health_check()
        print("Service Health:", health_results)
        
        # Example request orchestration
        try:
            result = await orchestrator.orchestrate_request(
                'memory-mcp', 
                {'action': 'retrieve_context', 'query': 'recent_interactions'}
            )
            print("Orchestration Result:", result)
        except Exception as e:
            print(f"Orchestration failed: {e}")
    
    asyncio.run(main())
