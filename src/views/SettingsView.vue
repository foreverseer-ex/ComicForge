<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div 
      :class="[
        'pb-4 border-b',
        isDark ? 'border-gray-700' : 'border-gray-200'
      ]"
    >
      <h1 
        :class="[
          'text-3xl font-bold mb-2',
          isDark ? 'text-white' : 'text-gray-900'
        ]"
      >
        应用设置
      </h1>
      <p 
        :class="[
          'text-sm italic',
          isDark ? 'text-gray-400' : 'text-gray-500'
        ]"
      >
        提示：修改后回车或点击其他地方自动保存
      </p>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2" 
           :class="isDark ? 'border-blue-500' : 'border-blue-600'"></div>
    </div>

    <!-- 设置内容 -->
    <div v-else class="space-y-8">
      <!-- 绘图设置 -->
      <DrawSettingsSection 
        :settings="settings.draw" 
        :is-dark="isDark"
        @update="handleUpdateDraw"
      />

      <!-- LLM 设置 -->
      <LlmSettingsSection 
        :settings="settings.llm" 
        :is-dark="isDark"
        @update="handleUpdateLlm"
      />

      <!-- Civitai 设置 -->
      <CivitaiSettingsSection 
        :settings="settings.civitai" 
        :is-dark="isDark"
        @update="handleUpdateCivitai"
      />

      <!-- SD Forge 设置 -->
      <SdForgeSettingsSection 
        :settings="settings.sd_forge" 
        :is-dark="isDark"
        @update="handleUpdateSdForge"
      />

      <!-- 前端设置 -->
      <FrontendSettingsSection 
        :is-dark="isDark"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useThemeStore } from '../stores/theme'
import { storeToRefs } from 'pinia'
import api from '../api'
import DrawSettingsSection from '../components/settings/DrawSettingsSection.vue'
import LlmSettingsSection from '../components/settings/LlmSettingsSection.vue'
import CivitaiSettingsSection from '../components/settings/CivitaiSettingsSection.vue'
import SdForgeSettingsSection from '../components/settings/SdForgeSettingsSection.vue'
import FrontendSettingsSection from '../components/settings/FrontendSettingsSection.vue'

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

const loading = ref(true)
const settings = ref<any>({
  llm: {},
  draw: {},
  civitai: {},
  sd_forge: {} // 注意：后端返回的是 sd_forge，但 API 路径是 sd-forge
})

// 加载所有设置
const loadSettings = async () => {
  loading.value = true
  try {
    const data = await api.get('/settings/')
    settings.value = data
  } catch (error: any) {
    console.error('加载设置失败:', error)
    alert('加载设置失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

// 更新绘图设置
const handleUpdateDraw = async (updates: any) => {
  try {
    await api.put('/settings/draw', updates)
    // 重新加载以获取最新值
    const updated = await api.get('/settings/draw')
    settings.value.draw = updated
  } catch (error: any) {
    console.error('更新绘图设置失败:', error)
    alert('更新绘图设置失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 更新 LLM 设置
const handleUpdateLlm = async (updates: any) => {
  try {
    await api.put('/settings/llm', updates)
    // 重新加载以获取最新值
    const updated = await api.get('/settings/llm')
    settings.value.llm = updated
  } catch (error: any) {
    console.error('更新 LLM 设置失败:', error)
    alert('更新 LLM 设置失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 更新 Civitai 设置
const handleUpdateCivitai = async (updates: any) => {
  try {
    await api.put('/settings/civitai', updates)
    // 重新加载以获取最新值
    const updated = await api.get('/settings/civitai')
    settings.value.civitai = updated
  } catch (error: any) {
    console.error('更新 Civitai 设置失败:', error)
    alert('更新 Civitai 设置失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 更新 SD Forge 设置
const handleUpdateSdForge = async (updates: any) => {
  try {
    await api.put('/settings/sd-forge', updates)
    // 重新加载以获取最新值
    const updated = await api.get('/settings/sd-forge')
    settings.value.sd_forge = updated
  } catch (error: any) {
    console.error('更新 SD Forge 设置失败:', error)
    alert('更新 SD Forge 设置失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 组件挂载时加载设置
onMounted(() => {
  loadSettings()
})
</script>
