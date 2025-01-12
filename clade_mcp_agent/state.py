"""State management models for the Clade MCP Agent."""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, model_validator
import json


class BaseState(BaseModel):
    """Base interface for all state models."""
    
    state_id: str = Field(default_factory=lambda: f"state_{datetime.utcnow().isoformat()}")
    state_type: str = Field(default="base")
    history: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    parent_state_id: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_state(self) -> 'BaseState':
        """Validate state after initial validation."""
        # Ensure history entries have timestamps
        for entry in self.history:
            if 'timestamp' not in entry:
                entry['timestamp'] = datetime.utcnow().isoformat()
        return self
    
    def add_history_entry(self, entry_type: str, data: Dict[str, Any]) -> None:
        """Add a new entry to the state history."""
        entry = {
            'type': entry_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.history.append(entry)
    
    def model_dump_json(self, **kwargs: Any) -> str:
        """Convert the model to JSON string, with special handling for datetime."""
        data = self.model_dump()
        return json.dumps(data, default=str)
    
    def create_child_state(self, **kwargs: Any) -> 'BaseState':
        """Create a new state instance that inherits from this one."""
        kwargs['parent_state_id'] = self.state_id
        kwargs['history'] = self.history.copy()  # Copy history from parent
        return self.__class__(**kwargs)


class ConversationState(BaseState):
    """State model for conversation context."""
    
    state_type: str = Field(default="conversation")
    current_task: str
    relevant_facts: List[str] = Field(default_factory=list)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.conversation_history.append(message)
        self.add_history_entry('message', message)


class TaskState(BaseState):
    """State model for task execution context."""
    
    state_type: str = Field(default="task")
    task_name: str
    task_status: str = Field(default="pending")
    task_data: Dict[str, Any] = Field(default_factory=dict)
    subtasks: List[Dict[str, Any]] = Field(default_factory=list)
    
    def update_status(self, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Update task status and record in history."""
        self.task_status = status
        entry_data = {'status': status}
        if details:
            entry_data.update(details)
        self.add_history_entry('status_update', entry_data)
    
    def add_subtask(self, name: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Add a subtask to the task state."""
        subtask = {
            'name': name,
            'status': 'pending',
            'data': data or {},
            'created_at': datetime.utcnow().isoformat()
        }
        self.subtasks.append(subtask)
        self.add_history_entry('subtask_added', subtask) 