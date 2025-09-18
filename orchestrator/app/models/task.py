from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Float, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    agent_id = Column(String, nullable=True)

    # Input/Output configuration
    input_files = Column(JSON, nullable=False)  # [{"storage": "shared", "path": "..."}]
    output_settings = Column(JSON, nullable=False)  # {"storage": "shared", "path": "...", "codec": "h264", "resolution": "1920x1080"}

    # Progress tracking
    progress = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Error handling
    error_message = Column(String, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "priority": self.priority.value if self.priority else None,
            "status": self.status.value if self.status else None,
            "agent_id": self.agent_id,
            "input_files": self.input_files,
            "output_settings": self.output_settings,
            "progress": self.progress,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message
        }