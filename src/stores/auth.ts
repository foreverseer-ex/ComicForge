import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(null)
  const user = ref<any | null>(null)

  const isAuthenticated = computed(() => !!accessToken.value)

  function setToken(token: string | null) {
    accessToken.value = token
  }

  function setUser(u: any | null) {
    user.value = u
  }

  function logout() {
    accessToken.value = null
    user.value = null
  }

  return { accessToken, user, isAuthenticated, setToken, setUser, logout }
})
