<template>
  <input
    v-bind="$attrs"
    :class="[
      'flex h-9 w-full rounded-lg border bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
      isDark ? 'border-gray-600 text-white placeholder-gray-400' : 'border-gray-300 text-gray-900 placeholder-gray-500'
    ]"
  />
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useThemeStore } from '../../stores/theme'

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)
</script>
