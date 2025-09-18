import { Task, TaskStatus, TaskPriority } from '../types'
import TaskCard from './TaskCard'

interface TaskListProps {
  tasks: Task[]
}

export default function TaskList({ tasks }: TaskListProps) {
  const getStatusBadge = (status: TaskStatus) => {
    const colors = {
      [TaskStatus.PENDING]: 'bg-gray-200 text-gray-800',
      [TaskStatus.ASSIGNED]: 'bg-yellow-200 text-yellow-800',
      [TaskStatus.RUNNING]: 'bg-blue-200 text-blue-800',
      [TaskStatus.COMPLETED]: 'bg-green-200 text-green-800',
      [TaskStatus.FAILED]: 'bg-red-200 text-red-800',
      [TaskStatus.CANCELLED]: 'bg-gray-300 text-gray-700',
    }
    return colors[status] || 'bg-gray-200 text-gray-800'
  }

  const getPriorityBadge = (priority: TaskPriority) => {
    const colors = {
      [TaskPriority.LOW]: 'bg-gray-100 text-gray-600',
      [TaskPriority.MEDIUM]: 'bg-yellow-100 text-yellow-700',
      [TaskPriority.HIGH]: 'bg-red-100 text-red-700',
    }
    return colors[priority] || 'bg-gray-100 text-gray-600'
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Tasks</h2>
        {tasks.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No tasks yet</p>
        ) : (
          <div className="space-y-4">
            {tasks.map(task => (
              <TaskCard
                key={task.id}
                task={task}
                getStatusBadge={getStatusBadge}
                getPriorityBadge={getPriorityBadge}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}