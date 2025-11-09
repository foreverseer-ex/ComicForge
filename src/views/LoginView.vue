<template>
  <div class="w-full px-4">
    <div class="mx-auto w-full max-w-sm">
      <!-- 卡片 -->
      <div class="rounded-xl border shadow-sm bg-white/80 backdrop-blur dark:bg-neutral-900/80 dark:border-neutral-800">
        <div class="px-6 pt-6">
          <div class="flex items-center gap-2">
            <div class="h-8 w-8 rounded-md bg-blue-600 flex items-center justify-center text-white font-bold">CF</div>
            <div>
              <h1 class="text-lg font-semibold leading-none">{{ mode === 'login' ? '登录账户' : '创建账户' }}</h1>
              <p class="text-sm text-neutral-500 dark:text-neutral-400">ComicForge</p>
            </div>
          </div>
        </div>

        <!-- 表单 -->
        <form class="px-6 pt-4 pb-6 space-y-4" @submit.prevent="onSubmit">
          <!-- 用户名/别名 -->
          <div class="space-y-2">
            <label class="text-sm font-medium">用户名 / 别名</label>
            <input
              v-model="username"
              class="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500 dark:bg-neutral-900 dark:text-neutral-100 dark:border-neutral-800"
              placeholder="用户名或别名"
              autocomplete="username"
            />
          </div>

          <!-- 别名（注册可选） -->
          <div v-if="mode==='register'" class="space-y-2">
            <label class="text-sm font-medium">别名（可选，逗号分隔）</label>
            <input
              v-model="aliases"
              class="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500 dark:bg-neutral-900 dark:text-neutral-100 dark:border-neutral-800"
              placeholder="例如：alice, alice@example.com"
              autocomplete="off"
            />
          </div>

          <!-- 密码 -->
          <div class="space-y-2">
            <label class="text-sm font-medium">密码</label>
            <input
              v-model="password"
              type="password"
              class="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500 dark:bg-neutral-900 dark:text-neutral-100 dark:border-neutral-800"
              placeholder="密码"
              autocomplete="current-password"
            />
          </div>

          <!-- 注册：确认密码（可选） -->
          <div v-if="mode==='register'" class="space-y-2">
            <label class="text-sm font-medium">确认密码</label>
            <input
              v-model="password2"
              type="password"
              class="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500 dark:bg-neutral-900 dark:text-neutral-100 dark:border-neutral-800"
              placeholder="再次输入密码"
              autocomplete="new-password"
            />
          </div>

          <!-- 错误提示 -->
          <p v-if="error" class="text-sm text-red-500">{{ error }}</p>

          <!-- 操作按钮 -->
          <div class="flex items-center gap-2 pt-1">
            <button
              type="submit"
              :disabled="loading"
              class="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium h-9 px-4 bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {{ loading ? (mode==='login' ? '登录中…' : '注册中…') : (mode==='login' ? '登录' : '注册') }}
            </button>
            <button
              type="button"
              class="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium h-9 px-4 border border-neutral-200 hover:bg-neutral-50 dark:border-neutral-800 dark:hover:bg-neutral-800"
              @click="toggleMode"
            >
              {{ mode==='login' ? '没有账号？去注册' : '已有账号？去登录' }}
            </button>
          </div>
        </form>
      </div>

      <!-- 底部说明 -->
      <p class="text-center text-xs text-neutral-500 mt-3">受保护的环境，登录后访问。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const mode = ref<'login'|'register'>('login')
const username = ref('')
const aliases = ref('')
const password = ref('')
const password2 = ref('')
const loading = ref(false)
const error = ref('')

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    if (mode.value === 'register') {
      const uname = username.value.trim()
      const pw = password.value
      if (!uname || !pw) throw new Error('请输入用户名与密码')
      if (password2.value && password2.value !== pw) throw new Error('两次输入的密码不一致')
      await api.post('/auth/register', {
        username: uname,
        password: pw,
        aliases: aliases.value
          ? aliases.value.split(',').map(s => s.trim()).filter(Boolean)
          : null,
      })
      // 注册完成后自动切回登录
      mode.value = 'login'
    }

    if (mode.value === 'login') {
      const uname = username.value.trim()
      const pw = password.value
      const resp = await api.post<{ access_token: string; expires_in: number }>('/auth/login', {
        username: uname,
        password: pw,
      }) as any
      const access = (resp?.access_token) ?? (resp?.data?.access_token)
      if (!access) throw new Error('登录失败')
      auth.setToken(access)
      // 拉取用户信息
      try {
        const me = await api.get('/auth/me')
        auth.setUser(me)
      } catch {}
      router.replace({ name: 'Home' })
    }
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? '登录失败'
  } finally {
    loading.value = false
  }
}

function toggleMode() {
  error.value = ''
  mode.value = mode.value === 'login' ? 'register' : 'login'
}
</script>

<style scoped>
</style>
