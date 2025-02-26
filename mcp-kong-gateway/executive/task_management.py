import uuid
from enum import Enum, auto
from typing import Dict, List, Optional
from dataclasses import dataclass, field

class TaskStatus(Enum):
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    BLOCKED = auto()

@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ''
    description: str = ''
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

class ExecutiveTaskManager:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.task_dependencies = {}
    
    def create_task(self, name: str, description: str = '', dependencies: List[str] = []) -> Task:
        task = Task(name=name, description=description, dependencies=dependencies)
        self.tasks[task.id] = task
        
        for dep in dependencies:
            if dep not in self.task_dependencies:
                self.task_dependencies[dep] = []
            self.task_dependencies[dep].append(task.id)
        
        return task
    
    def update_task_status(self, task_id: str, status: TaskStatus):
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            
            # Check and update dependent tasks
            if task_id in self.task_dependencies:
                for dependent_task_id in self.task_dependencies[task_id]:
                    if all(self.tasks[dep].status == TaskStatus.COMPLETED 
                           for dep in self.tasks[dependent_task_id].dependencies):
                        self.tasks[dependent_task_id].status = TaskStatus.IN_PROGRESS
    
    def get_task_chain(self, start_task_id: str) -> List[Task]:
        """Generate task execution chain"""
        visited = set()
        chain = []
        
        def dfs(task_id):
            if task_id in visited:
                return
            visited.add(task_id)
            
            task = self.tasks[task_id]
            for dep in task.dependencies:
                dfs(dep)
            
            chain.append(task)
        
        dfs(start_task_id)
        return list(reversed(chain))

# Example Usage
if __name__ == '__main__':
    manager = ExecutiveTaskManager()
    
    # Create interconnected tasks
    data_collection = manager.create_task('Data Collection')
    preprocessing = manager.create_task('Data Preprocessing', dependencies=[data_collection.id])
    model_training = manager.create_task('Model Training', dependencies=[preprocessing.id])
    
    # Simulate task progression
    manager.update_task_status(data_collection.id, TaskStatus.COMPLETED)
    manager.update_task_status(preprocessing.id, TaskStatus.COMPLETED)
    
    # Get execution chain
    execution_chain = manager.get_task_chain(model_training.id)
    for task in execution_chain:
        print(f"Task: {task.name}, Status: {task.status}")
