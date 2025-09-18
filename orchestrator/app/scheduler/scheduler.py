import logging
from sqlalchemy.orm import Session
from app.database.operations import TaskOperations
from app.websocket.messages import OrchestratorMessage, OrchestratorMessageType

logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self, connection_manager):
        self.manager = connection_manager

    async def try_assign_tasks(self, db: Session):
        """Try to assign pending tasks to available agents"""
        while True:
            # Get next pending task
            task = TaskOperations.get_next_pending_task(db)
            if not task:
                break

            # Get available agent
            agent_id = self.manager.get_available_agent()
            if not agent_id:
                break

            # Assign task to agent
            task = TaskOperations.assign_task(db, task.id, agent_id)
            if task:
                self.manager.assign_task_to_agent(agent_id, task.id)

                # Send task to agent
                message = OrchestratorMessage(
                    type=OrchestratorMessageType.ASSIGN,
                    task=task.to_dict()
                )

                success = await self.manager.send_to_agent(agent_id, message)
                if success:
                    logger.info(f"Assigned task {task.id} to agent {agent_id}")
                    await self.manager.broadcast_task_update(task.to_dict())
                    await self.manager.broadcast_agent_status()
                else:
                    # Failed to send, revert assignment
                    from app.models.task import TaskStatus
                    task.status = TaskStatus.PENDING
                    task.agent_id = None
                    task.started_at = None
                    db.commit()
                    self.manager.free_agent(agent_id)
                    break