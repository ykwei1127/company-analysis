import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getRuns, deleteRun } from '../api'

export const useDashboardStore = defineStore('dashboard', () => {
  const runs = ref<{ id: string; label: string }[]>([])
  const selectedRunId = ref<string>('')

  async function fetchRuns() {
    try {
      const { data } = await getRuns()
      runs.value = data
      if (data.length > 0 && !selectedRunId.value) {
        selectedRunId.value = data[0].id
      }
    } catch (e) {
      console.error('Failed to fetch runs', e)
    }
  }

  function selectRun(id: string) {
    selectedRunId.value = id || ''
  }

  async function removeRun(id: string) {
    await deleteRun(id)
    if (selectedRunId.value === id) {
      selectedRunId.value = ''
    }
    await fetchRuns()
  }

  return { runs, selectedRunId, fetchRuns, selectRun, removeRun }
})
