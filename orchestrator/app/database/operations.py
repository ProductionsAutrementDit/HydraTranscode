from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.task import Task, TaskStatus, TaskPriority

class TaskOperations:
    @staticmethod
    def create_task(db: Session, task_data: dict) -> Task:
        task = Task(**task_data)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get_task(db: Session, task_id: str) -> Optional[Task]:
        return db.query(Task).filter(Task.id == task_id).first()

    @staticmethod
    def get_all_tasks(db: Session, status: Optional[TaskStatus] = None) -> List[Task]:
        query = db.query(Task)
        if status:
            query = query.filter(Task.status == status)
        return query.order_by(Task.created_at.desc()).all()

    @staticmethod
    def get_next_pending_task(db: Session) -> Optional[Task]:
        # Priority order: HIGH > MEDIUM > LOW, then by created_at
        return db.query(Task).filter(
            Task.status == TaskStatus.PENDING
        ).order_by(
            Task.priority.desc(),
            Task.created_at.asc()
        ).first()

    @staticmethod
    def assign_task(db: Session, task_id: str, agent_id: str) -> Optional[Task]:
        task = TaskOperations.get_task(db, task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.ASSIGNED
            task.agent_id = agent_id
            task.started_at = datetime.utcnow()
            db.commit()
            db.refresh(task)
            return task
        return None

    @staticmethod
    def update_task_progress(db: Session, task_id: str, progress: float) -> Optional[Task]:
        task = TaskOperations.get_task(db, task_id)
        if task:
            task.progress = progress
            if task.status == TaskStatus.ASSIGNED:
                task.status = TaskStatus.RUNNING
            db.commit()
            db.refresh(task)
            return task
        return None

    @staticmethod
    def complete_task(db: Session, task_id: str) -> Optional[Task]:
        task = TaskOperations.get_task(db, task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.progress = 100.0
            task.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(task)
            return task
        return None

    @staticmethod
    def fail_task(db: Session, task_id: str, error_message: str) -> Optional[Task]:
        task = TaskOperations.get_task(db, task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = error_message
            task.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(task)
            return task
        return None