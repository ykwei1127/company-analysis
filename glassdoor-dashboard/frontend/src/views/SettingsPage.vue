<template>
  <div>
    <h1 class="page-title">Settings & Companies</h1>

    <el-tabs v-model="activeTab">
      <!-- Tab 1: Companies -->
      <el-tab-pane label="Companies" name="companies">
        <!-- Company Finder -->
        <div class="section">
          <div class="section-header">
            <h3 class="section-title">Company Finder</h3>
            <div>
              <el-button size="small" type="primary" @click="handleMatch" :loading="finderRunning" :disabled="finderRunning">Run Match</el-button>
              <el-button size="small" @click="handleExplore" :loading="finderRunning" :disabled="finderRunning">Run Explore</el-button>
              <el-button size="small" type="danger" plain @click="handleStopFinder" :disabled="!finderRunning">Stop</el-button>
            </div>
          </div>

          <div class="finder-info">
            <p><strong>Companies to Match:</strong></p>
            <div class="company-tags">
              <el-tag
                v-for="c in companiesToMatch"
                :key="c.name"
                closable
                @close="handleRemoveFromMatch(c.name)"
                style="margin: 0 6px 6px 0"
              >{{ c.name }}</el-tag>
              <div class="add-company-row">
                <el-input
                  v-model="newCompanyName"
                  placeholder="Add company name..."
                  size="small"
                  style="width: 180px"
                  @keyup.enter="handleAddToMatch"
                />
                <el-button size="small" type="primary" @click="handleAddToMatch" :disabled="!newCompanyName.trim()">Add</el-button>
              </div>
            </div>
          </div>

          <div v-if="finderLogs.length > 0" class="log-container">
            <div v-for="(line, i) in finderLogs.slice(-100)" :key="i" class="log-line">{{ line }}</div>
          </div>
        </div>

        <el-divider />

        <!-- Matched Companies Table -->
        <div class="section">
          <div class="section-header">
            <h3 class="section-title">Matched Companies</h3>
            <el-button size="small" @click="loadCompanies" :loading="loadingCompanies">Refresh</el-button>
          </div>
          <el-table :data="companies" size="small" stripe>
            <el-table-column prop="name" label="Company" />
            <el-table-column prop="entries" label="Entries" width="80" />
            <el-table-column prop="file" label="File" width="240" />
            <el-table-column label="Action" width="90">
              <template #default="{ row }">
                <el-popconfirm title="Remove this company?" @confirm="handleRemove(row.file)">
                  <template #reference>
                    <el-button type="danger" size="small" plain>Remove</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- Tab 2: Baseline -->
      <el-tab-pane label="Baseline Locations" name="baseline">
        <div class="section">
          <div class="section-header">
            <h3 class="section-title">ASUS Baseline Locations</h3>
            <el-tag size="small">{{ baselineLocations.length }} locations</el-tag>
          </div>
          <el-table :data="baselineLocations" size="small" stripe max-height="500">
            <el-table-column prop="location" label="Location" width="180" />
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
        </div>
      </el-tab-pane>

      <!-- Tab 3: Config -->
      <el-tab-pane label="Scraper Config" name="config">
        <div class="section">
          <el-form label-width="200px" size="small" v-if="configLoaded">
            <el-form-item label="Include Baseline (ASUS)">
              <el-switch v-model="config.include_baseline" @change="saveConfig" />
            </el-form-item>
            <el-form-item label="Parallel Ports">
              <el-input v-model="portsStr" placeholder="9222,9223,9224" style="width: 220px" @blur="saveConfig" />
            </el-form-item>
            <el-form-item label="Mode">
              <el-select v-model="config.scraper_config.mode" @change="saveConfig" style="width: 140px">
                <el-option value="manual" label="Manual" />
                <el-option value="auto" label="Auto" />
              </el-select>
            </el-form-item>
            <el-form-item label="Delay Between Requests (s)">
              <el-input-number v-model="config.scraper_config.delay_between_requests" :min="0.5" :max="30" :step="0.5" @change="saveConfig" />
            </el-form-item>
            <el-form-item label="Page Wait Time (s)">
              <el-input-number v-model="config.scraper_config.wait_time" :min="1" :max="30" :step="1" @change="saveConfig" />
            </el-form-item>
          </el-form>
          <el-tag v-if="configSaved" type="success" size="small">Saved</el-tag>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import {
  getConfig, updateConfig, getCompanies, removeCompany,
  getCompaniesToMatch, addCompanyToMatch, removeCompanyToMatch, getBaseline,
  runFinderMatch, runFinderExplore, getFinderStatus, stopFinder
} from '../api'

const activeTab = ref('companies')

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
const companiesToMatch = ref<any[]>([])
const newCompanyName = ref('')

async function loadCompaniesToMatch() {
  try {
    const { data } = await getCompaniesToMatch()
    companiesToMatch.value = data.companies
  } catch { /* ignore */ }
}

async function handleAddToMatch() {
  const name = newCompanyName.value.trim()
  if (!name) return
  await addCompanyToMatch(name)
  newCompanyName.value = ''
  await loadCompaniesToMatch()
}

async function handleRemoveFromMatch(name: string) {
  await removeCompanyToMatch(name)
  await loadCompaniesToMatch()
}

// ─── Finder ─────────────────────────────────────────────
const finderRunning = ref(false)
const finderLogs = ref<string[]>([])
let finderPoll: ReturnType<typeof setInterval> | null = null

async function handleMatch() {
  await runFinderMatch()
  finderRunning.value = true
  finderLogs.value = []
  startFinderPolling()
}

async function handleExplore() {
  await runFinderExplore()
  finderRunning.value = true
  finderLogs.value = []
  startFinderPolling()
}

async function handleStopFinder() {
  await stopFinder()
  finderRunning.value = false
  stopFinderPolling()
}

function startFinderPolling() {
  stopFinderPolling()
  finderPoll = setInterval(async () => {
    try {
      const { data } = await getFinderStatus()
      finderLogs.value = data.logs
      finderRunning.value = data.running
      if (!data.running) {
        stopFinderPolling()
        loadCompanies()
      }
    } catch { /* ignore */ }
  }, 2000)
}

function stopFinderPolling() {
  if (finderPoll) { clearInterval(finderPoll); finderPoll = null }
}

// ─── Baseline ───────────────────────────────────────────
const baselineLocations = ref<any[]>([])

async function loadBaseline() {
  try {
    const { data } = await getBaseline()
    baselineLocations.value = data.locations
  } catch { /* ignore */ }
}

// ─── Lifecycle ──────────────────────────────────────────
onMounted(() => {
  loadConfig()
  loadCompanies()
  loadCompaniesToMatch()
  loadBaseline()
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
