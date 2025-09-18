from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import logging
from datetime import datetime

from app.database import init_db, get_db, TaskOperations
from app.websocket import ConnectionManager, AgentMessage, OrchestratorMessage, OrchestratorMessageType, AgentMessageType
from app.models.task import Task, TaskStatus, TaskPriority
from app.api import tasks
from app.scheduler import TaskScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="PAD Transcoder Orchestrator", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
manager = ConnectionManager()
scheduler = TaskScheduler(manager)

# Make manager and scheduler available globally
app.state.manager = manager
app.state.scheduler = scheduler

# Include API routers
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])

@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Database initialized")

@app.get("/")
async def root():
    return {"message": "PAD Transcoder Orchestrator API", "version": "1.0.0"}

@app.get("/api/agents")
async def get_agents():
    return {
        "agents": {
            agent_id: agent.to_dict()
            for agent_id, agent in manager.agents.items()
        }
    }

@app.websocket("/ws/agent")
async def agent_websocket(websocket: WebSocket, db: Session = Depends(get_db)):
    agent_id = None
    try:
        # Accept the WebSocket connection first
        await websocket.accept()

        # Wait for initial connect message
        data = await websocket.receive_json()
        msg = AgentMessage(**data)

        if msg.type != AgentMessageType.CONNECT:
            await websocket.close(code=1003, reason="First message must be CONNECT")
            return

        agent_id = msg.agent_id
        await manager.connect_agent(websocket, agent_id)

        # Send acknowledgment
        ack = OrchestratorMessage(type=OrchestratorMessageType.ACK, message="Connected")
        await websocket.send_json(ack.dict())

        # Check if there's a pending task to assign
        await scheduler.try_assign_tasks(db)

        # Handle messages from agent
        while True:
            data = await websocket.receive_json()
            msg = AgentMessage(**data)

            if msg.type == AgentMessageType.HEARTBEAT:
                manager.active_connections[agent_id].last_heartbeat = datetime.utcnow()

            elif msg.type == AgentMessageType.PROGRESS:
                if msg.task_id:
                    progress = msg.data.get("progress", 0)
                    task = TaskOperations.update_task_progress(db, msg.task_id, progress)
                    if task:
                        await manager.broadcast_task_update(task.to_dict())

            elif msg.type == AgentMessageType.COMPLETE:
                if msg.task_id:
                    task = TaskOperations.complete_task(db, msg.task_id)
                    if task:
                        await manager.broadcast_task_update(task.to_dict())
                    manager.free_agent(agent_id)
                    await manager.broadcast_agent_status()
                    # Try to assign next task
                    await scheduler.try_assign_tasks(db)

            elif msg.type == AgentMessageType.FAILED:
                if msg.task_id:
                    error = msg.data.get("error", "Unknown error")
                    task = TaskOperations.fail_task(db, msg.task_id, error)
                    if task:
                        await manager.broadcast_task_update(task.to_dict())
                    manager.free_agent(agent_id)
                    await manager.broadcast_agent_status()
                    # Try to assign next task
                    await scheduler.try_assign_tasks(db)

            elif msg.type == AgentMessageType.RECONNECT:
                # Handle reconnection with existing task
                task_id = msg.task_id
                status = msg.data.get("status")
                if task_id and status:
                    task = TaskOperations.get_task(db, task_id)
                    if task:
                        if status == "failed":
                            error = msg.data.get("error", "Agent crashed")
                            TaskOperations.fail_task(db, task_id, error)
                        elif status == "running":
                            # Continue monitoring the task
                            manager.assign_task_to_agent(agent_id, task_id)
                        await manager.broadcast_task_update(task.to_dict())

    except WebSocketDisconnect:
        if agent_id:
            manager.disconnect_agent(agent_id)
            await manager.broadcast_agent_status()
    except Exception as e:
        logger.error(f"Error in agent websocket: {e}")
        if agent_id:
            manager.disconnect_agent(agent_id)
            await manager.broadcast_agent_status()

@app.websocket("/ws/frontend")
async def frontend_websocket(websocket: WebSocket):
    await manager.connect_frontend(websocket)
    try:
        # Send initial state
        agents_status = {
            "type": "agents_update",
            "agents": {
                agent_id: agent.to_dict()
                for agent_id, agent in manager.agents.items()
            }
        }
        await websocket.send_json(agents_status)

        # Keep connection alive
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect_frontend(websocket)
    except Exception as e:
        logger.error(f"Error in frontend websocket: {e}")
        manager.disconnect_frontend(websocket)