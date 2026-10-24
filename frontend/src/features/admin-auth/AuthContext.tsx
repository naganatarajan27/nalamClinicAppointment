import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import * as adminApi from '../../api/adminApi'
import type { AdminMe } from '../../types/api'

interface AuthState {
  admin: AdminMe | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [admin, setAdmin] = useState<AdminMe | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    adminApi
      .me()
      .then(setAdmin)
      .catch(() => setAdmin(null))
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    await adminApi.login(email, password)
    const current = await adminApi.me()
    setAdmin(current)
  }, [])

  const logout = useCallback(async () => {
    await adminApi.logout()
    setAdmin(null)
  }, [])

  return <AuthContext.Provider value={{ admin, loading, login, logout }}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
