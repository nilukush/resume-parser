import { Routes, Route } from 'react-router-dom'
import UploadPage from './pages/UploadPage'
import ProcessingPage from './pages/ProcessingPage'
import ReviewPage from './pages/ReviewPage'
import ShareManagementPage from './pages/ShareManagementPage'
import PublicSharedResumePage from './pages/PublicSharedResumePage'

/**
 * AppRoutes
 *
 * Defines route configuration without Router wrapper.
 * This allows tests to use MemoryRouter while production uses BrowserRouter.
 *
 * Architecture Pattern: Separation of routing logic from router provider
 *
 * Routes:
 * - /share/:id → ShareManagementPage (owner view - manage share settings)
 * - /shared/:token → PublicSharedResumePage (public view - read-only resume)
 */
export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<UploadPage />} />
      <Route path="/processing/:id" element={<ProcessingPage />} />
      <Route path="/review/:id" element={<ReviewPage />} />
      <Route path="/share/:id" element={<ShareManagementPage />} />
      <Route path="/shared/:token" element={<PublicSharedResumePage />} />
    </Routes>
  )
}
