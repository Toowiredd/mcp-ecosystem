from typing import Dict, List, Any
import json

class NeurodivergentMonitoringSystem:
    def __init__(self):
        self.status_indicators = {
            'green': 'All systems operational',
            'yellow': 'Processing/Syncing',
            'red': 'Issues detected',
            'grey': 'Disconnected'
        }
        
        self.notification_preferences = {
            'minimal_text': True,
            'clear_hierarchy': True,
            'avoid_sensory_overload': True
        }
    
    def generate_status_report(self, system_metrics: List[Dict[str, Any]]) -> Dict:
        """Generate a clear, minimal status report"""
        overall_status = 'green'  # Default to green
        
        # Determine overall system status
        for metric in system_metrics:
            if metric.get('health', 'green') == 'red':
                overall_status = 'red'
                break
            elif metric.get('health', 'green') == 'yellow':
                overall_status = 'yellow'
        
        return {
            'status': overall_status,
            'status_message': self.status_indicators[overall_status],
            'detailed_metrics': [
                {
                    'service': metric['service'],
                    'health': metric.get('health', 'green'),
                    'key_info': metric.get('key_info', 'No additional details')
                }
                for metric in system_metrics
            ]
        }
    
    def create_notification(self, report: Dict) -> str:
        """Create a neurodivergent-friendly notification"""
        if self.notification_preferences['minimal_text']:
            return f"System Status: {report['status_message']}"
        
        return json.dumps(report, indent=2)

# Example Usage
if __name__ == '__main__':
    monitor = NeurodivergentMonitoringSystem()
    
    sample_metrics = [
        {
            'service': 'memory-mcp',
            'health': 'green',
            'key_info': 'Operational'
        },
        {
            'service': 'vision-mcp',
            'health': 'yellow',
            'key_info': 'Processing large dataset'
        }
    ]
    
    report = monitor.generate_status_report(sample_metrics)
    notification = monitor.create_notification(report)
    print(notification)
