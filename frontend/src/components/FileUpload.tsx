import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload } from 'lucide-react'

interface FileUploadProps {
  onUpload: (file: File) => void
}

export default function FileUpload({ onUpload }: FileUploadProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onUpload(acceptedFiles[0])
    }
  }, [onUpload])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'text/plain': ['.txt']
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024 // 10MB
  })

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all
        ${isDragActive ? 'border-navy-500 bg-navy-50' : 'border-gray-300 hover:border-navy-400'}
      `}
    >
      <input {...getInputProps()} />
      <Upload className="mx-auto h-16 w-16 text-navy-600 mb-4" />
      <p className="text-lg font-semibold mb-2">
        {isDragActive ? 'Drop your resume here' : 'Drag & drop your resume here'}
      </p>
      <p className="text-gray-600 mb-4">or</p>
      <button className="btn-primary">
        Browse Files
      </button>
      <p className="text-sm text-gray-500 mt-4">
        Supported: PDF, DOCX, DOC, TXT (Max 10MB)
      </p>
    </div>
  )
}
