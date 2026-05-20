<template>
  <div>
    <h1 class="page-title">Settings & Companies</h1>

    <!-- Demo mode banner -->
    <el-alert
      v-if="STATIC_MODE"
      title="Demo Mode — Read Only"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 16px;"
    >
      This is a preview of the Settings interface. Configuration changes require the local backend to be running.
    </el-alert>

    <!-- Chrome Required Banner (only show when not running) -->
    <el-alert
      v-if="!chromeConnected && !finderStore.isRunning"
      title="Chrome Not Connected"
      type="error"
      :closable="false"
      style="margin-bottom: 16px;"
    >
      <div style="font-size: 13px; line-height: 1.6;">
        Please start Chrome with remote debugging port first.<br>
        Run: <code>啟動Chrome.bat</code> (port 9222, 9223, 9224)<br>
        Or use <router-link to="/scraper" style="color: var(--el-color-primary);">Scraper page</router-link> to launch Chrome.
        <div style="margin-top: 8px;">
          <el-button size="small" type="primary" @click="checkChromeStatus">Check Chrome Status</el-button>
          <el-button size="small" @click="$router.push('/scraper')">Go to Scraper →</el-button>
        </div>
      </div>
    </el-alert>

    <el-tabs v-model="activeTab">
      <!-- Tab 1: URL Lists -->
      <el-tab-pane label="URL Lists" name="companies">
        <!-- Company Management -->
        <div class="section">
          <div class="section-header">
            <h3 class="section-title">Companies</h3>
            <div style="display: flex; gap: 8px;">
              <el-button size="small" text @click="selectedMatchCompanies = availableMatchCompanies.map(c => c.name)">
                Select All
              </el-button>
              <el-button size="small" text @click="selectedMatchCompanies = []">
                Clear All
              </el-button>
            </div>
          </div>
          <el-checkbox-group v-model="selectedMatchCompanies" size="small" style="display: flex; flex-wrap: wrap; gap: 8px;" :disabled="STATIC_MODE || finderStore.isRunning">
            <el-checkbox
              v-for="c in availableMatchCompanies"
              :key="c.name"
              :label="c.name"
              :value="c.name"
              style="margin: 0;"
              border
            >
              {{ c.name }}
            </el-checkbox>
          </el-checkbox-group>
          <div style="margin-top: 8px; display: flex; gap: 8px; align-items: center;">
            <el-input
              v-model="newCompanyName"
              placeholder="Add new company..."
              size="small"
              style="width: 180px"
              :disabled="STATIC_MODE"
              @keyup.enter="handleAddToMatch"
            />
            <el-button size="small" type="primary" @click="handleAddToMatch" :disabled="STATIC_MODE || !newCompanyName.trim()">Add</el-button>
            <el-popconfirm title="Remove selected companies?" @confirm="handleRemoveSelected">
              <template #reference>
                <el-button size="small" type="danger" plain :disabled="STATIC_MODE || selectedMatchCompanies.length === 0">
                  Remove Selected
                </el-button>
              </template>
            </el-popconfirm>
          </div>
        </div>

        <el-divider />

        <!-- Build URL Lists -->
        <div class="section">
          <div class="section-header">
            <h3 class="section-title">Build URL Lists</h3>
            <el-button
              size="small"
              type="danger"
              plain
              @click="handleStopFinder"
              :disabled="STATIC_MODE || !finderRunning"
            >Stop</el-button>
          </div>
          <p style="font-size: 13px; color: var(--el-text-color-secondary); margin: 0 0 12px 0;">
            Build review URL lists for selected companies. Each type only needs to be run once; afterwards use <router-link to="/scraper">Scraper</router-link> to periodically collect reviews.
          </p>

          <div style="display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px;">
            <!-- Office Location -->
            <el-card shadow="hover" style="flex: 1; min-width: 200px;">
              <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <strong>Office Location</strong>
                  <el-tag size="small" type="info">office</el-tag>
                </div>
              </template>
              <p style="font-size: 12px; color: var(--el-text-color-secondary); margin: 0 0 12px 0;">
                Uses Glassdoor office locations page to find city-level review URLs.
              </p>
              <el-button
                size="small"
                type="primary"
                @click="handleBuildOffice"
                :loading="finderRunning && currentTask === 'office'"
                :disabled="STATIC_MODE || finderRunning"
              >
                <el-icon><Refresh /></el-icon> Build Office List
              </el-button>
            </el-card>

            <!-- Country -->
            <el-card shadow="hover" style="flex: 1; min-width: 200px;">
              <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <strong>Country</strong>
                  <el-tag size="small" type="success">country</el-tag>
                </div>
              </template>
              <p style="font-size: 12px; color: var(--el-text-color-secondary); margin: 0 0 12px 0;">
                Uses country-level IN codes to build review URLs. Fast and consistent.
              </p>
              <el-alert
                v-if="!baselineExists"
                type="warning"
                :closable="false"
                style="margin-bottom: 10px; padding: 6px 10px; font-size: 12px;"
              >
                <template #title>Requires ASUS Office list first</template>
                Run <strong>Build Office List</strong> (ASUS must be included) before building Country lists.
              </el-alert>
              <el-tooltip
                :disabled="baselineExists"
                content="Please build ASUS Office List first (data/asus_office.json)"
                placement="top"
              >
                <el-button
                  size="small"
                  type="primary"
                  @click="handleBuildCountry"
                  :loading="finderRunning && currentTask === 'country'"
                  :disabled="STATIC_MODE || finderRunning || !baselineExists"
                >
                  <el-icon><Refresh /></el-icon> Build Country List
                </el-button>
              </el-tooltip>
            </el-card>

            <!-- City Match -->
            <el-card shadow="hover" style="flex: 1; min-width: 200px;">
              <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <strong>City Match</strong>
                  <el-tag size="small" type="danger">city</el-tag>
                </div>
              </template>
              <p style="font-size: 12px; color: var(--el-text-color-secondary); margin: 0 0 12px 0;">
                Uses ASUS office locations as baseline, finds matching city-level URLs at other companies.
              </p>
              <el-alert
                v-if="!baselineExists"
                type="warning"
                :closable="false"
                style="margin-bottom: 10px; padding: 6px 10px; font-size: 12px;"
              >
                <template #title>Requires ASUS Office list first</template>
                Run <strong>Build Office List</strong> (ASUS must be included) before building City Match lists.
              </el-alert>
              <el-tooltip
                :disabled="baselineExists"
                content="Please build ASUS Office List first (data/asus_office.json)"
                placement="top"
              >
                <el-button
                  size="small"
                  type="danger"
                  plain
                  @click="handleBuildCity"
                  :loading="finderRunning && currentTask === 'city'"
                  :disabled="STATIC_MODE || finderRunning || !baselineExists"
                >
                  <el-icon><Refresh /></el-icon> Build City List
                </el-button>
              </el-tooltip>
            </el-card>

            <!-- World Scan -->
            <el-card shadow="hover" style="flex: 1; min-width: 200px;">
              <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <strong>World Scan</strong>
                  <el-tag size="small" type="warning">scan</el-tag>
                </div>
              </template>
              <p style="font-size: 12px; color: var(--el-text-color-secondary); margin: 0 0 12px 0;">
                Scans {{ totalScanCountries }} countries worldwide to discover where reviews exist.
              </p>
              <el-button
                size="small"
                type="warning"
                plain
                @click="handleScan"
                :loading="finderRunning && currentTask === 'scan'"
                :disabled="STATIC_MODE || finderRunning"
              >
                <el-icon><Search /></el-icon> Build Scan List
              </el-button>
            </el-card>
          </div>

          <el-collapse style="margin-bottom: 12px;">
            <el-collapse-item title="View countries to scan (by region)" name="1">
              <div v-for="group in scanCountryGroups" :key="group.region" style="margin-bottom: 16px;">
                <div style="font-weight: 600; font-size: 13px; color: var(--el-text-color-primary); margin-bottom: 8px; border-bottom: 1px solid var(--el-border-color-light); padding-bottom: 4px;">
                  {{ group.region }} ({{ group.countries.length }})
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                  <el-tag v-for="country in group.countries" :key="country" size="small" type="info">{{ country }}</el-tag>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>

        <el-divider />

        <!-- URL List Files -->
        <div class="section">
          <div class="section-header">
            <h3 class="section-title">URL List Files</h3>
            <el-button size="small" @click="loadCompanies" :loading="loadingCompanies">Refresh</el-button>
          </div>
          <el-table :data="companies" size="small" stripe>
            <el-table-column prop="name" label="Company" />
            <el-table-column prop="mode" label="Type" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="row.mode === 'country' ? 'success' : row.mode === 'scan' ? 'warning' : row.mode === 'city' ? 'danger' : 'info'">{{ row.mode }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="entries" label="Entries" width="80" />
            <el-table-column prop="file" label="File" width="260" />
            <el-table-column label="Action" width="90">
              <template #default="{ row }">
                <el-popconfirm title="Remove this file?" @confirm="handleRemove(row.file)">
                  <template #reference>
                    <el-button type="danger" size="small" plain :disabled="STATIC_MODE">Remove</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- Tab 2: View URL Lists -->
      <el-tab-pane label="View URL Lists" name="baseline">
        <div class="section">
          <div class="section-header">
            <h3 class="section-title">View URL List Entries</h3>
            <div style="display: flex; gap: 8px; align-items: center;">
              <el-select v-model="viewListFile" size="small" style="width: 250px" placeholder="Select a URL list file" @change="loadUrlListEntries">
                <el-option
                  v-for="c in companies"
                  :key="c.file"
                  :label="`${c.name} (${c.mode})`"
                  :value="c.file"
                />
              </el-select>
              <el-tag size="small">{{ viewListEntries.length }} entries</el-tag>
            </div>
          </div>
          <el-table :data="viewListEntries" size="small" stripe max-height="500" v-if="viewListEntries.length > 0">
            <el-table-column label="Location" width="180">
              <template #default="{ row }">
                <span>{{ row.location || row.baseline_location || row.country || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="country" label="Country" width="120" />
            <el-table-column prop="status" label="Status" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'found' ? 'success' : 'danger'" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="url" label="URL">
              <template #default="{ row }">
                <a v-if="row.url" :href="row.url" target="_blank" class="url-link">{{ row.url }}</a>
                <span v-else class="no-url">—</span>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="Select a URL list file to view entries" />
        </div>
      </el-tab-pane>

      <!-- Tab 3: Config -->
      <el-tab-pane label="Scraper Config" name="config">
        <div class="section">
          <el-form label-width="200px" size="small" v-if="configLoaded">
            <el-form-item label="Include Baseline (ASUS)">
              <el-switch v-model="config.include_baseline" :disabled="STATIC_MODE" @change="saveConfig" />
            </el-form-item>
            <el-form-item label="Parallel Ports">
              <el-input v-model="portsStr" placeholder="9222,9223,9224" style="width: 220px" :disabled="STATIC_MODE" @blur="saveConfig" />
            </el-form-item>
            <el-form-item label="Mode">
              <el-select v-model="config.scraper_config.mode" :disabled="STATIC_MODE" @change="saveConfig" style="width: 140px">
                <el-option value="manual" label="Manual" />
                <el-option value="auto" label="Auto" />
              </el-select>
            </el-form-item>
            <el-form-item label="Delay Between Requests (s)">
              <el-input-number v-model="config.scraper_config.delay_between_requests" :min="0.5" :max="30" :step="0.5" :disabled="STATIC_MODE" @change="saveConfig" />
            </el-form-item>
            <el-form-item label="Page Wait Time (s)">
              <el-input-number v-model="config.scraper_config.wait_time" :min="1" :max="30" :step="1" :disabled="STATIC_MODE" @change="saveConfig" />
            </el-form-item>
          </el-form>
          <el-tag v-if="configSaved" type="success" size="small">Saved</el-tag>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { Loading, Refresh, Search, InfoFilled } from '@element-plus/icons-vue'
import { useFinderStore } from '../stores/finder'
import { 
  getCompanies,
  removeCompany,
  runFinderOffice,
  runFinderCountry,
  runFinderCity,
  runFinderScan, 
  getFinderStatus, 
  stopFinder, 
  getConfig, 
  updateConfig, 
  getCompaniesToMatch, 
  addCompanyToMatch, 
  removeCompanyToMatch, 
  getBaseline 
} from '../api'

const STATIC_MODE = import.meta.env.VITE_STATIC_MODE === 'true'

const activeTab = ref('companies')

// Countries for Scan mode grouped by region (matching COUNTRY_IN_CODES in company_finder.py)
const scanCountryGroups = ref([
  {
    region: 'North America',
    countries: ['United States', 'Canada', 'Mexico']
  },
  {
    region: 'Europe',
    countries: ['United Kingdom', 'France', 'Germany', 'Spain', 'Italy', 'Netherlands', 'Hungary', 'Poland',
      'Czech Republic', 'Turkey', 'Sweden', 'Switzerland', 'Austria', 'Belgium', 'Denmark', 'Finland',
      'Ireland', 'Norway', 'Portugal', 'Romania', 'Greece', 'Ukraine', 'Russia']
  },
  {
    region: 'Asia Pacific',
    countries: ['India', 'Japan', 'South Korea', 'China', 'Taiwan', 'Singapore', 'Malaysia', 'Thailand',
      'Indonesia', 'Philippines', 'Vietnam', 'Australia', 'New Zealand', 'Hong Kong']
  },
  {
    region: 'Middle East',
    countries: ['United Arab Emirates', 'Israel', 'Saudi Arabia']
  },
  {
    region: 'South America',
    countries: ['Brazil', 'Chile', 'Argentina', 'Colombia', 'Peru']
  },
  {
    region: 'Africa',
    countries: ['South Africa', 'Nigeria', 'Egypt']
  },
])

const totalScanCountries = computed(() =>
  scanCountryGroups.value.reduce((sum, g) => sum + g.countries.length, 0)
)

// ─── Config ─────────────────────────────────────────────
const configLoaded = ref(false)
const configSaved = ref(false)
const config = ref({
  include_baseline: true,
  parallel_ports: [9222, 9223, 9224],
  scraper_config: { mode: 'manual', wait_time: 5, delay_between_requests: 3 },
  output_config: {},
})
const portsStr = ref('9222,9223,9224')

async function loadConfig() {
  try {
    const { data } = await getConfig()
    config.value = data
    portsStr.value = (data.parallel_ports || []).join(',')
    configLoaded.value = true
  } catch { /* ignore */ }
}

async function saveConfig() {
  config.value.parallel_ports = portsStr.value.split(',').map(p => parseInt(p.trim())).filter(p => !isNaN(p))
  await updateConfig(config.value)
  configSaved.value = true
  setTimeout(() => { configSaved.value = false }, 2000)
}

// ─── Companies ──────────────────────────────────────────
const companies = ref<any[]>([])
const loadingCompanies = ref(false)

async function loadCompanies() {
  loadingCompanies.value = true
  try {
    const { data } = await getCompanies()
    companies.value = data.companies
  } catch { /* ignore */ }
  loadingCompanies.value = false
}

async function handleRemove(filename: string) {
  await removeCompany(filename)
  await loadCompanies()
}

// ─── Companies to Match ─────────────────────────────────
const availableMatchCompanies = ref<{name: string}[]>([])
// 從 localStorage 初始化選中的公司
const savedCompanies = localStorage.getItem('selectedMatchCompanies')
const selectedMatchCompanies = ref<string[]>(savedCompanies ? JSON.parse(savedCompanies) : [])

// 監聽變化並保存到 localStorage
watch(selectedMatchCompanies, (newVal) => {
  localStorage.setItem('selectedMatchCompanies', JSON.stringify(newVal))
}, { deep: true })
const newCompanyName = ref('')

async function loadCompaniesToMatch() {
  try {
    const { data } = await getCompaniesToMatch()
    // API 回傳可能是字串或 {name: string} 物件
    availableMatchCompanies.value = data.companies.map((c: any) => ({ 
      name: typeof c === 'string' ? c : c.name 
    }))
  } catch { /* ignore */ }
}

async function handleAddToMatch() {
  const name = newCompanyName.value.trim()
  if (!name) return
  await addCompanyToMatch(name)
  newCompanyName.value = ''
  await loadCompaniesToMatch()
  // 新加入的公司自動選中
  if (!selectedMatchCompanies.value.includes(name)) {
    selectedMatchCompanies.value.push(name)
  }
}

async function handleRemoveSelected() {
  // 批量移除選中的公司
  for (const name of selectedMatchCompanies.value) {
    await removeCompanyToMatch(name)
  }
  selectedMatchCompanies.value = []
  await loadCompaniesToMatch()
}

// ─── Global Finder Store ─────────────────────────────────
const finderStore = useFinderStore()

const logContainerRef = ref<HTMLElement | null>(null)
const baselineExists = ref(false)

// ─── View URL List entries ──────────────────────────────
const viewListFile = ref('')
const viewListEntries = ref<any[]>([])

async function loadUrlListEntries() {
  if (!viewListFile.value) {
    viewListEntries.value = []
    return
  }
  try {
    const { data } = await getBaseline(viewListFile.value)
    viewListEntries.value = data.locations || []
  } catch {
    viewListEntries.value = []
  }
}

// ─── Global Status ─────────────────────────────────────
const chromeConnected = ref(true)  // 預設 true，檢查後更新

// 使用 computed 綁定到 store，這樣可以在 template 直接使用
const finderRunning = computed(() => finderStore.isRunning)
const currentTask = computed(() => finderStore.currentTask)
const finderLogs = computed(() => finderStore.logs)

async function checkChromeStatus() {
  try {
    // 簡單檢查 port 9222 是否可連接
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 2000)
    
    await fetch('http://127.0.0.1:9222/json', { 
      signal: controller.signal,
      mode: 'no-cors'
    })
    clearTimeout(timeoutId)
    chromeConnected.value = true
  } catch {
    chromeConnected.value = false
  }
}

async function handleStopFinder() {
  try {
    await stopFinder()
    finderStore.stop()
  } catch (e) {
    console.error('Failed to stop finder', e)
  }
}

// Check if baseline file exists
async function checkBaseline() {
  // 同時檢查 Chrome
  await checkChromeStatus()
  try {
    const { data } = await getBaseline()
    baselineExists.value = data && data.locations && data.locations.length > 0
  } catch {
    baselineExists.value = false
  }
}

// Auto-scroll log to bottom
watch(finderLogs, () => {
  nextTick(() => {
    if (logContainerRef.value) {
      logContainerRef.value.scrollTop = logContainerRef.value.scrollHeight
    }
  })
}, { deep: true })
let finderPoll: ReturnType<typeof setInterval> | null = null

async function handleBuildOffice() {
  finderStore.start('office')
  startFinderPolling()
  const companiesToRun = selectedMatchCompanies.value.length > 0
    ? selectedMatchCompanies.value
    : availableMatchCompanies.value.map(c => c.name)
  await runFinderOffice(companiesToRun)
}

async function handleBuildCountry() {
  finderStore.start('country')
  startFinderPolling()
  const companiesToRun = selectedMatchCompanies.value.length > 0
    ? selectedMatchCompanies.value
    : availableMatchCompanies.value.map(c => c.name)
  await runFinderCountry(companiesToRun)
}

async function handleBuildCity() {
  finderStore.start('city')
  startFinderPolling()
  const companiesToRun = selectedMatchCompanies.value.length > 0
    ? selectedMatchCompanies.value
    : availableMatchCompanies.value.map(c => c.name)
  await runFinderCity(companiesToRun)
}

async function handleScan() {
  finderStore.start('scan')
  startFinderPolling()
  const companiesToRun = selectedMatchCompanies.value.length > 0
    ? selectedMatchCompanies.value
    : availableMatchCompanies.value.map(c => c.name)
  await runFinderScan(companiesToRun)
}

function startFinderPolling() {
  stopFinderPolling()
  finderPoll = setInterval(async function pollFinderStatus() {
    try {
      const { data } = await getFinderStatus()
      // Check for completion BEFORE updating state
      const wasRunning = finderStore.isRunning
      const isRunningNow = data.running
      
      // Update store state (which updates global status bar)
      if (data.running !== finderStore.isRunning) {
        finderStore.isRunning = data.running
      }
      if (data.logs) {
        finderStore.setLogs(data.logs)
      }
      // Detect transition from running to not running (task completed)
      if (wasRunning && !isRunningNow) {
        // Task completed - update final logs then stop
        if (data.logs) {
          finderStore.setLogs(data.logs)
        }
        finderStore.stop()
        loadCompanies()
        checkBaseline()  // Recheck baseline after task completes
        stopFinderPolling()
      }
    } catch (e) {
      console.error('Failed to poll status', e)
    }
  }, 2000)
}

function stopFinderPolling() {
  if (finderPoll) { clearInterval(finderPoll); finderPoll = null }
}

// ─── Lifecycle ──────────────────────────────────────────
onMounted(() => {
  loadConfig()
  loadCompanies()
  loadCompaniesToMatch()
  checkBaseline()
  // Resume polling if a task was already running (e.g. user navigated away and back)
  if (finderStore.isRunning) {
    startFinderPolling()
  }
})

onUnmounted(stopFinderPolling)
</script>

<style scoped>
.page-title { font-size: 22px; font-weight: 600; color: var(--text-primary); margin: 0 0 14px 0; }

.section { margin-bottom: 8px; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.section-title { font-size: 15px; font-weight: 600; margin: 0; color: var(--text-primary); }

.finder-info { margin-bottom: 12px; font-size: 13px; color: var(--text-secondary); }
.finder-info p { margin: 4px 0 8px 0; }
.company-tags { display: flex; flex-wrap: wrap; align-items: center; }
.add-company-row { display: flex; gap: 8px; align-items: center; margin-top: 4px; }

.log-container {
  max-height: 250px;
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

.url-link { color: var(--accent-blue-light); text-decoration: none; font-size: 12px; word-break: break-all; }
.url-link:hover { text-decoration: underline; }
.no-url { color: #666; }
</style>
