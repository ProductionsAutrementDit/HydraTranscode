import axios from 'axios'
import { Task, Agent } from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const taskService = {
  async getTasks(status?: string): Promise<Task[]> {
    const response = await api.get('/api/tasks', { params: { status } })
    return response.data.tasks
  },

  async createTask(data: {
    priority?: string
    input_files: Array<{ storage: string; path: string }>
    output_settings: {
      storage: string
      path: string
      codec: string
      resolution?: string
    }
  }): Promise<Task> {
    const response = await api.post('/api/tasks', data)
    return response.data
  },

  async updateTask(id: string, data: Partial<Task>): Promise<Task> {
    const response = await api.patch(`/api/tasks/${id}`, data)
    return response.data
  },

  async deleteTask(id: string): Promise<void> {
    await api.delete(`/api/tasks/${id}`)
  },
}

export const agentService = {
  async getAgents(): Promise<Record<string, Agent>> {
    const response = await api.get('/api/agents')
    return response.data.agents
  },
}