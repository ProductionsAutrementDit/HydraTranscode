import { Agent, AgentStatus } from '../types'
import { format } from 'date-fns'

interface AgentListProps {
  agents: Agent[]
}

export default function AgentList({ agents }: AgentListProps) {
  const getStatusIcon = (status: AgentStatus) => {
    const icons = {
      [AgentStatus.OFFLINE]: '⚫',
      [AgentStatus.ONLINE]: '🟢',
      [AgentStatus.BUSY]: '🟡',
      [AgentStatus.ERROR]: '🔴',
    }
    return icons[status] || '⚫'
  }

  const getStatusColor = (status: AgentStatus) => {
    const colors = {
      [AgentStatus.OFFLINE]: 'text-gray-500',
      [AgentStatus.ONLINE]: 'text-green-600',
      [AgentStatus.BUSY]: 'text-yellow-600',
      [AgentStatus.ERROR]: 'text-red-600',
    }
    return colors[status] || 'text-gray-500'
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Agents</h2>
        {agents.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No agents connected</p>
        ) : (
          <div className="space-y-3">
            {agents.map(agent => (
              <div key={agent.id} className="border rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className={getStatusColor(agent.status)}>
                      {getStatusIcon(agent.status)}
                    </span>
                    <span className="font-medium text-gray-900">{agent.id}</span>
                  </div>
                </div>

                <div className="text-sm text-gray-600 space-y-1">
                  <p>
                    <span className="font-medium">Status:</span> {agent.status}
                  </p>
                  {agent.current_task_id && (
                    <p>
                      <span className="font-medium">Task:</span> #{agent.current_task_id.slice(0, 8)}
                    </p>
                  )}
                  {agent.last_heartbeat && (
                    <p className="text-xs">
                      <span className="font-medium">Last seen:</span>{' '}
                      {format(new Date(agent.last_heartbeat), 'p')}
                    </p>
                  )}
                </div>

                {agent.capabilities && Object.keys(agent.capabilities).length > 0 && (
                  <div className="mt-2 pt-2 border-t">
                    <p className="text-xs font-medium text-gray-700 mb-1">Capabilities:</p>
                    <div className="text-xs text-gray-600">
                      {agent.capabilities.codecs && (
                        <p>Codecs: {agent.capabilities.codecs.join(', ')}</p>
                      )}
                      {agent.capabilities.formats && (
                        <p>Formats: {agent.capabilities.formats.join(', ')}</p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}