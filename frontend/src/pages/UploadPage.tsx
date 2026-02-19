import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import FileUpload from '../components/FileUpload'

export default function UploadPage() {
  const navigate = useNavigate()
  const [isUploading, setIsUploading] = useState(false)

  const handleUpload = async (file: File) => {
    setIsUploading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/resumes/upload`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      const data = await response.json()
      // Navigate to processing page
      navigate(`/processing/${data.resume_id}`)
    } catch (error) {
      console.error('Upload error:', error)
      alert('Failed to upload resume. Please try again.')
    } finally {
      setIsUploading(false)
    }
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
