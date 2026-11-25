import { useState, useEffect } from 'react'
import { analyticsAPI, healthAPI } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import './DashboardPage.css'

export default function DashboardPage({ onNavigate }) {
  const [summary, setSummary] = useState(null)
  const [healthStatus, setHealthStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)

        // Fetch system summary
        const summaryRes = await analyticsAPI.getSystemSummary()
        setSummary(summaryRes.data)

        // Check health
        try {
          const healthRes = await healthAPI.check()
          setHealthStatus(healthRes.data)
        } catch {
          setHealthStatus({ status: 'error' })
        }
      } catch (err) {
        setError(err.response?.data?.detail || err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) return <LoadingSpinner message="Loading dashboard..." />

  return (
    <div className="dashboard-page">
      <section className="dashboard-header">
        <h1>System Dashboard</h1>
        <p>Cloud-Connected Smart Plant Care System</p>
      </section>

      {error && (
        <ErrorAlert
          message={error}
          onDismiss={() => setError(null)}
        />
      )}

      {healthStatus && (
        <div className={`health-banner health-${healthStatus.status || 'unknown'}`}>
          <span className="health-indicator"></span>
          <div>
            <strong>Backend Status</strong>
            <p>{healthStatus.service || 'Smart Plant Care API'} v{healthStatus.version || '1.0.0'}</p>
          </div>
        </div>
      )}

      {summary ? (
        <div className="dashboard-grid">
          <div className="stat-card">
            <h3>Plants</h3>
            <div className="stat-value">{summary.total_plants}</div>
            <p className="stat-subtitle">
              {summary.active_plants} active
            </p>
          </div>

          <div className="stat-card">
            <h3>Devices</h3>
            <div className="stat-value">{summary.total_devices}</div>
            <p className="stat-subtitle">
              {summary.active_devices} active
            </p>
          </div>

          <div className="stat-card">
            <h3>Sensor Readings</h3>
            <div className="stat-value">{summary.total_readings}</div>
            <p className="stat-subtitle">
              Total readings recorded
            </p>
          </div>

          <div className="stat-card">
            <h3>Watering Events</h3>
            <div className="stat-value">{summary.total_watering_events}</div>
            <p className="stat-subtitle">
              Total watering actions
            </p>
          </div>

          <div className="stat-card">
            <h3>Active Alerts</h3>
            <div className="stat-value alert-count">{summary.active_alerts}</div>
            <p className="stat-subtitle">
              {summary.critical_alerts} critical
            </p>
          </div>

          <div className="stat-card">
            <h3>System Health</h3>
            <div className="stat-value health-ok">✓</div>
            <p className="stat-subtitle">
              All systems operational
            </p>
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <p>Unable to load system summary</p>
        </div>
      )}

      <div className="dashboard-actions">
        <button
          className="btn-primary btn-large"
          onClick={() => onNavigate('plants')}
        >
          Go to Plants
        </button>
        <button
          className="btn-secondary btn-large"
          onClick={() => onNavigate('alerts')}
        >
          View Alerts
        </button>
      </div>
    </div>
  )
}
