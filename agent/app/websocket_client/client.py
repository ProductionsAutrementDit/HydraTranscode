import asyncio
import json
import logging
import websockets
from typing import Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketClient:
    def __init__(self, url: str, agent_id: str, on_task_received: Callable):
        self.url = url
        self.agent_id = agent_id
        self.on_task_received = on_task_received
        self.websocket = None
        self.running = False
        self.heartbeat_task = None
        self.receive_task = None

    async def connect(self):
        """Connect to orchestrator with automatic reconnection"""
        self.running = True
        backoff = 1

        while self.running:
            try:
                logger.info(f"Connecting to orchestrator at {self.url}")
                self.websocket = await websockets.connect(self.url)

                # Send connect message
                await self.send_message({
                    "type": "connect",
                    "agent_id": self.agent_id,
                    "data": {
                        "capabilities": {
                            "codecs": ["h264", "h265", "vp9"],
                            "formats": ["mp4", "webm", "mkv"]
                        }
                    }
                })

                # Start heartbeat and message receiver
                self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                self.receive_task = asyncio.create_task(self._receive_loop())

                # Wait for tasks to complete (they won't unless disconnected)
                await asyncio.gather(self.heartbeat_task, self.receive_task)

            except websockets.exceptions.WebSocketException as e:
                logger.error(f"WebSocket error: {e}")
            except Exception as e:
                logger.error(f"Connection error: {e}")

            if self.running:
                logger.info(f"Reconnecting in {backoff} seconds...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)  # Exponential backoff with cap

    async def disconnect(self):
        """Disconnect from orchestrator"""
        self.running = False

        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.receive_task:
            self.receive_task.cancel()

        if self.websocket:
            await self.websocket.close()

    async def send_message(self, message: dict):
        """Send a message to orchestrator"""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                raise

    async def send_progress(self, task_id: str, progress: float):
        """Send progress update"""
        await self.send_message({
            "type": "progress",
            "agent_id": self.agent_id,
            "task_id": task_id,
            "data": {"progress": progress}
        })

    async def send_complete(self, task_id: str):
        """Send task completion"""
        await self.send_message({
            "type": "complete",
            "agent_id": self.agent_id,
            "task_id": task_id,
            "data": {}
        })

    async def send_failed(self, task_id: str, error: str):
        """Send task failure"""
        await self.send_message({
            "type": "failed",
            "agent_id": self.agent_id,
            "task_id": task_id,
            "data": {"error": error}
        })

    async def report_crashed_task(self, crashed_task: dict):
        """Report a task that was running when agent crashed"""
        await self.send_message({
            "type": "reconnect",
            "agent_id": self.agent_id,
            "task_id": crashed_task['task_id'],
            "data": {
                "status": "failed",
                "error": "Agent crashed during execution"
            }
        })

    async def _heartbeat_loop(self):
        """Send periodic heartbeats to orchestrator"""
        while self.running:
            try:
                await self.send_message({
                    "type": "heartbeat",
                    "agent_id": self.agent_id
                })
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break

    async def _receive_loop(self):
        """Receive and handle messages from orchestrator"""
        while self.running:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)

                if data['type'] == 'assign':
                    # Handle task assignment
                    task = data['task']
                    logger.info(f"Assigned task: {task['id']}")
                    asyncio.create_task(self.on_task_received(task))

                elif data['type'] == 'cancel':
                    # Handle task cancellation
                    logger.info("Task cancellation requested")
                    # Will be implemented when needed

                elif data['type'] == 'ping':
                    # Respond to ping
                    await self.send_message({
                        "type": "heartbeat",
                        "agent_id": self.agent_id
                    })

            except websockets.exceptions.ConnectionClosed:
                logger.warning("Connection closed by orchestrator")
                break
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                break