import { useState } from 'react'
import { taskService } from '../services/api'
import { TaskPriority } from '../types'

interface CreateTaskModalProps {
  onClose: () => void
}

export default function CreateTaskModal({ onClose }: CreateTaskModalProps) {
  const [priority, setPriority] = useState<TaskPriority>(TaskPriority.MEDIUM)
  const [inputFiles, setInputFiles] = useState([
    { storage: 'shared', path: '' }
  ])
  const [outputSettings, setOutputSettings] = useState({
    storage: 'shared',
    path: '',
    codec: 'h264',
    resolution: '1920x1080'
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      await taskService.createTask({
        priority,
        input_files: inputFiles.filter(f => f.path),
        output_settings: outputSettings,
      })
      onClose()
    } catch (error) {
      console.error('Failed to create task:', error)
      alert('Failed to create task')
    } finally {
      setIsSubmitting(false)
    }
  }

  const addInputFile = () => {
    setInputFiles([...inputFiles, { storage: 'shared', path: '' }])
  }

  const removeInputFile = (index: number) => {
    setInputFiles(inputFiles.filter((_, i) => i !== index))
  }

  const updateInputFile = (index: number, path: string) => {
    const newFiles = [...inputFiles]
    newFiles[index].path = path
    setInputFiles(newFiles)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold mb-4">Create New Task</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Priority
            </label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as TaskPriority)}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value={TaskPriority.LOW}>Low</option>
              <option value={TaskPriority.MEDIUM}>Medium</option>
              <option value={TaskPriority.HIGH}>High</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Input Files
            </label>
            {inputFiles.map((file, index) => (
              <div key={index} className="flex space-x-2 mb-2">
                <select
                  value={file.storage}
                  onChange={(e) => {
                    const newFiles = [...inputFiles]
                    newFiles[index].storage = e.target.value
                    setInputFiles(newFiles)
                  }}
                  className="px-3 py-2 border rounded-lg"
                >
                  <option value="shared">Shared</option>
                  <option value="local">Local</option>
                  <option value="cloud">Cloud</option>
                </select>
                <input
                  type="text"
                  value={file.path}
                  onChange={(e) => updateInputFile(index, e.target.value)}
                  placeholder="Path (e.g., videos/input.mp4)"
                  className="flex-1 px-3 py-2 border rounded-lg"
                  required
                />
                {inputFiles.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeInputFile(index)}
                    className="px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              onClick={addInputFile}
              className="px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              Add Input File
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Output Settings
            </label>
            <div className="flex space-x-2">
              <select
                value={outputSettings.storage}
                onChange={(e) => setOutputSettings({ ...outputSettings, storage: e.target.value })}
                className="px-3 py-2 border rounded-lg"
              >
                <option value="shared">Shared</option>
                <option value="local">Local</option>
                <option value="cloud">Cloud</option>
              </select>
              <input
                type="text"
                value={outputSettings.path}
                onChange={(e) => setOutputSettings({ ...outputSettings, path: e.target.value })}
                placeholder="Path (e.g., output/transcoded.mp4)"
                className="flex-1 px-3 py-2 border rounded-lg"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Codec
              </label>
              <select
                value={outputSettings.codec}
                onChange={(e) => setOutputSettings({ ...outputSettings, codec: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="h264">H.264</option>
                <option value="h265">H.265</option>
                <option value="vp9">VP9</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Resolution
              </label>
              <select
                value={outputSettings.resolution}
                onChange={(e) => setOutputSettings({ ...outputSettings, resolution: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="3840x2160">4K (3840x2160)</option>
                <option value="1920x1080">1080p (1920x1080)</option>
                <option value="1280x720">720p (1280x720)</option>
                <option value="854x480">480p (854x480)</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-400"
            >
              {isSubmitting ? 'Creating...' : 'Create Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}