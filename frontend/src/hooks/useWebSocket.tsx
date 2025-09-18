import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { Task, Agent } from '../types'

interface WebSocketContextType {
  tasks: Map<string, Task>
  agents: Map<string, Agent>
  connectionStatus: 'connected' | 'disconnected' | 'reconnecting'
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [tasks, setTasks] = useState<Map<string, Task>>(new Map())
  const [agents, setAgents] = useState<Map<string, Agent>>(new Map())
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'reconnecting'>('disconnected')
  const [ws, setWs] = useState<WebSocket | null>(null)

  const connect = useCallback(() => {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
    const websocket = new WebSocket(`${wsUrl}/ws/frontend`)

    websocket.onopen = () => {
      console.log('WebSocket connected')
      setConnectionStatus('connected')
    }

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'task_update') {
        setTasks(prev => {
          const newTasks = new Map(prev)
          newTasks.set(data.task.id, data.task)
          return newTasks
        })
      } else if (data.type === 'agents_update') {
        const agentsMap = new Map<string, Agent>()
        Object.entries(data.agents).forEach(([id, agent]) => {
          agentsMap.set(id, agent as Agent)
        })
        setAgents(agentsMap)
      }
    }

    websocket.onclose = () => {
      console.log('WebSocket disconnected')
      setConnectionStatus('disconnected')
      // Reconnect after 3 seconds
      setTimeout(() => {
        setConnectionStatus('reconnecting')
        connect()
      }, 3000)
    }

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    setWs(websocket)

    return websocket
  }, [])

  useEffect(() => {
    const websocket = connect()

    return () => {
      if (websocket.readyState === WebSocket.OPEN) {
        websocket.close()
      }
    }
  }, [connect])

  return (
    <WebSocketContext.Provider value={{ tasks, agents, connectionStatus }}>
      {children}
    </WebSocketContext.Provider>
  )
}

export const useWebSocket = () => {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }
  return context
}