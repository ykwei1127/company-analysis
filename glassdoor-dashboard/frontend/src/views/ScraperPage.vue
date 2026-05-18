<template>
  <div>
    <h3 class="page-title">Scraper Control</h3>

    <!-- Chrome Status -->
    <el-card style="margin-bottom: 16px">
      <template #header><span>Chrome Debug Instances</span></template>
      <div class="chrome-status">
        <div v-for="(open, port) in chromeStatus" :key="port" class="port-status">
          <span class="port-label">Port {{ port }}</span>
          <el-tag :type="open ? 'success' : 'danger'" size="small">{{ open ? 'Connected' : 'Offline' }}</el-tag>
        </div>
        <el-button size="small" @click="refreshChromeStatus" :loading="checkingChrome">Refresh</el-button>
      </div>

      <!-- Login check -->
      <div class="login-status" v-if="loginResult">
        <el-tag :type="loginResult.logged_in ? 'success' : 'warning'" size="small">
          {{ loginResult.message || loginResult.error || 'Unknown' }}
        </el-tag>
      </div>
    </el-card>

    <!-- Scraper Controls -->
    <el-card style="margin-bottom: 16px">
      <template #header><span>Run Scraper</span></template>
      <div class="scraper-controls">
        <div class="control-group">
          <label>Ports:</label>
          <el-input v-model="ports" size="small" style="width: 160px" placeholder="9222,9223" />
        </div>
        <div class="control-group">
          <label>Mode:</label>
          <el-select v-model="mode" size="small" style="width: 140px">
            <el-option label="Matched" value="matched" />
            <el-option label="Baseline" value="baseline" />
          </el-select>
        </div>
        <el-button type="primary" size="small" @click="handleStart" :loading="starting" :disabled="isRunning">Start</el-button>
        <el-button type="danger" size="small" @click="handleStop" :disabled="!isRunning">Stop</el-button>
        <el-button size="small" @click="checkLoginStatus">Check Login</el-button>
      </div>
    </el-card>

    <!-- Progress -->
    <el-card v-if="isRunning || logs.length > 0">
      <template #header>
        <div class="card-header">
          <span>Output</span>
          <el-tag v-if="isRunning" type="warning" size="small" effect="dark">Running</el-tag>
          <el-tag v-else-if="logs.length > 0" type="info" size="small">Done</el-tag>
        </div>
      </template>

      <!-- Progress bar -->
      <el-progress v-if="progressPercent > 0" :percentage="progressPercent" :status="progressStatus" :stroke-width="8" style="margin-bottom: 12px" />

      <!-- Log output -->
      <div class="log-container" ref="logContainer">
        <div v-for="(line, i) in visibleLogLines" :key="i" class="log-line" :class="logClass(line)">
          {{ line }}
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { getScraperStatus, startScraper, stopScraper, checkLogin, getChromeStatus } from '../api'

const ports = ref('9222')
const mode = ref('matched')
const isRunning = ref(false)
const starting = ref(false)
const logs = ref<string[]>([])
const chromeStatus = ref<Record<number, boolean>>({})
const checkingChrome = ref(false)
const loginResult = ref<{ logged_in: boolean; message?: string; error?: string } | null>(null)
const logContainer = ref<HTMLElement | null>(null)
const autoScroll = ref(true)
let pollTimer: ReturnType<typeof setInterval> | null = null

const visibleLogLines = computed(() => logs.value.slice(-200))

const progressPercent = computed(() => {
  for (let i = logs.value.length - 1; i >= 0; i--) {
    const m = logs.value[i].match(/\[PROGRESS\]\s*(\d+)\/(\d+)/)
    if (m) return Math.round((parseInt(m[1]) / parseInt(m[2])) * 100)
  }
  return 0
})

const progressStatus = computed(() => {
  if (progressPercent.value >= 100) return 'success' as const
  return '' as const
})

const logClass = (line: string) => {
  if (line.includes('[ERROR]') || line.includes('Error')) return 'log-error'
  if (line.includes('[WARN]') || line.includes('Warning')) return 'log-warn'
  if (line.includes('[PROGRESS]')) return 'log-progress'
  if (line.includes('[DONE]') || line.includes('completed')) return 'log-success'
  return ''
}

async function refreshChromeStatus() {
  checkingChrome.value = true
  try {
    const { data } = await getChromeStatus()
    chromeStatus.value = data
  } catch { /* ignore */ }
  checkingChrome.value = false
}

async function checkLoginStatus() {
  const portNum = parseInt(ports.value.split(',')[0])
  try {
    const { data } = await checkLogin(portNum)
    loginResult.value = data
  } catch (e: any) {
    loginResult.value = { logged_in: false, error: e.message }
  }
}

async function handleStart() {
  starting.value = true
  try {
    const { data } = await startScraper(ports.value, mode.value)
    if (data.error) {
      logs.value = [data.error]
    } else {
      isRunning.value = true
      logs.value = []
      startPolling()
    }
  } catch (e: any) {
    logs.value = [`Failed to start: ${e.message}`]
  }
  starting.value = false
}

async function handleStop() {
  try {
    await stopScraper()
    isRunning.value = false
    stopPolling()
  } catch { /* ignore */ }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const { data } = await getScraperStatus()
      logs.value = data.logs
      isRunning.value = data.running
      if (!data.running) stopPolling()
      if (autoScroll.value) {
        nextTick(() => {
          if (logContainer.value) logContainer.value.scrollTop = logContainer.value.scrollHeight
        })
      }
    } catch { /* ignore */ }
  }, 2000)
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

onMounted(() => {
  refreshChromeStatus()
  // Check if scraper already running
  getScraperStatus().then(({ data }) => {
    if (data.running) {
      isRunning.value = true
      logs.value = data.logs
      startPolling()
    }
  }).catch(() => {})
})

onUnmounted(stopPolling)
</script>

<style scoped>
.page-title { font-size: 22px; font-weight: 600; color: var(--text-primary); margin: 0 0 14px 0; }
.card-header { display: flex; align-items: center; justify-content: space-between; }

.chrome-status { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.port-status { display: flex; align-items: center; gap: 6px; }
.port-label { font-size: 13px; color: var(--text-secondary); }
.login-status { margin-top: 12px; }

.scraper-controls { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.control-group { display: flex; align-items: center; gap: 6px; }
.control-group label { font-size: 13px; color: var(--text-secondary); white-space: nowrap; }

.log-container {
  max-height: 400px;
  overflow-y: auto;
  background: #0a0a0a;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 10px 14px;
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.6;
}
.log-line { color: #aaa; }
.log-error { color: #f56c6c; }
.log-warn { color: #e6a23c; }
.log-progress { color: #67c23a; }
.log-success { color: #67c23a; font-weight: 600; }
</style>
