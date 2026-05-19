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
          <el-button v-if="!open" size="small" type="primary" plain @click="handleLaunchChrome(Number(port))" :loading="launchingPort === Number(port)">Launch</el-button>
        </div>
        <el-button size="small" @click="refreshChromeStatus" :loading="checkingChrome">Refresh</el-button>
        <el-button size="small" type="primary" @click="handleLaunchAll" :loading="launchingAll" :disabled="offlinePorts.length === 0">Launch All</el-button>
        <el-button size="small" type="danger" plain @click="handleCloseAll" :loading="closingAll" :disabled="connectedPorts.length === 0">Close All</el-button>
      </div>

      <!-- Login check -->
      <div class="login-status" v-if="loginResults.length > 0">
        <el-tag v-for="r in loginResults" :key="r.port" :type="r.logged_in ? 'success' : 'warning'" size="small" style="margin-right: 8px">
          {{ r.message }}
        </el-tag>
      </div>
    </el-card>

    <!-- Scraper Controls -->
    <el-card style="margin-bottom: 16px">
      <template #header><span>Run Scraper</span></template>
      <div class="scraper-controls">
        <div class="control-group">
          <label>Ports:</label>
          <el-checkbox-group v-model="selectedPorts" size="small">
            <el-checkbox v-for="port in ALL_PORTS" :key="port" :label="port" :value="port" :disabled="!chromeStatus[port]">
              {{ port }}
            </el-checkbox>
          </el-checkbox-group>
        </div>
        <div class="control-group">
          <label>Data Source:</label>
          <el-select v-model="mode" size="small" style="width: 160px">
            <el-option label="Company Reviews" value="matched" />
            <el-option label="ASUS Baseline Only" value="baseline" />
          </el-select>
        </div>
        <div class="control-group">
          <label>Match Mode:</label>
          <el-select v-model="sourceMode" size="small" style="width: 140px" :disabled="mode !== 'matched'">
            <el-option label="All" value="all" />
            <el-option label="Country" value="country" />
            <el-option label="City" value="city" />
            <el-option label="Discovery" value="scan" />
          </el-select>
          <el-tooltip v-if="mode === 'baseline'" content="ASUS Baseline has no Match Mode filter">
            <el-icon style="margin-left: 4px; color: var(--el-text-color-secondary);"><info-filled /></el-icon>
          </el-tooltip>
        </div>
        <div class="control-group" v-if="mode === 'matched'" style="flex-wrap: wrap;">
          <label>Companies:</label>
          <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
            <el-select-v2
              v-model="selectedCompanies"
              :options="companyOptions"
              placeholder="All companies (click to select)"
              size="small"
              style="width: 280px"
              multiple
              collapse-tags
              :max-collapse-tags="2"
            />
            <el-tooltip content="Select specific companies to scrape. Empty = all companies.">
              <el-icon style="color: var(--el-text-color-secondary);"><info-filled /></el-icon>
            </el-tooltip>
            <el-button size="small" text @click="loadAvailableCompanies" :loading="loadingCompanies">
              <el-icon><refresh /></el-icon>
            </el-button>
            <el-button v-if="selectedCompanies.length > 0" size="small" text @click="selectedCompanies = []">
              Clear
            </el-button>
          </div>
        </div>
        <el-button type="primary" size="small" @click="handleStart" :loading="starting" :disabled="isRunning || selectedPorts.length === 0">Start</el-button>
        <el-button type="danger" size="small" @click="handleStop" :disabled="!isRunning">Stop</el-button>
        <el-button size="small" @click="checkLoginStatus" :disabled="selectedPorts.length === 0">Check Login</el-button>
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

      <!-- Blocked alert -->
      <el-alert v-if="blockedPorts.length > 0" type="error" :closable="false" show-icon style="margin-bottom: 12px">
        <template #title>
          Port {{ blockedPorts.join(', ') }} 被 Cloudflare 攔截！請到 Chrome 視窗手動通過驗證，通過後爬蟲會自動繼續。
        </template>
      </el-alert>

      <!-- Progress bar -->
      <el-progress v-if="progressPercent > 0" :percentage="progressPercent" :status="progressStatus" :stroke-width="8" style="margin-bottom: 8px" />
      <div v-if="isRunning && progressPercent > 0" class="time-info">
        <span>Elapsed: {{ elapsedStr }}</span>
        <span v-if="etaStr">ETA: {{ etaStr }}</span>
      </div>

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
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { InfoFilled, Refresh } from '@element-plus/icons-vue'
import { getScraperStatus, startScraper, stopScraper, checkLogin, getChromeStatus, launchChrome, closeAllChrome, getCompanies } from '../api'

