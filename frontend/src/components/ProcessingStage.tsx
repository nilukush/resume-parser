import React from 'react'
import { Check, Clock, AlertCircle } from 'lucide-react'

interface ProcessingStageProps {
  name: string
  status: 'pending' | 'in_progress' | 'complete' | 'error'
  progress: number
}

export default function ProcessingStage({ name, status, progress }: ProcessingStageProps) {
  const getStatusIcon = () => {
    switch (status) {
      case 'complete':
        return <Check className="h-5 w-5 text-green-600" />
      case 'in_progress':
        return <Clock className="h-5 w-5 text-navy-600 animate-pulse" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-600" />
      default:
        return <Clock className="h-5 w-5 text-gray-400" />
    }
  }

  const getStatusColor = () => {
    switch (status) {
      case 'complete':
        return 'text-green-600'
      case 'in_progress':
        return 'text-navy-600'
      case 'error':
        return 'text-red-600'
      default:
        return 'text-gray-400'
    }
  }

  const getProgressBarColor = () => {
    switch (status) {
      case 'complete':
        return 'bg-green-600'
      case 'in_progress':
        return 'bg-navy-600'
      case 'error':
        return 'bg-red-600'
      default:
        return 'bg-gray-300'
    }
  }

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <span className={`font-semibold ${getStatusColor()}`}>
            {name}
          </span>
        </div>
        <span className={`font-mono ${getStatusColor()}`}>
          {progress}%
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full ${getProgressBarColor()} transition-all duration-500 ease-out`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  )
}
