import { useState, useEffect } from 'react'
import { alertsAPI } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import StatusBadge from '../components/StatusBadge'
import './AlertsPage.css'

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('all') // all, active, resolved

  useEffect(() => {
    fetchAlerts()
  }, [])

  const fetchAlerts = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await alertsAPI.getAll()
      setAlerts(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateAlert = async (alertId, newStatus) => {
    try {
      await alertsAPI.update(alertId, { status: newStatus })
      await fetchAlerts()
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    }
  }

  if (loading) return <LoadingSpinner message="Loading alerts..." />

  const filteredAlerts = alerts.filter((alert) => {
    if (filter === 'active') return alert.status === 'active'
    if (filter === 'resolved') return alert.status === 'resolved'
    return true
  })

  const getSeverityIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return '🔴'
      case 'warning':
        return '🟡'
      case 'info':
        return '🔵'
      default:
        return '⚪'
    }
  }

  return (
    <div className="alerts-page">
      <div className="page-header">
        <h1>System Alerts</h1>
      </div>

      {error && (
        <ErrorAlert
          message={error}
          onDismiss={() => setError(null)}
        />
      )}

      <div className="alerts-toolbar">
        <div className="filter-buttons">
          <button
            className={`btn-filter ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All ({alerts.length})
          </button>
          <button
            className={`btn-filter ${filter === 'active' ? 'active' : ''}`}
            onClick={() => setFilter('active')}
          >
            Active ({alerts.filter((a) => a.status === 'active').length})
          </button>
          <button
            className={`btn-filter ${filter === 'resolved' ? 'active' : ''}`}
            onClick={() => setFilter('resolved')}
          >
            Resolved ({alerts.filter((a) => a.status === 'resolved').length})
          </button>
        </div>
      </div>

      {filteredAlerts.length > 0 ? (
        <div className="alerts-list">
          {filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`alert-item alert-${alert.severity?.toLowerCase()}`}
            >
              <div className="alert-icon">
                {getSeverityIcon(alert.severity)}
              </div>

              <div className="alert-content">
                <div className="alert-header">
                  <h3>{alert.alert_type.replace(/_/g, ' ').toUpperCase()}</h3>
                  <StatusBadge status={alert.status} type="alert" />
                </div>
                <p className="alert-message">{alert.message}</p>
                <div className="alert-meta">
                  <span className="alert-time">
                    {new Date(alert.created_at).toLocaleString()}
                  </span>
                  {alert.plant_id && (
                    <span className="alert-plant">Plant ID: {alert.plant_id}</span>
                  )}
                </div>
              </div>

              {alert.status === 'active' && (
                <div className="alert-actions">
                  <button
                    className="btn-secondary"
                    onClick={() => handleUpdateAlert(alert.id, 'acknowledged')}
                  >
                    Acknowledge
                  </button>
                </div>
              )}

              {alert.status !== 'resolved' && (
                <button
                  className="btn-secondary"
                  onClick={() => handleUpdateAlert(alert.id, 'resolved')}
                >
                  Resolve
                </button>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <h3>No {filter !== 'all' ? `${filter} ` : ''}alerts</h3>
          <p>Your system is running smoothly!</p>
        </div>
      )}
    </div>
  )
}
