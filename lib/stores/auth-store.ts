import { create } from "zustand"
import { persist } from "zustand/middleware"

interface AuthState {
  isAuthenticated: boolean
  token: string | null
  user: {
    id: string
    username: string
    isAdmin: boolean
  } | null
  login: (token: string, user: { id: string; username: string; isAdmin: boolean }) => void
  logout: () => void
  setToken: (token: string | null) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      token: null,
      user: null,
      login: (token: string, user: { id: string; username: string; isAdmin: boolean }) =>
        set({
          isAuthenticated: true,
          token,
          user,
        }),
      logout: () =>
        set({
          isAuthenticated: false,
          token: null,
          user: null,
        }),
      setToken: (token: string | null) =>
        set({ token }),
    }),
    {
      name: "auth-storage",
    }
  )
)
