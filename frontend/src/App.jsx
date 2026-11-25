import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [apiStatus, setApiStatus] = useState('Loading...')
  const [error, setError] = useState(null)

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
        const response = await fetch(`${apiUrl.replace('/api/v1', '')}/health`)
        const data = await response.json()
        setApiStatus(`Backend is running: ${data.service} v${data.version}`)
      } catch (err) {
        setError(`Backend error: ${err.message}`)
        setApiStatus('Backend not responding')
      }
    }

    checkBackend()
  }, [])

  return (
    <div className="container">
      <header>
        <h1>Smart Plant Care Dashboard</h1>
        <p>Cloud-Connected Plant Monitoring & Watering System</p>
      </header>

      <main>
        <section className="status-section">
          <h2>System Status</h2>
          <div className="status-box">
            <p className={error ? 'status-error' : 'status-ok'}>
              {error || apiStatus}
            </p>
          </div>
        </section>

        <section className="placeholder-section">
          <h2>Dashboard</h2>
          <div className="placeholder">
            <p>Dashboard and plant monitoring features coming in Phase 3</p>
          </div>
        </section>

        <section className="placeholder-section">
          <h2>Recent Data</h2>
          <div className="placeholder">
            <p>Real-time sensor data visualizations coming soon</p>
          </div>
        </section>
      </main>

      <footer>
        <p>Smart Plant Care System v1.0.0 | Foundation Setup Phase</p>
      </footer>
    </div>
  )
}

export default App
