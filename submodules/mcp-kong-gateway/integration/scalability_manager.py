import multiprocessing
import threading
import queue
import time
from typing import Callable, Any, List
import psutil

class ScalabilityManager:
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.workers = []
    
    def _worker(self):
        """Background worker processing tasks"""
        while True:
            try:
                task, args, kwargs = self.task_queue.get(timeout=5)
                try:
                    result = task(*args, **kwargs)
                    self.result_queue.put((task.__name__, result))
                except Exception as e:
                    self.result_queue.put((task.__name__, str(e)))
                finally:
                    self.task_queue.task_done()
            except queue.Empty:
                break
    
    def submit_task(self, task: Callable, *args, **kwargs):
        """Submit a task for asynchronous processing"""
        self.task_queue.put((task, args, kwargs))
    
    def start_workers(self):
        """Start worker threads"""
        for _ in range(self.max_workers):
            worker = threading.Thread(target=self._worker)
            worker.start()
            self.workers.append(worker)
    
    def wait_completion(self):
        """Wait for all tasks to complete"""
        self.task_queue.join()
        for worker in self.workers:
            worker.join()
    
    def get_results(self):
        """Retrieve all task results"""
        results = {}
        while not self.result_queue.empty():
            task_name, result = self.result_queue.get()
            results[task_name] = result
        return results
    
    @staticmethod
    def monitor_system_resources() -> Dict[str, float]:
        """Monitor current system resources"""
        return {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'available_memory': psutil.virtual_memory().available / (1024 * 1024),  # MB
            'total_memory': psutil.virtual_memory().total / (1024 * 1024)  # MB
        }
    
    def auto_scale(self, resource_threshold: float = 80.0):
        """Dynamically adjust worker count based on system resources"""
        resources = self.monitor_system_resources()
        
        if resources['cpu_usage'] > resource_threshold:
            # Reduce worker count
            self.max_workers = max(1, self.max_workers // 2)
        elif resources['cpu_usage'] < resource_threshold / 2:
            # Increase worker count
            self.max_workers = min(multiprocessing.cpu_count() * 2, self.max_workers * 2)

# Example Usage
if __name__ == '__main__':
    def sample_task(x):
        time.sleep(1)  # Simulate work
        return x * x
    
    scalability_manager = ScalabilityManager(max_workers=4)
    scalability_manager.start_workers()
    
    # Submit multiple tasks
    for i in range(10):
        scalability_manager.submit_task(sample_task, i)
    
    scalability_manager.wait_completion()
    results = scalability_manager.get_results()
    
    print("Task Results:", results)
    print("System Resources:", ScalabilityManager.monitor_system_resources())
