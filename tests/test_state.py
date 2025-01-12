"""Tests for state management models."""
import pytest
from datetime import datetime
import json
from clade_mcp_agent.state import BaseState, ConversationState, TaskState


def test_base_state_creation():
    """Test basic state creation and validation."""
    state = BaseState()
    assert state.state_type == "base"
    assert state.state_id.startswith("state_")
    assert isinstance(state.history, list)
    assert isinstance(state.metadata, dict)
    assert state.parent_state_id is None


def test_base_state_history():
    """Test history tracking in base state."""
    state = BaseState()
    test_data = {"key": "value"}
    
    state.add_history_entry("test", test_data)
    assert len(state.history) == 1
    entry = state.history[0]
    assert entry["type"] == "test"
    assert entry["data"] == test_data
    assert "timestamp" in entry


def test_state_serialization():
    """Test state serialization to JSON."""
    state = BaseState(metadata={"created_at": datetime.utcnow()})
    json_data = state.model_dump_json()
    
    # Verify serialization worked
    data = json.loads(json_data)
    assert "state_id" in data
    assert "metadata" in data
    assert "created_at" in data["metadata"]


def test_child_state_creation():
    """Test creating child states."""
    parent = BaseState(metadata={"parent_data": "test"})
    parent.add_history_entry("parent_event", {"event": "test"})
    
    child = parent.create_child_state(metadata={"child_data": "test"})
    assert child.parent_state_id == parent.state_id
    assert len(child.history) == len(parent.history)
    assert child.metadata == {"child_data": "test"}


def test_conversation_state():
    """Test conversation state functionality."""
    state = ConversationState(current_task="test task")
    assert state.state_type == "conversation"
    assert state.current_task == "test task"
    assert isinstance(state.relevant_facts, list)
    assert isinstance(state.user_preferences, dict)
    assert isinstance(state.conversation_history, list)
    
    # Test message addition
    state.add_message("user", "test message")
    assert len(state.conversation_history) == 1
    assert len(state.history) == 1
    message = state.conversation_history[0]
    assert message["role"] == "user"
    assert message["content"] == "test message"
    assert "timestamp" in message


def test_task_state():
    """Test task state functionality."""
    state = TaskState(task_name="test task")
    assert state.state_type == "task"
    assert state.task_name == "test task"
    assert state.task_status == "pending"
    assert isinstance(state.task_data, dict)
    assert isinstance(state.subtasks, list)
    
    # Test status updates
    state.update_status("in_progress", {"progress": 50})
    assert state.task_status == "in_progress"
    assert len(state.history) == 1
    status_entry = state.history[0]
    assert status_entry["type"] == "status_update"
    assert status_entry["data"]["status"] == "in_progress"
    assert status_entry["data"]["progress"] == 50
    
    # Test subtask addition
    state.add_subtask("subtask1", {"priority": "high"})
    assert len(state.subtasks) == 1
    assert len(state.history) == 2
    subtask = state.subtasks[0]
    assert subtask["name"] == "subtask1"
    assert subtask["status"] == "pending"
    assert subtask["data"]["priority"] == "high"
    assert "created_at" in subtask


def test_state_validation():
    """Test state validation rules."""
    # Test history timestamp validation
    state = BaseState()
    state.history.append({"type": "test", "data": {}})  # Missing timestamp
    state.validate_state()
    assert "timestamp" in state.history[0]
    
    # Test required fields
    with pytest.raises(ValueError):
        ConversationState()  # Missing required current_task
    
    with pytest.raises(ValueError):
        TaskState()  # Missing required task_name


def test_complex_state_operations():
    """Test more complex state operations and interactions."""
    # Create a task state with a conversation child
    task_state = TaskState(task_name="planning")
    task_state.update_status("in_progress")
    task_state.add_subtask("research", {"topic": "weather"})
    
    conv_state = ConversationState(
        current_task="research",
        parent_state_id=task_state.state_id
    )
    conv_state.add_message("system", "Starting research phase")
    conv_state.add_message("user", "What's the weather like?")
    
    # Verify task state
    assert task_state.task_status == "in_progress"
    assert len(task_state.subtasks) == 1
    assert len(task_state.history) == 2  # status update + subtask
    
    # Verify conversation state
    assert conv_state.parent_state_id == task_state.state_id
    assert len(conv_state.conversation_history) == 2
    assert len(conv_state.history) == 2  # two messages
    
    # Test serialization of complex state
    task_json = task_state.model_dump_json()
    conv_json = conv_state.model_dump_json()
    
    # Verify both can be parsed back to JSON
    assert json.loads(task_json)
    assert json.loads(conv_json) 