const ALL_PORTS = [9222, 9223, 9224]
const selectedPorts = ref<number[]>([9222])
const mode = ref('matched')
const sourceMode = ref('all')  // 'all', 'country', 'city', 'scan'
const availableCompanies = ref<{name: string, file: string, mode: string}[]>([])
const selectedCompanies = ref<string[]>([])  // Empty means all companies
const loadingCompanies = ref(false)
const isRunning = ref(false)
const starting = ref(false)
const logs = ref<string[]>([])
const chromeStatus = ref<Record<number, boolean>>({})
const checkingChrome = ref(false)
const launchingPort = ref<number | null>(null)
const launchingAll = ref(false)
const offlinePorts = computed(() => ALL_PORTS.filter(p => !chromeStatus.value[p]))
const connectedPorts = computed(() => ALL_PORTS.filter(p => chromeStatus.value[p]))
const closingAll = ref(false)
const loginResults = ref<{ port: number; logged_in: boolean; message: string }[]>([])
const logContainer = ref<HTMLElement | null>(null)
const autoScroll = ref(true)
let pollTimer: ReturnType<typeof setInterval> | null = null
const startTime = ref<number>(0)
const elapsedSeconds = ref(0)
let elapsedTimer: ReturnType<typeof setInterval> | null = null

const visibleLogLines = computed(() => logs.value.slice(-200))

const filteredCompanies = computed(() => {
  if (sourceMode.value === 'all') return availableCompanies.value
  return availableCompanies.value.filter(c => c.mode === sourceMode.value)
})

const companyOptions = computed(() => {
  return filteredCompanies.value.map(c => ({
    label: c.name,
    value: c.name
  }))
})

async function loadAvailableCompanies() {
  loadingCompanies.value = true
  try {
    const { data } = await getCompanies()
    availableCompanies.value = data.companies || []
    // Don't reset selectedCompanies - keep user's selection
  } catch (e) {
    console.error('Failed to load companies', e)
  }
  loadingCompanies.value = false
}

const progressInfo = computed(() => {
  for (let i = logs.value.length - 1; i >= 0; i--) {
    const m = logs.value[i].match(/\[PROGRESS\]\s*(\d+)\/(\d+)/)
    if (m) return { current: parseInt(m[1]), total: parseInt(m[2]) }
  }
  return { current: 0, total: 0 }
})

const progressPercent = computed(() => {
  const { current, total } = progressInfo.value
  return total > 0 ? Math.round((current / total) * 100) : 0
})

const progressStatus = computed(() => {
  if (progressPercent.value >= 100) return 'success' as const
  return '' as const
})

const elapsedStr = computed(() => formatDuration(elapsedSeconds.value))

const etaStr = computed(() => {
  const { current, total } = progressInfo.value
  if (current <= 0 || elapsedSeconds.value <= 0) return ''
  const rate = elapsedSeconds.value / current
  const remaining = Math.round(rate * (total - current))
  return formatDuration(remaining)
})

function formatDuration(sec: number): string {
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  if (h > 0) return `${h}h ${m}m ${s}s`
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
}

const blockedPorts = computed(() => {
  const ports = new Set<string>()
  // Check last 50 lines for active blocks
  const recent = logs.value.slice(-50)
  for (const line of recent) {
    const m = line.match(/\[BLOCKED\] Port (\S+) 被/)
    if (m) ports.add(m[1])
    const r = line.match(/\[BLOCKED\] Port (\S+) 已恢復/)
    if (r) ports.delete(r[1])
  }
  return Array.from(ports)
})

