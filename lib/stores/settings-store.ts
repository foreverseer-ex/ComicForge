import { create } from "zustand"
import { persist } from "zustand/middleware"

interface DevSettings {
  enableAuthRedirect: boolean
}

interface SettingsState {
  dev: DevSettings
  setEnableAuthRedirect: (enabled: boolean) => void
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      dev: {
        enableAuthRedirect: true, // 默认启用
      },
      setEnableAuthRedirect: (enabled: boolean) =>
        set((state) => ({
          dev: {
            ...state.dev,
            enableAuthRedirect: enabled,
          },
        })),
    }),
    {
      name: "settings-storage",
    }
  )
)
