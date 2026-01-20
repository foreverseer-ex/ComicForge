import { create } from "zustand"
import { persist } from "zustand/middleware"

export type Theme = "light" | "dark" | "system"

interface ThemeState {
  theme: Theme
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
  resolvedTheme: "light" | "dark"
  setResolvedTheme: (theme: "light" | "dark") => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: "system",
      resolvedTheme: "light",
      setTheme: (theme) => set({ theme }),
      toggleTheme: () => {
        const current = get()
        if (current.theme === "system") {
          // 如果当前是跟随系统，切换到与当前系统主题相反的主题
          const systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches
            ? "dark"
            : "light"
          const newTheme = systemTheme === "light" ? "dark" : "light"
          set({ theme: newTheme })
        } else {
          // 如果已经手动设置，在浅色和暗黑之间切换
          const newTheme = current.theme === "light" ? "dark" : "light"
          set({ theme: newTheme })
        }
      },
      setResolvedTheme: (resolvedTheme) => set({ resolvedTheme }),
    }),
    {
      name: "theme-storage",
    }
  )
)
