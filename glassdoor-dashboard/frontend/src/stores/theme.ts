import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export type ThemeMode = 'dark' | 'light'

export const useThemeStore = defineStore('theme', () => {
  const saved = localStorage.getItem('theme') as ThemeMode | null
  const mode = ref<ThemeMode>(saved || 'dark')

  const toggle = () => {
    mode.value = mode.value === 'dark' ? 'light' : 'dark'
  }

  const isDark = () => mode.value === 'dark'

  watch(mode, (val) => {
    document.documentElement.setAttribute('data-theme', val)
    localStorage.setItem('theme', val)
  }, { immediate: true })

  return { mode, toggle, isDark }
})
