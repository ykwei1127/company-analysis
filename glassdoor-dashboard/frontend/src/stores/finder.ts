import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useFinderStore = defineStore('finder', () => {
  // State
  const isRunning = ref(false)
  const currentTask = ref<'explore' | 'match' | 'scan' | null>(null)
  const logs = ref<string[]>([])
  const startTime = ref<number | null>(null)

  // Getters
  const statusTitle = computed(() => {
    if (!currentTask.value) return ''
    const titles: Record<string, string> = {
      explore: 'Exploring Baseline',
      match: 'Matching Companies',
      scan: 'Scanning Countries'
    }
    return `Running: ${titles[currentTask.value]}`
  })

  const statusText = computed(() => {
    if (!currentTask.value) return ''
    const texts: Record<string, string> = {
      explore: 'Creating ASUS baseline location list...',
      match: 'Matching companies against baseline...',
      scan: 'Scanning all countries for reviews...'
    }
    return texts[currentTask.value]
  })

  const elapsedTime = computed(() => {
    if (!startTime.value) return ''
    const elapsed = Math.floor((Date.now() - startTime.value) / 1000)
    const mins = Math.floor(elapsed / 60)
    const secs = elapsed % 60
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
  })

  // Actions
  function start(task: 'explore' | 'match' | 'scan') {
    isRunning.value = true
    currentTask.value = task
    startTime.value = Date.now()
    logs.value = []
  }

  function stop() {
    isRunning.value = false
    currentTask.value = null
    startTime.value = null
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
    statusTitle,
    statusText,
    elapsedTime,
    start,
    stop,
    addLog,
    setLogs
  }
})
