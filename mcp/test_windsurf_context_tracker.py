import pytest
import os
import json
from windsurf_context_tracker import WindsurfContextTracker

@pytest.fixture
def context_tracker():
    """Create a fresh WindsurfContextTracker for each test"""
    tracker = WindsurfContextTracker(context_dir='/tmp/mcp_contexts')
    yield tracker
    # Clean up context files after test
    for file in os.listdir('/tmp/mcp_contexts'):
        os.remove(os.path.join('/tmp/mcp_contexts', file))

def test_conversation_logging(context_tracker):
    """Test conversation logging functionality"""
    conv_id = context_tracker.log_conversation(
        "Test user message", 
        "Test AI response"
    )
    assert conv_id is not None
    assert len(context_tracker.conversations) == 1
    
    logged_conv = context_tracker.conversations[0]
    assert logged_conv['user_message'] == "Test user message"
    assert logged_conv['ai_response'] == "Test AI response"

def test_task_extraction(context_tracker):
    """Test task extraction mechanism"""
    context_tracker.log_conversation(
        "Implement a new feature for the context tracking system", 
        "Great, I'll help you design the feature extraction"
    )
    
    tasks = context_tracker.extract_tasks()
    assert len(tasks) > 0
    assert any('implement' in task['description'].lower() for task in tasks)

def test_persistent_memory(context_tracker):
    """Test persistent memory addition"""
    memory_content = {
        'project': 'Test Project',
        'description': 'Memory persistence test'
    }
    memory_id = context_tracker.add_persistent_memory(
        memory_content, 
        tags=['test', 'memory']
    )
    
    assert memory_id is not None
    assert len(context_tracker.persistent_memories) == 1
    
    stored_memory = context_tracker.persistent_memories[0]
    assert stored_memory['content'] == memory_content
    assert 'test' in stored_memory['tags']

def test_interaction_rule(context_tracker):
    """Test interaction rule addition"""
    rule = {
        'type': 'test_rule',
        'conditions': ['test_condition'],
        'actions': ['test_action']
    }
    rule_id = context_tracker.add_interaction_rule(rule)
    
    assert rule_id is not None
    assert len(context_tracker.interaction_rules) == 1
    
    stored_rule = context_tracker.interaction_rules[0]
    assert stored_rule['rule'] == rule

def test_context_persistence(context_tracker):
    """Test context saving and loading"""
    # Add some data
    context_tracker.log_conversation("Test message", "Test response")
    context_tracker.add_persistent_memory({'test': 'memory'})
    context_tracker.add_interaction_rule({'test': 'rule'})
    
    # Save context
    context_tracker._save_context()
    
    # Create new tracker and load context
    new_tracker = WindsurfContextTracker(context_dir='/tmp/mcp_contexts')
    loaded_context = new_tracker.load_latest_context()
    
    assert loaded_context is not None
    assert len(new_tracker.conversations) > 0
    assert len(new_tracker.persistent_memories) > 0
    assert len(new_tracker.interaction_rules) > 0

def test_context_directory_creation():
    """Verify context directory creation"""
    test_dir = '/tmp/test_context_dir'
    tracker = WindsurfContextTracker(context_dir=test_dir)
    assert os.path.exists(test_dir)
    os.rmdir(test_dir)  # Clean up

if __name__ == '__main__':
    pytest.main()
