import { useState } from 'react'
import DashboardPage from './pages/DashboardPage'
import PlantsPage from './pages/PlantsPage'
import PlantDetailsPage from './pages/PlantDetailsPage'
import AlertsPage from './pages/AlertsPage'

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [selectedPlant, setSelectedPlant] = useState(null)

  const handleSelectPlant = (plant) => {
    setSelectedPlant(plant)
    setCurrentPage('plant-details')
  }

  const handleBack = () => {
    setSelectedPlant(null)
    setCurrentPage('plants')
  }

  const handleNavigate = (page) => {
    setCurrentPage(page)
    setSelectedPlant(null)
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">🌱 Smart Plant Care</h1>
          <nav className="nav-menu">
            <button
              className={`nav-link ${currentPage === 'dashboard' ? 'active' : ''}`}
              onClick={() => handleNavigate('dashboard')}
            >
              Dashboard
            </button>
            <button
              className={`nav-link ${currentPage === 'plants' ? 'active' : ''}`}
              onClick={() => handleNavigate('plants')}
            >
              Plants
            </button>
            <button
              className={`nav-link ${currentPage === 'alerts' ? 'active' : ''}`}
              onClick={() => handleNavigate('alerts')}
            >
              Alerts
            </button>
          </nav>
        </div>
      </header>

      <main className="app-main">
        <div className="page-container">
          {currentPage === 'dashboard' && (
            <DashboardPage onNavigate={handleNavigate} />
          )}

          {currentPage === 'plants' && (
            <PlantsPage
              onSelectPlant={handleSelectPlant}
              selectedPlantId={selectedPlant?.id}
            />
          )}

          {currentPage === 'plant-details' && selectedPlant && (
            <PlantDetailsPage
              plantId={selectedPlant.id}
              onBack={handleBack}
            />
          )}

          {currentPage === 'alerts' && (
            <AlertsPage />
          )}
        </div>
      </main>

      <footer className="app-footer">
        <p>Smart Plant Care System v1.0.0 | Phase 5 - Frontend Dashboard</p>
      </footer>
    </div>
  )
}

export default App
