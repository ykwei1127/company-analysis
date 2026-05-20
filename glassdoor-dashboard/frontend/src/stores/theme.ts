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
    // Element Plus dark mode CSS requires the 'dark' class on <html>
    if (val === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    localStorage.setItem('theme', val)
  }, { immediate: true })

  return { mode, toggle, isDark }
})
