from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db, TaskOperations
from app.models.task import TaskStatus, TaskPriority

router = APIRouter()

class CreateTaskRequest(BaseModel):
    priority: Optional[TaskPriority] = TaskPriority.MEDIUM
    input_files: List[dict]  # [{"storage": "shared", "path": "..."}]
    output_settings: dict  # {"storage": "shared", "path": "...", "codec": "h264", "resolution": "1920x1080"}

class UpdateTaskRequest(BaseModel):
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None

@router.get("/")
async def list_tasks(
    status: Optional[TaskStatus] = None,
    db: Session = Depends(get_db)
):
    tasks = TaskOperations.get_all_tasks(db, status)
    return {"tasks": [task.to_dict() for task in tasks]}

@router.post("/")
async def create_task(
    request: CreateTaskRequest,
    app_request: Request,
    db: Session = Depends(get_db)
):
    task_data = {
        "priority": request.priority,
        "input_files": request.input_files,
        "output_settings": request.output_settings
    }

    task = TaskOperations.create_task(db, task_data)

    # Try to assign the task immediately
    scheduler = app_request.app.state.scheduler
    manager = app_request.app.state.manager

    await scheduler.try_assign_tasks(db)
    await manager.broadcast_task_update(task.to_dict())

    return task.to_dict()

@router.get("/{task_id}")
async def get_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    task = TaskOperations.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()

@router.patch("/{task_id}")
async def update_task(
    task_id: str,
    request: UpdateTaskRequest,
    app_request: Request,
    db: Session = Depends(get_db)
):
    task = TaskOperations.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if request.priority is not None:
        task.priority = request.priority

    if request.status is not None:
        # Handle status changes
        if request.status == TaskStatus.CANCELLED:
            task.status = request.status
        elif request.status == TaskStatus.PENDING and task.status == TaskStatus.FAILED:
            # Restarting a failed task
            task.status = TaskStatus.PENDING
            task.agent_id = None
            task.error_message = None
            task.progress = 0.0
            task.started_at = None
            task.completed_at = None

    db.commit()
    db.refresh(task)

    # Broadcast task update
    manager = app_request.app.state.manager
    await manager.broadcast_task_update(task.to_dict())

    # Try to assign if task is now pending
    if task.status == TaskStatus.PENDING:
        scheduler = app_request.app.state.scheduler
        await scheduler.try_assign_tasks(db)

    return task.to_dict()

@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    task = TaskOperations.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status in [TaskStatus.RUNNING, TaskStatus.ASSIGNED]:
        raise HTTPException(status_code=400, detail="Cannot delete running or assigned task")

    db.delete(task)
    db.commit()

    return {"message": "Task deleted successfully"}