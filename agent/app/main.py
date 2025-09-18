import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the parent directory to Python path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.websocket_client import WebSocketClient
from app.transcoder import TranscodeTask
from app.checkpoint import CheckpointManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TranscoderAgent:
    def __init__(self):
        self.agent_id = os.getenv("AGENT_ID", "agent-unknown")
        self.orchestrator_url = os.getenv("ORCHESTRATOR_URL", "ws://localhost:8000/ws/agent")
        self.state_dir = Path(os.getenv("STATE_DIR", "/tmp/agent-state"))
        self.storage_map = json.loads(os.getenv("STORAGE_MAP", '{"shared": "/storage"}'))

        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.ws_client = WebSocketClient(
            url=self.orchestrator_url,
            agent_id=self.agent_id,
            on_task_received=self.handle_task_assignment
        )

        self.checkpoint_manager = CheckpointManager(self.state_dir)
        self.current_task = None
        self.shutdown_requested = False

    async def start(self):
        """Start the agent and handle reconnection"""
        logger.info(f"Agent {self.agent_id} starting...")

        # Check for any crashed tasks
        crashed_task = self.checkpoint_manager.get_crashed_task()
        if crashed_task:
            logger.info(f"Found crashed task: {crashed_task['task_id']}")
            await self.ws_client.report_crashed_task(crashed_task)

        # Start WebSocket connection
        await self.ws_client.connect()

    async def handle_task_assignment(self, task_data: dict):
        """Handle a new task assignment from orchestrator"""
        try:
            logger.info(f"Received task: {task_data['id']}")

            # Map storage paths
            input_files = self._map_storage_paths(task_data['input_files'])
            output_settings = self._map_storage_path(task_data['output_settings'])

            # Create checkpoint
            self.checkpoint_manager.create_checkpoint(task_data['id'])

            # Create and start transcoding task
            self.current_task = TranscodeTask(
                task_id=task_data['id'],
                input_files=input_files,
                output_settings=output_settings,
                progress_callback=self._on_progress,
                completion_callback=self._on_completion,
                error_callback=self._on_error
            )

            # Run transcoding
            await self.current_task.run()

        except Exception as e:
            logger.error(f"Error handling task: {e}")
            await self.ws_client.send_failed(task_data['id'], str(e))
            self.checkpoint_manager.clear_checkpoint()
            self.current_task = None

    def _map_storage_paths(self, files: list) -> list:
        """Map storage IDs to actual paths"""
        mapped = []
        for file in files:
            storage_id = file['storage']
            if storage_id in self.storage_map:
                base_path = self.storage_map[storage_id]
                mapped.append(os.path.join(base_path, file['path']))
            else:
                raise ValueError(f"Unknown storage ID: {storage_id}")
        return mapped

    def _map_storage_path(self, settings: dict) -> dict:
        """Map storage ID to actual path in output settings"""
        storage_id = settings['storage']
        if storage_id in self.storage_map:
            base_path = self.storage_map[storage_id]
            settings = settings.copy()
            settings['path'] = os.path.join(base_path, settings['path'])
            return settings
        else:
            raise ValueError(f"Unknown storage ID: {storage_id}")

    async def _on_progress(self, task_id: str, progress: float):
        """Handle progress updates from transcoding task"""
        await self.ws_client.send_progress(task_id, progress)
        self.checkpoint_manager.update_progress(progress)

    async def _on_completion(self, task_id: str):
        """Handle task completion"""
        logger.info(f"Task {task_id} completed successfully")
        await self.ws_client.send_complete(task_id)
        self.checkpoint_manager.clear_checkpoint()
        self.current_task = None

    async def _on_error(self, task_id: str, error: str):
        """Handle task error"""
        logger.error(f"Task {task_id} failed: {error}")
        await self.ws_client.send_failed(task_id, error)
        self.checkpoint_manager.clear_checkpoint()
        self.current_task = None

    async def shutdown(self):
        """Graceful shutdown"""
        self.shutdown_requested = True
        if self.current_task:
            logger.info("Stopping current task...")
            await self.current_task.cancel()
        await self.ws_client.disconnect()

async def main():
    agent = TranscoderAgent()

    # Handle shutdown signals
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        asyncio.create_task(agent.shutdown())

    import signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await agent.start()
    except Exception as e:
        logger.error(f"Agent error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())