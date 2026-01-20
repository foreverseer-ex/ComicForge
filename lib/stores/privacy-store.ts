import { create } from "zustand"
import { persist } from "zustand/middleware"

interface PrivacyState {
  privacyMode: boolean
  setPrivacyMode: (enabled: boolean) => void
  togglePrivacyMode: () => void
}

export const usePrivacyStore = create<PrivacyState>()(
  persist(
    (set) => ({
      privacyMode: false,
      setPrivacyMode: (enabled) => set({ privacyMode: enabled }),
      togglePrivacyMode: () => set((state) => ({ privacyMode: !state.privacyMode })),
    }),
    {
      name: "privacy-storage",
    }
  )
)
