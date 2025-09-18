from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

class AgentStatus(str, Enum):
    OFFLINE = "OFFLINE"
    ONLINE = "ONLINE"
    BUSY = "BUSY"
    ERROR = "ERROR"

class Agent(BaseModel):
    id: str
    host: str
    port: Optional[int] = None
    status: AgentStatus = AgentStatus.OFFLINE
    current_task_id: Optional[str] = None
    last_heartbeat: Optional[datetime] = None
    storage_mappings: Dict[str, str] = {}
    capabilities: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "host": self.host,
            "port": self.port,
            "status": self.status.value,
            "current_task_id": self.current_task_id,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "storage_mappings": self.storage_mappings,
            "capabilities": self.capabilities
        }