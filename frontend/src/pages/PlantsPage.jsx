import { useState, useEffect } from 'react'
import { plantsAPI, sensorAPI } from '../services/api'
import PlantCard from '../components/PlantCard'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import './PlantsPage.css'

export default function PlantsPage({ onSelectPlant }) {
  const [plants, setPlants] = useState([])
  const [sensorData, setSensorData] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    species: '',
    moisture_threshold_min: 30,
    moisture_threshold_max: 80,
    is_active: true,
  })

  useEffect(() => {
    fetchPlants()
  }, [])

  const fetchPlants = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await plantsAPI.getAll()
      setPlants(res.data)

      // Fetch latest sensor data for each plant
      const sensorMap = {}
      for (const plant of res.data) {
        try {
          const sensorRes = await sensorAPI.getLatest(plant.id)
          sensorMap[plant.id] = sensorRes.data
        } catch {
          // Ignore sensor fetch errors
        }
      }
      setSensorData(sensorMap)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleAddPlant = async (e) => {
    e.preventDefault()
    try {
      await plantsAPI.create(formData)
      setFormData({
        name: '',
        species: '',
        moisture_threshold_min: 30,
        moisture_threshold_max: 80,
        is_active: true,
      })
      setShowForm(false)
      await fetchPlants()
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    }
  }

  const handleDeletePlant = async (plantId) => {
    try {
      await plantsAPI.delete(plantId)
      await fetchPlants()
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    }
  }

  if (loading) return <LoadingSpinner message="Loading plants..." />

  return (
    <div className="plants-page">
      <div className="page-header">
        <h1>My Plants</h1>
        <button
          className="btn-primary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Cancel' : '+ Add Plant'}
        </button>
      </div>

      {error && (
        <ErrorAlert
          message={error}
          onDismiss={() => setError(null)}
        />
      )}

      {showForm && (
        <form className="plant-form" onSubmit={handleAddPlant}>
          <div className="form-group">
            <label>Plant Name *</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Tomato Plant"
            />
          </div>

          <div className="form-group">
            <label>Species</label>
            <input
              type="text"
              value={formData.species}
              onChange={(e) => setFormData({ ...formData, species: e.target.value })}
              placeholder="e.g., Solanum lycopersicum"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Min Moisture Threshold (%)</label>
              <input
                type="number"
                min="0"
                max="100"
                value={formData.moisture_threshold_min}
                onChange={(e) => setFormData({ ...formData, moisture_threshold_min: parseFloat(e.target.value) })}
              />
            </div>

            <div className="form-group">
              <label>Max Moisture Threshold (%)</label>
              <input
                type="number"
                min="0"
                max="100"
                value={formData.moisture_threshold_max}
                onChange={(e) => setFormData({ ...formData, moisture_threshold_max: parseFloat(e.target.value) })}
              />
            </div>
          </div>

          <div className="form-group checkbox">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
            />
            <label htmlFor="is_active">Active</label>
          </div>

          <button type="submit" className="btn-primary btn-full">
            Create Plant
          </button>
        </form>
      )}

      {plants.length > 0 ? (
        <div className="plants-grid">
          {plants.map((plant) => (
            <PlantCard
              key={plant.id}
              plant={plant}
              moisture={sensorData[plant.id]?.latest_moisture}
              temperature={sensorData[plant.id]?.latest_temperature}
              onSelect={onSelectPlant}
              onDelete={handleDeletePlant}
            />
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <h3>No plants yet</h3>
          <p>Add your first plant to get started</p>
        </div>
      )}
    </div>
  )
}
