# Hydra Transcode

A distributed video transcoding system with orchestrator, agents, and web frontend.

## Architecture

- **Orchestrator**: Python/FastAPI server that manages tasks and agent coordination
- **Agents**: Python workers that perform actual transcoding using ffmpeg
- **Frontend**: React/TypeScript dashboard for monitoring and task management
- **Communication**: WebSocket for real-time updates between components

## Features

- ✅ Priority-based task queue (HIGH, MEDIUM, LOW)
- ✅ Real-time progress tracking
- ✅ Agent health monitoring with auto-reconnection
- ✅ Crash recovery with checkpoint system
- ✅ Sequential video concatenation
- ✅ Multiple codec support (H.264, H.265, VP9)
- ✅ Resolution control
- ✅ Storage mapping for cross-platform paths
- ✅ WebSocket-based real-time updates

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd hydratranscode
```

2. Start all services:
```bash
docker-compose up --build
```

3. Access the frontend:
- Open http://localhost:5173 in your browser

4. The system starts with 3 agents ready to process tasks

### Test with Sample Video

1. Copy a test video to the shared storage:
```bash
docker cp sample.mp4 hydratranscode_agent-1_1:/storage/
```

2. Create a test task via the UI or API:
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "priority": "HIGH",
    "input_files": [{"storage": "shared", "path": "sample.mp4"}],
    "output_settings": {
      "storage": "shared",
      "path": "output/transcoded.mp4",
      "codec": "h264",
      "resolution": "1280x720"
    }
  }'
```

## Development

### Project Structure
```
hydratranscode
├── orchestrator/          # FastAPI backend
├── agent/                 # Transcoding workers
├── frontend/             # React dashboard
├── shared/storage/       # Shared storage volume
└── docker-compose.yml    # Container orchestration
```

### API Endpoints

- `GET /api/tasks` - List all tasks
- `POST /api/tasks` - Create new task
- `GET /api/tasks/{id}` - Get task details
- `PATCH /api/tasks/{id}` - Update task (restart, cancel)
- `DELETE /api/tasks/{id}` - Delete task
- `GET /api/agents` - List all agents

### WebSocket Endpoints

- `/ws/agent` - Agent connection endpoint
- `/ws/frontend` - Frontend real-time updates

## Configuration

### Orchestrator (`orchestrator/config.yaml`)
- Agent definitions
- Storage mappings
- Task settings
- Logging configuration

### Environment Variables
See `.env.example` for all available configuration options

## Task Workflow

1. **PENDING**: Task created, waiting for assignment
2. **ASSIGNED**: Task assigned to an agent
3. **RUNNING**: Agent is processing the task
4. **COMPLETED**: Task finished successfully
5. **FAILED**: Task failed with error
6. **CANCELLED**: Task cancelled by user

## Monitoring

- **Frontend Dashboard**: Real-time task and agent status
- **Logs**: Check container logs with `docker-compose logs -f [service]`
- **Agent Status**: Online/Offline/Busy indicators
- **Progress Tracking**: Real-time progress bars for running tasks

## Troubleshooting

### Agent Won't Connect
- Check orchestrator is running: `docker-compose ps`
- Verify network connectivity: `docker-compose logs agent-1`
- Ensure WebSocket URL is correct in environment

### Task Fails Immediately
- Check storage paths are correct
- Verify input files exist
- Check agent logs for ffmpeg errors

### Frontend Not Updating
- Check WebSocket connection status indicator
- Verify VITE_WS_URL environment variable
- Check browser console for errors

## Future Enhancements

- [ ] Multiple audio track support
- [ ] Advanced concatenation options
- [ ] Batch task creation
- [ ] Task templates
- [ ] Performance metrics
- [ ] Authentication system
- [ ] Email notifications
- [ ] Cloud storage support (S3, GCS)
- [ ] Hardware acceleration (NVENC, QSV)
- [ ] Task dependencies and workflows

## License

MIT