const logClass = (line: string) => {
  if (line.includes('[BLOCKED]')) return 'log-blocked'
  if (line.includes('[ERROR]') || line.includes('Error')) return 'log-error'
  if (line.includes('[WARN]') || line.includes('Warning')) return 'log-warn'
  if (line.includes('[PROGRESS]')) return 'log-progress'
  if (line.includes('[DONE]') || line.includes('completed')) return 'log-success'
  return ''
}

async function handleLaunchChrome(port: number) {
  launchingPort.value = port
  try {
    await launchChrome(port)
    await new Promise(r => setTimeout(r, 2000))
    await refreshChromeStatus()
    autoSelectConnected()
  } catch { /* ignore */ }
  launchingPort.value = null
}

async function handleLaunchAll() {
  launchingAll.value = true
  try {
    for (const port of offlinePorts.value) {
      await launchChrome(port)
    }
    await new Promise(r => setTimeout(r, 3000))
    await refreshChromeStatus()
    autoSelectConnected()
  } catch { /* ignore */ }
  launchingAll.value = false
}

async function handleCloseAll() {
  closingAll.value = true
  try {
    await closeAllChrome()
    await new Promise(r => setTimeout(r, 2000))
    await refreshChromeStatus()
    autoSelectConnected()
  } catch { /* ignore */ }
  closingAll.value = false
}

function autoSelectConnected() {
  selectedPorts.value = ALL_PORTS.filter(p => chromeStatus.value[p])
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
  if (selectedPorts.value.length === 0) return
  loginResults.value = []
  for (const port of selectedPorts.value) {
    try {
      const { data } = await checkLogin(port)
      loginResults.value.push({ port, logged_in: data.logged_in, message: data.message || data.error || `Port ${port}: Unknown` })
    } catch (e: any) {
      loginResults.value.push({ port, logged_in: false, message: `Port ${port}: ${e.message}` })
    }
  }
}

async function handleStart() {
  starting.value = true
  try {
    const portsStr = selectedPorts.value.join(',')
    const companiesStr = selectedCompanies.value.length > 0 ? selectedCompanies.value.join(',') : undefined
    const { data } = await startScraper(portsStr, mode.value, sourceMode.value, companiesStr)
    if (data.error) {
      logs.value = [data.error]
    } else {
      isRunning.value = true
      logs.value = []
      startTime.value = Date.now()
      elapsedSeconds.value = 0
      startElapsedTimer()
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
    stopElapsedTimer()
  } catch { /* ignore */ }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const { data } = await getScraperStatus()
      logs.value = data.logs
      isRunning.value = data.running
      if (!data.running) { stopPolling(); stopElapsedTimer() }
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

function startElapsedTimer() {
  stopElapsedTimer()
  elapsedTimer = setInterval(() => {
    elapsedSeconds.value = Math.round((Date.now() - startTime.value) / 1000)
  }, 1000)
}

function stopElapsedTimer() {
  if (elapsedTimer) { clearInterval(elapsedTimer); elapsedTimer = null }
}

// When sourceMode changes, clear selected companies that no longer match
watch(sourceMode, () => {
  if (sourceMode.value !== 'all') {
    const validNames = new Set(filteredCompanies.value.map(c => c.name))
    selectedCompanies.value = selectedCompanies.value.filter(n => validNames.has(n))
  }
})

onMounted(async () => {
  await refreshChromeStatus()
  // Load available companies
  await loadAvailableCompanies()
  // Auto-select connected ports
  selectedPorts.value = ALL_PORTS.filter(p => chromeStatus.value[p])
  // Check if scraper already running
  getScraperStatus().then(({ data }) => {
    if (data.running) {
      isRunning.value = true
      logs.value = data.logs
      // Restore start time from backend
      startTime.value = data.start_time ? data.start_time * 1000 : Date.now()
      elapsedSeconds.value = Math.round((Date.now() - startTime.value) / 1000)
      startElapsedTimer()
      startPolling()
    }
  }).catch(() => {})
})

onUnmounted(() => { stopPolling(); stopElapsedTimer() })
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

.time-info { display: flex; gap: 24px; font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; }

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
.log-blocked { color: #f56c6c; font-weight: 600; background: rgba(245,108,108,0.1); padding: 2px 4px; border-radius: 3px; }
</style>
