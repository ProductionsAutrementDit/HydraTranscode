import { useState } from 'react'
import { Task, TaskStatus } from '../types'
import { taskService } from '../services/api'
import { format } from 'date-fns'

interface TaskCardProps {
  task: Task
  getStatusBadge: (status: TaskStatus) => string
  getPriorityBadge: (priority: string) => string
}

export default function TaskCard({ task, getStatusBadge, getPriorityBadge }: TaskCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const handleRestart = async () => {
    try {
      await taskService.updateTask(task.id, {
        status: TaskStatus.PENDING,
      })
    } catch (error) {
      console.error('Failed to restart task:', error)
    }
  }

  const handleCancel = async () => {
    try {
      await taskService.updateTask(task.id, {
        status: TaskStatus.CANCELLED,
      })
    } catch (error) {
      console.error('Failed to cancel task:', error)
    }
  }

  return (
    <div className="border rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-2">
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-600">#{task.id.slice(0, 8)}</span>
            <span className={`px-2 py-1 text-xs rounded-full ${getStatusBadge(task.status)}`}>
              {task.status}
            </span>
            <span className={`px-2 py-1 text-xs rounded-full ${getPriorityBadge(task.priority)}`}>
              {task.priority}
            </span>
          </div>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-gray-400 hover:text-gray-600"
        >
          {isExpanded ? '▼' : '▶'}
        </button>
      </div>

      {task.status === TaskStatus.RUNNING && (
        <div className="mb-2">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Progress</span>
            <span>{task.progress.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${task.progress}%` }}
            />
          </div>
        </div>
      )}

      <div className="text-sm text-gray-600 space-y-1">
        <p>
          <span className="font-medium">Input:</span> {task.input_files.map(f => f.path).join(', ')}
        </p>
        <p>
          <span className="font-medium">Output:</span> {task.output_settings.path}
        </p>
        {task.agent_id && (
          <p>
            <span className="font-medium">Agent:</span> {task.agent_id}
          </p>
        )}
      </div>

      {isExpanded && (
        <div className="mt-3 pt-3 border-t">
          <div className="text-sm text-gray-600 space-y-1">
            <p>
              <span className="font-medium">Codec:</span> {task.output_settings.codec}
            </p>
            {task.output_settings.resolution && (
              <p>
                <span className="font-medium">Resolution:</span> {task.output_settings.resolution}
              </p>
            )}
            <p>
              <span className="font-medium">Created:</span> {format(new Date(task.created_at), 'PPp')}
            </p>
            {task.started_at && (
              <p>
                <span className="font-medium">Started:</span> {format(new Date(task.started_at), 'PPp')}
              </p>
            )}
            {task.completed_at && (
              <p>
                <span className="font-medium">Completed:</span> {format(new Date(task.completed_at), 'PPp')}
              </p>
            )}
            {task.error_message && (
              <p className="text-red-600">
                <span className="font-medium">Error:</span> {task.error_message}
              </p>
            )}
          </div>

          <div className="mt-3 flex space-x-2">
            {task.status === TaskStatus.FAILED && (
              <button
                onClick={handleRestart}
                className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
              >
                Restart
              </button>
            )}
            {(task.status === TaskStatus.RUNNING || task.status === TaskStatus.ASSIGNED) && (
              <button
                onClick={handleCancel}
                className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
              >
                Cancel
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}