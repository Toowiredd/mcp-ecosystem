import time
import statistics
from typing import Dict, List

class APIPerformanceMonitor:
    def __init__(self):
        self.service_metrics = {}
    
    def track_request(self, service: str, start_time: float, end_time: float):
        """Track request performance for a service"""
        duration = end_time - start_time
        
        if service not in self.service_metrics:
            self.service_metrics[service] = {
                'durations': [],
                'total_requests': 0,
                'error_count': 0
            }
        
        metrics = self.service_metrics[service]
        metrics['durations'].append(duration)
        metrics['total_requests'] += 1
    
    def get_service_performance(self, service: str) -> Dict:
        """Generate performance report for a service"""
        if service not in self.service_metrics:
            return {}
        
        metrics = self.service_metrics[service]
        return {
            'avg_response_time': statistics.mean(metrics['durations']) if metrics['durations'] else 0,
            'total_requests': metrics['total_requests'],
            'error_rate': metrics['error_count'] / metrics['total_requests'] if metrics['total_requests'] > 0 else 0
        }
    
    def generate_system_report(self) -> List[Dict]:
        """Generate comprehensive system performance report"""
        return [
            {
                'service': service,
                'metrics': self.get_service_performance(service)
            }
            for service in self.service_metrics
        ]

# Example Usage
if __name__ == '__main__':
    monitor = APIPerformanceMonitor()
    
    # Simulate tracking
    start = time.time()
    time.sleep(0.1)  # Simulate request processing
    monitor.track_request('memory-mcp', start, time.time())
    
    print(monitor.generate_system_report())
