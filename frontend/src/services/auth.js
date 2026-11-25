/**
 * Authentication service using Supabase Auth
 */
import { supabase } from './supabaseClient'

export const authService = {
  /**
   * Register a new user
   */
  register: async (email, password) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    })
    if (error) throw error
    return data
  },

  /**
   * Login with email and password
   */
  login: async (email, password) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    if (error) throw error
    return data
  },

  /**
   * Logout the current user
   */
  logout: async () => {
    const { error } = await supabase.auth.signOut()
    if (error) throw error
  },

  /**
   * Get the current user
   */
  getCurrentUser: async () => {
    const { data, error } = await supabase.auth.getUser()
    if (error) throw error
    return data.user
  },

  /**
   * Get the current session
   */
  getSession: async () => {
    const { data, error } = await supabase.auth.getSession()
    if (error) throw error
    return data.session
  },

  /**
   * Refresh the session
   */
  refreshSession: async () => {
    const { data, error } = await supabase.auth.refreshSession()
    if (error) throw error
    return data.session
  },

  /**
   * Reset password
   */
  resetPassword: async (email) => {
    const { data, error } = await supabase.auth.resetPasswordForEmail(email)
    if (error) throw error
    return data
  },

  /**
   * Update password
   */
  updatePassword: async (newPassword) => {
    const { data, error } = await supabase.auth.updateUser({
      password: newPassword,
    })
    if (error) throw error
    return data
  },

  /**
   * Get authorization header for API requests
   */
  getAuthHeader: async () => {
    const session = await authService.getSession()
    if (!session || !session.access_token) {
      return null
    }
    return {
      Authorization: `Bearer ${session.access_token}`,
    }
  },
}

export default authService
