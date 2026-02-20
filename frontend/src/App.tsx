import { BrowserRouter as Router } from 'react-router-dom'
import { AppRoutes } from './AppRoutes'

/**
 * App
 *
 * Main application component with BrowserRouter for production.
 * Tests use MemoryRouter instead, importing AppRoutes directly.
 */
function App() {
  return (
    <Router>
      <AppRoutes />
    </Router>
  )
}

export default App
