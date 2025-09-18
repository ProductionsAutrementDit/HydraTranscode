import { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { useWebSocket } from '../hooks/useWebSocket'
import { taskService, agentService } from '../services/api'
import TaskList from '../components/TaskList'
import AgentList from '../components/AgentList'
import CreateTaskModal from '../components/CreateTaskModal'
import { Task, Agent } from '../types'

export default function Dashboard() {
  const { tasks: wsTasks, agents: wsAgents, connectionStatus } = useWebSocket()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [tasks, setTasks] = useState<Task[]>([])
  const [agents, setAgents] = useState<Agent[]>([])

  // Fetch initial data
  const { data: initialTasks } = useQuery('tasks', taskService.getTasks, {
    refetchInterval: false,
  })

  const { data: initialAgents } = useQuery('agents', agentService.getAgents, {
    refetchInterval: false,
  })

  // Merge WebSocket updates with initial data
  useEffect(() => {
    if (initialTasks) {
      const mergedTasks = new Map<string, Task>()
      initialTasks.forEach(task => mergedTasks.set(task.id, task))
      wsTasks.forEach((task, id) => mergedTasks.set(id, task))
      setTasks(Array.from(mergedTasks.values()).sort((a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      ))
    }
  }, [initialTasks, wsTasks])

  useEffect(() => {
    if (initialAgents) {
      const mergedAgents = new Map<string, Agent>()
      Object.entries(initialAgents).forEach(([id, agent]) =>
        mergedAgents.set(id, agent)
      )
      wsAgents.forEach((agent, id) => mergedAgents.set(id, agent))
      setAgents(Array.from(mergedAgents.values()))
    }
  }, [initialAgents, wsAgents])

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900">PAD Transcoder</h1>
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <div className={`w-3 h-3 rounded-full mr-2 ${
                  connectionStatus === 'connected' ? 'bg-green-500' :
                  connectionStatus === 'reconnecting' ? 'bg-yellow-500' : 'bg-red-500'
                }`} />
                <span className="text-sm text-gray-600">{connectionStatus}</span>
              </div>
              <button
                onClick={() => setShowCreateModal(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                New Task
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-3">
            <TaskList tasks={tasks} />
          </div>
          <div className="lg:col-span-1">
            <AgentList agents={agents} />
          </div>
        </div>
      </main>

      {showCreateModal && (
        <CreateTaskModal onClose={() => setShowCreateModal(false)} />
      )}
    </div>
  )
}