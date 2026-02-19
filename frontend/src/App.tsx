import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import UploadPage from './pages/UploadPage'
import ProcessingPage from './pages/ProcessingPage'
import ReviewPage from './pages/ReviewPage'
import SharePage from './pages/SharePage'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/processing/:id" element={<ProcessingPage />} />
        <Route path="/review/:id" element={<ReviewPage />} />
        <Route path="/share/:id" element={<SharePage />} />
      </Routes>
    </Router>
  )
}

export default App
