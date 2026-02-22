import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import FileUpload from '@/components/FileUpload'

interface UploadResponse {
  resume_id: string
  status: string
  message?: string
  file_hash?: string
  original_filename?: string
  uploaded_at?: string
  processed_at?: string | null
  websocket_url?: string
  has_parsed_data?: boolean
  existing_data?: any
}

export default function UploadPage() {
  const navigate = useNavigate()
  const [isUploading, setIsUploading] = useState(false)
  const [duplicateInfo, setDuplicateInfo] = useState<UploadResponse | null>(null)

  const handleUpload = async (file: File) => {
    setIsUploading(true)
    setDuplicateInfo(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/v1'}/resumes/upload`, {
        method: 'POST',
        body: formData
      })

      const data: UploadResponse = await response.json()

      if (!response.ok) {
        throw new Error(data.message || 'Upload failed')
      }

      // Handle duplicate upload
      if (data.status === 'already_processed' && data.has_parsed_data) {
        setDuplicateInfo(data)
        setIsUploading(false)
        return
      }

      // Navigate to processing page for new uploads
      navigate(`/processing/${data.resume_id}`)
    } catch (error) {
      console.error('Upload error:', error)
      alert(error instanceof Error ? error.message : 'Failed to upload resume. Please try again.')
    } finally {
      // Only set false if not showing duplicate info
      if (!duplicateInfo) {
        setIsUploading(false)
      }
    }
  }

  const handleViewExisting = () => {
    if (duplicateInfo) {
      navigate(`/review/${duplicateInfo.resume_id}`)
    }
  }

  const handleUploadNew = () => {
    setDuplicateInfo(null)
    setIsUploading(false)
  }

  // Show duplicate detected dialog
  if (duplicateInfo) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-navy-900 to-navy-700 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-2xl w-full">
          <div className="text-center mb-6">
            <div className="h-16 w-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="h-8 w-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-navy-900 mb-2">
              Resume Already Uploaded
            </h2>
            <p className="text-gray-600 mb-4">
              This file was previously uploaded as <strong>{duplicateInfo.original_filename}</strong>
            </p>
            {duplicateInfo.processed_at && (
              <p className="text-sm text-gray-500">
                Processed on {new Date(duplicateInfo.processed_at).toLocaleDateString()}
              </p>
            )}
          </div>

          <div className="flex gap-4">
            <button
              onClick={handleViewExisting}
              className="flex-1 bg-navy-600 hover:bg-navy-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              View Previous Results
            </button>
            <button
              onClick={handleUploadNew}
              className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              Upload Different File
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-navy-900 to-navy-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-2xl w-full">
        <h1 className="text-4xl font-bold text-navy-900 text-center mb-2">
          ResuMate
        </h1>
        <p className="text-gray-600 text-center mb-8">
          Transform Your Resume Into Structured Data
        </p>

        {isUploading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-navy-600 mx-auto mb-4"></div>
            <p className="text-lg">Uploading your resume...</p>
          </div>
        ) : (
          <FileUpload onUpload={handleUpload} />
        )}
      </div>
    </div>
  )
}
