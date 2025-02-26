import uuid
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

class WindsurfContextTracker:
    def __init__(self, context_dir='/root/mcp/contexts'):
        """
        Initialize Windsurf Context Tracker
        
        Core Responsibilities:
        1. Persistent conversation memory
        2. Task extraction
        3. Rule and memory management
        4. Context preservation across sessions
        """
        self.context_dir = context_dir
        os.makedirs(context_dir, exist_ok=True)
        
        # Core tracking structures
        self.conversations = []
        self.extracted_tasks = []
        self.persistent_memories = []
        self.interaction_rules = []
    
    def log_conversation(self, user_message: str, ai_response: str):
        """
        Log a conversation turn with comprehensive metadata
        """
        conversation_entry = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'ai_response': ai_response,
            'metadata': {
                'message_length': {
                    'user': len(user_message),
                    'ai': len(ai_response)
                }
            }
        }
        self.conversations.append(conversation_entry)
        self._save_context()
        return conversation_entry['id']
    
    def extract_tasks(self, conversation_id: str = None):
        """
        Extract potential tasks from conversations
        
        Supports:
        - Task extraction from specific conversation
        - Global task extraction
        """
        if conversation_id:
            target_conversations = [
                conv for conv in self.conversations 
                if conv['id'] == conversation_id
            ]
        else:
            target_conversations = self.conversations
        
        new_tasks = []
        for conv in target_conversations:
            # Basic task extraction heuristics
            potential_tasks = self._identify_tasks(
                conv['user_message'], 
                conv['ai_response']
            )
            new_tasks.extend(potential_tasks)
        
        self.extracted_tasks.extend(new_tasks)
        self._save_context()
        return new_tasks
    
    def _identify_tasks(self, user_message: str, ai_response: str) -> List[Dict]:
        """
        Identify potential tasks using basic NLP heuristics
        
        Future enhancement: Replace with more sophisticated NLP
        """
        task_keywords = [
            'implement', 'create', 'build', 'develop', 
            'design', 'write', 'modify', 'update'
        ]
        
        tasks = []
        for keyword in task_keywords:
            if keyword in user_message.lower() or keyword in ai_response.lower():
                tasks.append({
                    'id': str(uuid.uuid4()),
                    'description': f"Task derived from conversation: {user_message[:100]}...",
                    'status': 'pending',
                    'created_at': datetime.now().isoformat()
                })
        
        return tasks
    
    def add_persistent_memory(self, memory_content: Dict[str, Any], tags: List[str] = None):
        """
        Add a persistent memory with optional tagging
        """
        memory = {
            'id': str(uuid.uuid4()),
            'content': memory_content,
            'tags': tags or [],
            'created_at': datetime.now().isoformat()
        }
        self.persistent_memories.append(memory)
        self._save_context()
        return memory['id']
    
    def add_interaction_rule(self, rule: Dict[str, Any]):
        """
        Add an interaction rule for future reference
        """
        rule_entry = {
            'id': str(uuid.uuid4()),
            'rule': rule,
            'created_at': datetime.now().isoformat()
        }
        self.interaction_rules.append(rule_entry)
        self._save_context()
        return rule_entry['id']
    
    def _save_context(self):
        """
        Save context to persistent storage
        """
        context_data = {
            'conversations': self.conversations,
            'extracted_tasks': self.extracted_tasks,
            'persistent_memories': self.persistent_memories,
            'interaction_rules': self.interaction_rules
        }
        
        # Create timestamped context file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.context_dir}/context_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(context_data, f, indent=2)
    
    def load_latest_context(self):
        """
        Load the most recent context file
        """
        context_files = sorted(
            [f for f in os.listdir(self.context_dir) if f.startswith('context_')],
            reverse=True
        )
        
        if not context_files:
            return None
        
        latest_file = os.path.join(self.context_dir, context_files[0])
        with open(latest_file, 'r') as f:
            context_data = json.load(f)
        
        self.conversations = context_data.get('conversations', [])
        self.extracted_tasks = context_data.get('extracted_tasks', [])
        self.persistent_memories = context_data.get('persistent_memories', [])
        self.interaction_rules = context_data.get('interaction_rules', [])
        
        return context_data

# Example Usage
def main():
    tracker = WindsurfContextTracker()
    
    # Simulate a conversation
    conv_id = tracker.log_conversation(
        "We need to build a context tracking system for Windsurf",
        "Great! I'll help you design a comprehensive context tracker."
    )
    
    # Extract tasks
    tasks = tracker.extract_tasks(conv_id)
    
    # Add a persistent memory
    memory_id = tracker.add_persistent_memory(
        {
            'project': 'MCP Ecosystem',
            'component': 'Context Tracking',
            'key_requirements': ['AI-driven', 'Persistent', 'Extensible']
        },
        tags=['mcp', 'context', 'design']
    )
    
    # Add an interaction rule
    rule_id = tracker.add_interaction_rule({
        'type': 'conversation_analysis',
        'conditions': ['task_extraction', 'memory_preservation'],
        'actions': ['log_context', 'update_memories']
    })

if __name__ == '__main__':
    main()
