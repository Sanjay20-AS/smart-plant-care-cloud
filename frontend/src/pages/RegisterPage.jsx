import { useState } from 'react'
import authService from '../services/auth'
import ErrorAlert from '../components/ErrorAlert'
import LoadingSpinner from '../components/LoadingSpinner'
import './RegisterPage.css'

function RegisterPage({ onRegistrationSuccess, onNavigateToLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess(false)

    // Validate passwords match
    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    // Validate password strength
    if (password.length < 8) {
      setError('Password must be at least 8 characters long')
      return
    }

    setLoading(true)

    try {
      await authService.register(email, password)
      setSuccess(true)
      setEmail('')
      setPassword('')
      setConfirmPassword('')

      // Auto-navigate after a short delay
      setTimeout(() => {
        onRegistrationSuccess()
      }, 2000)
    } catch (err) {
      const errorMsg = err.message || 'Registration failed'
      // Handle specific error messages from Supabase
      if (errorMsg.includes('already registered')) {
        setError('This email is already registered. Please login or use another email.')
      } else if (errorMsg.includes('invalid email')) {
        setError('Please enter a valid email address.')
      } else {
        setError(errorMsg)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-box">
        <div className="auth-header">
          <h1>🌱 Smart Plant Care</h1>
          <p>Create your account</p>
        </div>

        {success && (
          <div className="success-alert">
            <p>✓ Registration successful! Redirecting to login...</p>
          </div>
        )}

        {error && <ErrorAlert message={error} onDismiss={() => setError('')} />}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
              disabled={loading || success}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 characters"
              required
              disabled={loading || success}
            />
            <small>Must be at least 8 characters</small>
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm password"
              required
              disabled={loading || success}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={loading || success}
          >
            {loading ? <LoadingSpinner /> : 'Register'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Already have an account?{' '}
            <button
              type="button"
              className="link-button"
              onClick={onNavigateToLogin}
              disabled={loading}
            >
              Login here
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}

export default RegisterPage
