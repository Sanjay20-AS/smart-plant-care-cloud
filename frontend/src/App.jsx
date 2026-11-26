import { useState, useEffect } from 'react'
import { supabase } from './services/supabaseClient'
import authService from './services/auth'
import DashboardPage from './pages/DashboardPage'
import PlantsPage from './pages/PlantsPage'
import PlantDetailsPage from './pages/PlantDetailsPage'
import AlertsPage from './pages/AlertsPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import LoadingSpinner from './components/LoadingSpinner'

function App() {
  const [currentPage, setCurrentPage] = useState('loading')
  const [selectedPlant, setSelectedPlant] = useState(null)
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Initialize authentication on mount
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const currentUser = await authService.getCurrentUser()
        setUser(currentUser)
        setCurrentPage(currentUser ? 'dashboard' : 'login')
      } catch (err) {
        console.error('Failed to initialize auth:', err)
        setCurrentPage('login')
      } finally {
        setLoading(false)
      }
    }

    initializeAuth()

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        if (session && session.user) {
          setUser(session.user)
          // Don't redirect to dashboard if already on a protected page
          setCurrentPage((prevPage) => {
            if (['login', 'register'].includes(prevPage)) {
              return 'dashboard'
            }
            return prevPage
          })
        } else {
          setUser(null)
          setCurrentPage('login')
        }
      }
    )

    return () => {
      subscription?.unsubscribe()
    }
  }, [])

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

  const handleLogout = async () => {
    try {
      await authService.logout()
      setUser(null)
      setCurrentPage('login')
    } catch (err) {
      console.error('Logout failed:', err)
    }
  }

  const handleLoginSuccess = () => {
    setCurrentPage('dashboard')
  }

  const handleRegistrationSuccess = () => {
    setCurrentPage('login')
  }

  if (loading) {
    return (
      <div className="loading-container">
        <LoadingSpinner />
      </div>
    )
  }

  // Authentication pages
  if (currentPage === 'login') {
    return (
      <LoginPage
        onLoginSuccess={handleLoginSuccess}
        onNavigateToRegister={() => setCurrentPage('register')}
      />
    )
  }

  if (currentPage === 'register') {
    return (
      <RegisterPage
        onRegistrationSuccess={handleRegistrationSuccess}
        onNavigateToLogin={() => setCurrentPage('login')}
      />
    )
  }

  // Protected app pages (require authentication)
  if (!user) {
    return (
      <LoginPage
        onLoginSuccess={handleLoginSuccess}
        onNavigateToRegister={() => setCurrentPage('register')}
      />
    )
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
            <button
              className="nav-link logout-btn"
              onClick={handleLogout}
            >
              Logout ({user?.email || 'User'})
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
        <p>Smart Plant Care System v1.0.0 | Phase 6 - Authentication & Cloud Integration</p>
      </footer>
    </div>
  )
}

export default App
