/**
 * API service for communicating with the backend
 */
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

// Plants API
export const plantsAPI = {
  getAll: (skip = 0, limit = 100, activeOnly = false) =>
    api.get('/plants', { params: { skip, limit, active_only: activeOnly } }),
  get: (plantId) => api.get(`/plants/${plantId}`),
  create: (data) => api.post('/plants', data),
  update: (plantId, data) => api.put(`/plants/${plantId}`, data),
  delete: (plantId) => api.delete(`/plants/${plantId}`),
}

// Devices API
export const devicesAPI = {
  getAll: (skip = 0, limit = 100) => api.get('/devices', { params: { skip, limit } }),
  get: (deviceId) => api.get(`/devices/${deviceId}`),
  register: (data) => api.post('/devices', data),
  update: (deviceId, data) => api.put(`/devices/${deviceId}`, data),
  delete: (deviceId) => api.delete(`/devices/${deviceId}`),
}

// Sensor Readings API
export const sensorAPI = {
  ingest: (data) => api.post('/sensor-readings', data),
  getByPlant: (plantId) => api.get(`/sensor-readings/plant/${plantId}`),
  getLatest: (plantId) => api.get(`/sensor-readings/latest/${plantId}`),
}

// Watering API
export const wateringAPI = {
  getDecision: (plantId) => api.post(`/watering/decision/${plantId}`),
  execute: (plantId) => api.post(`/watering/execute/${plantId}`),
  getHistory: (plantId) => api.get(`/watering/history/${plantId}`),
  getSummary: (plantId) => api.get(`/watering/summary/${plantId}`),
}

// Alerts API
export const alertsAPI = {
  getAll: () => api.get('/alerts'),
  get: (alertId) => api.get(`/alerts/${alertId}`),
  update: (alertId, data) => api.put(`/alerts/${alertId}`, data),
}

// Analytics API
export const analyticsAPI = {
  getPlantAnalytics: (plantId) => api.get(`/analytics/plant/${plantId}`),
  getSystemSummary: () => api.get('/analytics/summary'),
}

// Health API (utility)
export const healthAPI = {
  check: () => axios.get(`${API_BASE_URL.replace('/api/v1', '')}/health`),
}

export default api
