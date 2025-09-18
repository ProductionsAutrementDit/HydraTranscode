from typing import Dict, Optional, Set
from fastapi import WebSocket
from datetime import datetime
import json
import logging
from app.models.agent import Agent, AgentStatus
from app.websocket.messages import OrchestratorMessage, OrchestratorMessageType

logger = logging.getLogger(__name__)

class AgentConnection:
    def __init__(self, websocket: WebSocket, agent_id: str):
        self.websocket = websocket
        self.agent_id = agent_id
        self.connected_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, AgentConnection] = {}
        self.agents: Dict[str, Agent] = {}
        self.frontend_connections: Set[WebSocket] = set()

    async def connect_agent(self, websocket: WebSocket, agent_id: str):
        connection = AgentConnection(websocket, agent_id)
        self.active_connections[agent_id] = connection

        if agent_id not in self.agents:
            self.agents[agent_id] = Agent(
                id=agent_id,
                host="",  # Will be updated from config
                status=AgentStatus.ONLINE
            )
        else:
            self.agents[agent_id].status = AgentStatus.ONLINE

        logger.info(f"Agent {agent_id} connected")
        await self.broadcast_agent_status()

    def disconnect_agent(self, agent_id: str):
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
            if agent_id in self.agents:
                self.agents[agent_id].status = AgentStatus.OFFLINE
            logger.info(f"Agent {agent_id} disconnected")

    async def connect_frontend(self, websocket: WebSocket):
        await websocket.accept()
        self.frontend_connections.add(websocket)
        logger.info("Frontend client connected")

    def disconnect_frontend(self, websocket: WebSocket):
        self.frontend_connections.discard(websocket)
        logger.info("Frontend client disconnected")

    async def send_to_agent(self, agent_id: str, message: OrchestratorMessage):
        if agent_id in self.active_connections:
            connection = self.active_connections[agent_id]
            try:
                await connection.websocket.send_json(message.dict())
                return True
            except Exception as e:
                logger.error(f"Error sending to agent {agent_id}: {e}")
                self.disconnect_agent(agent_id)
        return False

    async def broadcast_to_frontend(self, message: dict):
        disconnected = set()
        for websocket in self.frontend_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to frontend: {e}")
                disconnected.add(websocket)

        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect_frontend(websocket)

    async def broadcast_agent_status(self):
        agents_status = {
            "type": "agents_update",
            "agents": {
                agent_id: agent.to_dict()
                for agent_id, agent in self.agents.items()
            }
        }
        await self.broadcast_to_frontend(agents_status)

    async def broadcast_task_update(self, task_dict: dict):
        message = {
            "type": "task_update",
            "task": task_dict
        }
        await self.broadcast_to_frontend(message)

    def get_available_agent(self) -> Optional[str]:
        for agent_id, agent in self.agents.items():
            if agent.status == AgentStatus.ONLINE and agent.current_task_id is None:
                return agent_id
        return None

    def assign_task_to_agent(self, agent_id: str, task_id: str):
        if agent_id in self.agents:
            self.agents[agent_id].status = AgentStatus.BUSY
            self.agents[agent_id].current_task_id = task_id

    def free_agent(self, agent_id: str):
        if agent_id in self.agents:
            self.agents[agent_id].status = AgentStatus.ONLINE
            self.agents[agent_id].current_task_id = None