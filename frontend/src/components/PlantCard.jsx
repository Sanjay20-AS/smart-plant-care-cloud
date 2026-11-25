import { useState } from 'react'
import StatusBadge from './StatusBadge'
import MoistureIndicator from './MoistureIndicator'
import './PlantCard.css'

export default function PlantCard({ plant, onSelect, onDelete, moisture, temperature }) {
  const [showMenu, setShowMenu] = useState(false)

  return (
    <div className="plant-card">
      <div className="plant-card-header">
        <div>
          <h3>{plant.name}</h3>
          {plant.species && <p className="plant-species">{plant.species}</p>}
        </div>
        <div className="plant-menu">
          <button
            className="btn-menu"
            onClick={() => setShowMenu(!showMenu)}
          >
            ⋮
          </button>
          {showMenu && (
            <div className="menu-dropdown">
              <button onClick={() => { onSelect(plant); setShowMenu(false); }}>
                View Details
              </button>
              {onDelete && (
                <button
                  onClick={() => {
                    if (confirm(`Delete plant "${plant.name}"?`)) {
                      onDelete(plant.id)
                      setShowMenu(false)
                    }
                  }}
                  className="menu-delete"
                >
                  Delete
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      <StatusBadge status={plant.is_active} />

      <div className="plant-card-body">
        {moisture !== null && moisture !== undefined ? (
          <>
            <label>Soil Moisture</label>
            <MoistureIndicator
              moisture={moisture}
              minThreshold={plant.moisture_threshold_min}
              maxThreshold={plant.moisture_threshold_max}
            />
          </>
        ) : (
          <p className="no-data">No sensor data available</p>
        )}

        {temperature !== null && temperature !== undefined && (
          <div className="sensor-reading">
            <label>Temperature</label>
            <span>{temperature.toFixed(1)}°C</span>
          </div>
        )}

        <div className="threshold-info">
          <label>Watering Thresholds</label>
          <p>Min: {plant.moisture_threshold_min}% | Max: {plant.moisture_threshold_max}%</p>
        </div>
      </div>

      <button
        className="btn-primary btn-full"
        onClick={() => onSelect(plant)}
      >
        View Details
      </button>
    </div>
  )
}
