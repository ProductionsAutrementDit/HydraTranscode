export enum TaskStatus {
  PENDING = 'PENDING',
  ASSIGNED = 'ASSIGNED',
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED'
}

export enum TaskPriority {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH'
}

export enum AgentStatus {
  OFFLINE = 'OFFLINE',
  ONLINE = 'ONLINE',
  BUSY = 'BUSY',
  ERROR = 'ERROR'
}

export interface Task {
  id: string
  priority: TaskPriority
  status: TaskStatus
  agent_id?: string
  input_files: Array<{
    storage: string
    path: string
  }>
  output_settings: {
    storage: string
    path: string
    codec: string
    resolution?: string
  }
  progress: number
  created_at: string
  started_at?: string
  completed_at?: string
  error_message?: string
}

export interface Agent {
  id: string
  host: string
  port?: number
  status: AgentStatus
  current_task_id?: string
  last_heartbeat?: string
  storage_mappings: Record<string, string>
  capabilities: Record<string, any>
}