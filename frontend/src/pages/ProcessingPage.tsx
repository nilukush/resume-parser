import { useParams } from 'react-router-dom'

export default function ProcessingPage() {
  const { id } = useParams<{ id: string }>()

  return (
    <div className="min-h-screen bg-navy-50">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-navy-900">Processing Resume</h1>
        <p className="mt-4 text-gray-600">Processing ID: {id}</p>
        <p className="mt-2 text-gray-600">Page content coming soon...</p>
      </div>
    </div>
  )
}
