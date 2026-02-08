import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react'
import type { User, UserProfile } from '../types'
import { authApi, userApi } from '../services/api'
import i18n, { getLocaleFromCountry } from '../i18n'

interface AuthContextType {
  user: User | null
  profile: UserProfile | null
  isLoading: boolean
  isAuthenticated: boolean
  hasProfile: boolean
  googleClientId: string | null
  login: (credential: string) => Promise<{ hasProfile: boolean }>
  logout: () => void
  refreshProfile: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [googleClientId, setGoogleClientId] = useState<string | null>(null)

  const fetchProfile = useCallback(async () => {
    try {
      const response = await userApi.getProfile()
      if (response.data.success) {
        setProfile(response.data.data)
        return true
      }
    } catch {
      setProfile(null)
    }
    return false
  }, [])

  const fetchUser = useCallback(async () => {
    try {
      const response = await userApi.getMe()
      if (response.data.success) {
        setUser(response.data.data)
        return true
      }
    } catch {
      setUser(null)
    }
    return false
  }, [])

  // Initialize auth state
  useEffect(() => {
    const init = async () => {
      // Fetch Google Client ID
      try {
        const configResponse = await authApi.getGoogleConfig()
        if (configResponse.data.success) {
          setGoogleClientId(configResponse.data.data.client_id)
        }
      } catch (error) {
        console.error('Failed to fetch Google config:', error)
      }

      // Check if user is already logged in
      const token = localStorage.getItem('access_token')
      if (token) {
        const userFetched = await fetchUser()
        if (userFetched) {
          await fetchProfile()
        }
      }
      setIsLoading(false)
    }
    init()
  }, [fetchUser, fetchProfile])

  const login = async (credential: string) => {
    const response = await authApi.googleLogin(credential)
    if (response.data.success) {
      const { user: userData, access_token, refresh_token } = response.data.data
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      setUser(userData)

      // Check if user has profile
      const hasProfile = await fetchProfile()
      return { hasProfile }
    }
    throw new Error('Login failed')
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
    setProfile(null)
  }

  // Auto-detect language from profile country (only if user hasn't manually chosen)
  useEffect(() => {
    if (profile?.country?.code && !localStorage.getItem('i18n_language')) {
      const locale = getLocaleFromCountry(profile.country.code)
      i18n.changeLanguage(locale)
    }
  }, [profile?.country?.code])

  const refreshProfile = async () => {
    await fetchProfile()
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        isLoading,
        isAuthenticated: !!user,
        hasProfile: !!profile,
        googleClientId,
        login,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
