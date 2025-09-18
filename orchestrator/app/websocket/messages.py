from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum

class AgentMessageType(str, Enum):
    CONNECT = "connect"
    HEARTBEAT = "heartbeat"
    PROGRESS = "progress"
    COMPLETE = "complete"
    FAILED = "failed"
    RECONNECT = "reconnect"

class OrchestratorMessageType(str, Enum):
    ASSIGN = "assign"
    CANCEL = "cancel"
    PING = "ping"
    ACK = "acknowledge"

class AgentMessage(BaseModel):
    type: AgentMessageType
    agent_id: str
    task_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = {}

class OrchestratorMessage(BaseModel):
    type: OrchestratorMessageType
    task: Optional[Dict[str, Any]] = None
    message: Optional[str] = None