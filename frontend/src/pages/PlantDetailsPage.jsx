import { useState, useEffect } from 'react'
import {
  plantsAPI,
  sensorAPI,
  wateringAPI,
  analyticsAPI,
} from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import MoistureIndicator from '../components/MoistureIndicator'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import './PlantDetailsPage.css'

export default function PlantDetailsPage({ plantId, onBack }) {
  const [plant, setPlant] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [readings, setReadings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [wateringDecision, setWateringDecision] = useState(null)
  const [wateringLoading, setWateringLoading] = useState(false)

  useEffect(() => {
    if (!plantId) {
      onBack()
      return
    }
    fetchPlantDetails()
  }, [plantId, onBack])

  const fetchPlantDetails = async () => {
    try {
      setLoading(true)
      setError(null)

      const [plantRes, analyticsRes, sensorRes] = await Promise.allSettled([
        plantsAPI.get(plantId),
        analyticsAPI.getPlantAnalytics(plantId),
        sensorAPI.getByPlant(plantId),
      ])

      if (plantRes.status === 'fulfilled') {
        setPlant(plantRes.value.data)
      }
      if (analyticsRes.status === 'fulfilled') {
        setAnalytics(analyticsRes.value.data)
      }
      if (sensorRes.status === 'fulfilled') {
        const sorted = sensorRes.value.data.sort(
          (a, b) => new Date(b.reading_timestamp) - new Date(a.reading_timestamp)
        )
        setReadings(sorted)
      }

      // Fetch watering decision
      try {
        const decisionRes = await wateringAPI.getDecision(plantId)
        setWateringDecision(decisionRes.data)
      } catch {
        // Ignore decision fetch errors
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleWatering = async () => {
    try {
      setWateringLoading(true)
      const res = await wateringAPI.execute(plantId)
      alert(`Watering executed: ${res.data.message}`)
      await fetchPlantDetails()
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setWateringLoading(false)
    }
  }

  if (loading) return <LoadingSpinner message="Loading plant details..." />
  if (!plant) return <ErrorAlert message="Plant not found" />

  // Prepare chart data
  const chartData = readings
    .slice()
    .reverse()
    .slice(-24)
    .map((r) => ({
      timestamp: new Date(r.reading_timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      }),
      moisture: r.soil_moisture,
      temperature: r.temperature,
      humidity: r.humidity,
    }))

  return (
    <div className="plant-details-page">
      <button className="btn-back" onClick={onBack}>
        ← Back to Plants
      </button>

      {error && (
        <ErrorAlert
          message={error}
          onDismiss={() => setError(null)}
        />
      )}

      <div className="details-header">
        <div>
          <h1>{plant.name}</h1>
          {plant.species && <p className="species">{plant.species}</p>}
        </div>
      </div>

      <div className="details-grid">
        {/* Sensor Status */}
        <section className="detail-card">
          <h2>Current Status</h2>
          {analytics ? (
            <>
              <div className="status-item">
                <label>Latest Moisture</label>
                {analytics.latest_moisture !== null ? (
                  <MoistureIndicator
                    moisture={analytics.latest_moisture}
                    minThreshold={plant.moisture_threshold_min}
                    maxThreshold={plant.moisture_threshold_max}
                  />
                ) : (
                  <p className="no-data">No data</p>
                )}
              </div>

              {analytics.latest_temperature !== null && (
                <div className="status-item">
                  <label>Temperature</label>
                  <p className="value">{analytics.latest_temperature.toFixed(1)}°C</p>
                </div>
              )}

              {analytics.latest_humidity !== null && (
                <div className="status-item">
                  <label>Humidity</label>
                  <p className="value">{analytics.latest_humidity.toFixed(1)}%</p>
                </div>
              )}

              <div className="status-item">
                <label>Last Reading</label>
                <p className="value">
                  {analytics.last_reading_timestamp
                    ? new Date(analytics.last_reading_timestamp).toLocaleString()
                    : 'Never'}
                </p>
              </div>
            </>
          ) : (
            <p className="no-data">No sensor data available</p>
          )}
        </section>

        {/* Watering Status */}
        <section className="detail-card">
          <h2>Watering Status</h2>
          {wateringDecision ? (
            <>
              <div className="status-item">
                <label>Eligible for Watering</label>
                <p className={`badge badge-${wateringDecision.eligible ? 'success' : 'warning'}`}>
                  {wateringDecision.eligible ? 'Yes' : 'No'}
                </p>
              </div>

              <div className="status-item">
                <label>Reason</label>
                <p className="reason">{wateringDecision.reason}</p>
              </div>

              {wateringDecision.cooldown_remaining_minutes && (
                <div className="status-item">
                  <label>Cooldown Remaining</label>
                  <p className="value">{wateringDecision.cooldown_remaining_minutes} min</p>
                </div>
              )}

              {wateringDecision.daily_limit_remaining !== null && (
                <div className="status-item">
                  <label>Daily Watering Remaining</label>
                  <p className="value">{wateringDecision.daily_limit_remaining}</p>
                </div>
              )}

              <button
                className="btn-primary btn-full"
                onClick={handleWatering}
                disabled={!wateringDecision.eligible || wateringLoading}
              >
                {wateringLoading ? 'Watering...' : 'Water Plant (Virtual)'}
              </button>
            </>
          ) : (
            <p className="no-data">Unable to determine watering status</p>
          )}
        </section>

        {/* Plant Configuration */}
        <section className="detail-card">
          <h2>Configuration</h2>
          <div className="status-item">
            <label>Min Moisture Threshold</label>
            <p className="value">{plant.moisture_threshold_min}%</p>
          </div>
          <div className="status-item">
            <label>Max Moisture Threshold</label>
            <p className="value">{plant.moisture_threshold_max}%</p>
          </div>
          <div className="status-item">
            <label>Status</label>
            <p className={`badge badge-${plant.is_active ? 'active' : 'inactive'}`}>
              {plant.is_active ? 'Active' : 'Inactive'}
            </p>
          </div>
        </section>

        {/* Statistics */}
        {analytics && (
          <section className="detail-card">
            <h2>Statistics</h2>
            <div className="status-item">
              <label>Readings Today</label>
              <p className="value">{analytics.recent_readings_24h}</p>
            </div>
            <div className="status-item">
              <label>Total Readings</label>
              <p className="value">{analytics.reading_count}</p>
            </div>
            <div className="status-item">
              <label>Devices</label>
              <p className="value">{analytics.active_devices}/{analytics.device_count}</p>
            </div>
            <div className="status-item">
              <label>Recent Waterings</label>
              <p className="value">{analytics.recent_watering_count}</p>
            </div>
          </section>
        )}
      </div>

      {/* Sensor Chart */}
      {chartData.length > 0 && (
        <section className="detail-card chart-card">
          <h2>Sensor Readings (Last 24 Hours)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="moisture"
                stroke="#0984e3"
                name="Moisture (%)"
                dot={false}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="temperature"
                stroke="#e17055"
                name="Temperature (°C)"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </section>
      )}

      {/* Recent Readings */}
      {readings.length > 0 && (
        <section className="detail-card">
          <h2>Recent Readings</h2>
          <div className="readings-list">
            {readings.slice(0, 10).map((reading, idx) => (
              <div key={idx} className="reading-item">
                <span className="reading-time">
                  {new Date(reading.reading_timestamp).toLocaleString()}
                </span>
                <span className="reading-moisture">
                  {reading.soil_moisture.toFixed(1)}% moisture
                </span>
                {reading.temperature && (
                  <span className="reading-temp">{reading.temperature.toFixed(1)}°C</span>
                )}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
