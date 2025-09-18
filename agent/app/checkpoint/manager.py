import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class CheckpointManager:
    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.checkpoint_file = state_dir / "task_checkpoint.json"

    def create_checkpoint(self, task_id: str):
        """Create a checkpoint for a new task"""
        checkpoint = {
            "task_id": task_id,
            "started_at": datetime.utcnow().isoformat(),
            "progress": 0.0,
            "pid": os.getpid()
        }

        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint, f)
            logger.info(f"Created checkpoint for task {task_id}")
        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")

    def update_progress(self, progress: float):
        """Update progress in checkpoint"""
        if not self.checkpoint_file.exists():
            return

        try:
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)

            checkpoint['progress'] = progress
            checkpoint['last_updated'] = datetime.utcnow().isoformat()

            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint, f)
        except Exception as e:
            logger.error(f"Failed to update checkpoint: {e}")

    def get_crashed_task(self) -> Optional[Dict]:
        """Check if there was a task running when agent crashed"""
        if not self.checkpoint_file.exists():
            return None

        try:
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)

            # Check if the PID in checkpoint is still running
            pid = checkpoint.get('pid')
            if pid and self._is_process_running(pid):
                # Process is still running, not a crash
                return None

            logger.info(f"Found crashed task: {checkpoint['task_id']}")
            return checkpoint

        except Exception as e:
            logger.error(f"Failed to read checkpoint: {e}")
            return None

    def clear_checkpoint(self):
        """Clear the checkpoint file"""
        try:
            if self.checkpoint_file.exists():
                self.checkpoint_file.unlink()
                logger.info("Checkpoint cleared")
        except Exception as e:
            logger.error(f"Failed to clear checkpoint: {e}")

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running"""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False