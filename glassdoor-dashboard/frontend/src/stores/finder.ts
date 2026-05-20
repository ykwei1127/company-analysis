import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useFinderStore = defineStore('finder', () => {
  // State
  const isRunning = ref(false)
  const currentTask = ref<'office' | 'country' | 'scan' | null>(null)
  const logs = ref<string[]>([])
  const startTime = ref<number | null>(null)
  const elapsedTime = ref('')  // Now a ref that updates via setInterval
  let elapsedTimer: number | null = null

  // Update elapsed time every second
  function updateElapsed() {
    if (!startTime.value) {
      elapsedTime.value = ''
      return
    }
    const elapsed = Math.floor((Date.now() - startTime.value) / 1000)
    const mins = Math.floor(elapsed / 60)
    const secs = elapsed % 60
    elapsedTime.value = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
  }

  // Getters
  const statusTitle = computed(() => {
    if (!currentTask.value) return ''
    const titles: Record<string, string> = {
      office: 'Building Office Lists',
      country: 'Building Country Lists',
      scan: 'Scanning Countries'
    }
    return `Running: ${titles[currentTask.value]}`
  })

  const statusText = computed(() => {
    if (!currentTask.value) return ''
    const texts: Record<string, string> = {
      office: 'Finding office location review URLs...',
      country: 'Building country-level review URLs...',
      scan: 'Scanning all countries for reviews...'
    }
    return texts[currentTask.value]
  })

  // Actions
  function start(task: 'office' | 'country' | 'scan') {
    isRunning.value = true
    currentTask.value = task
    startTime.value = Date.now()
    logs.value = []
    elapsedTime.value = '0s'
    // Start timer to update elapsed time every second
    if (elapsedTimer) clearInterval(elapsedTimer)
    elapsedTimer = window.setInterval(updateElapsed, 1000)
  }

  function stop() {
    isRunning.value = false
    currentTask.value = null
    startTime.value = null
    elapsedTime.value = ''
    // Stop timer
    if (elapsedTimer) {
      clearInterval(elapsedTimer)
      elapsedTimer = null
    }
  }

  function addLog(line: string) {
    logs.value.push(line)
    // Keep last 500 lines
    if (logs.value.length > 500) {
      logs.value = logs.value.slice(-500)
    }
  }

  function setLogs(newLogs: string[]) {
    logs.value = newLogs
  }

  return {
    isRunning,
    currentTask,
    logs,
    startTime,
    elapsedTime,
    statusTitle,
    statusText,
    updateElapsed,
    start,
    stop,
    addLog,
    setLogs
  }
})
