<template>
  <div>
    <h3 class="page-title">Company Comparison</h3>

    <!-- Radar Chart -->
    <el-card style="margin-bottom: 20px">
      <template #header><span style="font-weight: 600">Multi-Dimension Radar</span></template>

      <!-- Clickable Legend: toggle companies on/off -->
      <div class="legend-row">
        <span
          v-for="c in companies"
          :key="c.company"
          class="legend-item"
          :class="{ inactive: !selectedCompanies.includes(c.company) }"
          @click="toggleCompany(c.company)"
        >
          <span class="legend-square" :style="{ background: getCompanyColor(c.company) }"></span>
          {{ c.company }}
        </span>
      </div>

      <v-chart :option="radarOption" style="height: 480px" autoresize />
    </el-card>

    <!-- Gap Analysis -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span style="font-weight: 600">Gap Analysis</span>
          <div class="gap-controls">
            <el-select v-model="companyA" size="small" style="width: 160px">
              <el-option v-for="name in companyNames" :key="name" :label="name" :value="name" />
            </el-select>
            <span style="margin: 0 6px; color: var(--text-secondary)">vs</span>
            <el-select v-model="companyB" size="small" style="width: 160px">
              <el-option v-for="name in companyNames" :key="name" :label="name" :value="name" />
            </el-select>
          </div>
        </div>
      </template>
      <el-table :data="gapData" stripe style="width: 100%">
        <el-table-column prop="dimension" label="Dimension" min-width="140" />
        <el-table-column prop="valueA" :label="companyA" min-width="100" align="center" />
        <el-table-column prop="valueB" :label="companyB" min-width="100" align="center" />
        <el-table-column label="Gap" min-width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.gap != null" :style="{ color: row.gap > 0 ? '#67c23a' : row.gap < 0 ? '#f56c6c' : '#ccc' }">
              {{ row.gap > 0 ? '+' : '' }}{{ row.gap.toFixed(2) }}
            </span>
            <span v-else style="color: #666">N/A</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { RadarChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent, RadarComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { getOverview } from '../api'
import { useDashboardStore } from '../stores/dashboard'
import { useThemeStore } from '../stores/theme'
import type { CompanyOverview } from '../types'
import { type DimensionKey, DIMENSION_LABELS } from '../types'

use([RadarChart, TooltipComponent, LegendComponent, RadarComponent, CanvasRenderer])

const COMPANY_COLORS: Record<string, string> = {
  Google: '#4285f4',
  NVIDIA: '#76b900',
  'HP Inc.': '#2196f3',
  MSI: '#f44336',
  'Dell Technologies': '#ff9800',
  'Trend Micro': '#9c27b0',
  Wiwynn: '#00bcd4',
  'Compal Electronics': '#ff7043',
  Lenovo: '#e91e63',
  Inventec: '#ff5722',
  'AU Optronics': '#607d8b',
  Acer: '#8bc34a',
  TSMC: '#795548',
  ASUS: '#00bcd4',
  'Quanta Computer': '#3f51b5',
  'Delta Electronics': '#673ab7',
  Wistron: '#009688',
  Pegatron: '#f06292',
}

const DEFAULT_SELECTED = ['ASUS', 'NVIDIA', 'Google', 'Dell Technologies', 'HP Inc.', 'Acer', 'Lenovo', 'MSI']

const store = useDashboardStore()
const themeStore = useThemeStore()
const companies = ref<CompanyOverview[]>([])
const selectedCompanies = ref<string[]>([])
const companyA = ref('')
const companyB = ref('')

// Case-insensitive color lookup
function getCompanyColor(name: string): string {
  if (COMPANY_COLORS[name]) return COMPANY_COLORS[name]
  const entry = Object.entries(COMPANY_COLORS).find(([k]) => k.toLowerCase() === name.toLowerCase())
  return entry?.[1] ?? '#409eff'
}

const companyNames = computed(() => companies.value.map(c => c.company))

const visibleCompanies = computed(() =>
  companies.value.filter(c => selectedCompanies.value.includes(c.company))
)

function toggleCompany(name: string) {
  const idx = selectedCompanies.value.indexOf(name)
  if (idx >= 0) {
    selectedCompanies.value.splice(idx, 1)
  } else {
    selectedCompanies.value.push(name)
  }
}

const DIMS: DimensionKey[] = ['overall', 'culture', 'wlb', 'salary', 'career', 'diversity', 'management']

// Normalize dimension value for radar chart (CEO Approval % -> 1-5 scale)
const getRadarValue = (c: CompanyOverview, d: DimensionKey): number => {
  const val = c[d]
  if (val == null) return 0
  if (d === 'ceo_approval') return val / 20
  return val
}

const radarOption = computed(() => {
  const isDark = themeStore.mode === 'dark'
  const textColor = isDark ? '#A0A0A0' : '#606060'
  const lineColor = isDark ? '#2A2A2A' : '#E0E0E0'

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: isDark ? '#1A1A1A' : '#FFF',
      borderColor: isDark ? '#2A2A2A' : '#E0E0E0',
      textStyle: { color: isDark ? '#F5F5F5' : '#1A1A1A' },
    },
    legend: { show: false },
    radar: {
      indicator: DIMS.map(d => ({ name: DIMENSION_LABELS[d], max: 5, min: 2 })),
      axisName: { color: textColor, fontSize: 12 },
      splitLine: { lineStyle: { color: lineColor } },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: lineColor } },
      radius: '65%',
    },
    series: [{
      type: 'radar',
      data: visibleCompanies.value.map(c => ({
        name: c.company,
        value: DIMS.map(d => getRadarValue(c, d)),
        lineStyle: { color: getCompanyColor(c.company), width: 2 },
        areaStyle: { color: getCompanyColor(c.company) + '18' },
        itemStyle: { color: getCompanyColor(c.company) },
        symbol: 'circle',
        symbolSize: 5,
      })),
    }],
  }
})

const gapData = computed(() => {
  const a = companies.value.find(c => c.company === companyA.value)
  const b = companies.value.find(c => c.company === companyB.value)
  if (!a || !b) return []
  return DIMS.map(key => ({
    dimension: DIMENSION_LABELS[key],
    valueA: a[key]?.toFixed(2) ?? 'N/A',
    valueB: b[key]?.toFixed(2) ?? 'N/A',
    gap: a[key] != null && b[key] != null ? a[key]! - b[key]! : null,
  }))
})

async function loadData() {
  const { data } = await getOverview(store.selectedRunId || undefined)
  companies.value = data
  // Match DEFAULT_SELECTED against actual company names (case-insensitive)
  const available = data.map(c => c.company)
  const matched = available.filter(n =>
    DEFAULT_SELECTED.some(d => d.toLowerCase() === n.toLowerCase())
  )
  selectedCompanies.value = matched.length > 0 ? matched : available.slice(0, 8)
  // Set gap analysis defaults
  const asusName = available.find(n => n.toLowerCase() === 'asus')
  companyA.value = asusName ?? available[0] ?? ''
  companyB.value = available.find(n => n !== companyA.value) ?? available[1] ?? ''
}

onMounted(loadData)
watch(() => store.selectedRunId, loadData)
</script>

<style scoped>
.page-title { font-size: 22px; font-weight: 600; color: var(--text-primary); margin: 0 0 14px 0; }
.card-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
.gap-controls { display: flex; align-items: center; gap: 8px; }
.legend-row { display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 8px; padding: 0 8px; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--text-secondary); cursor: pointer; user-select: none; transition: opacity 0.2s; }
.legend-item.inactive { opacity: 0.35; }
.legend-square { width: 12px; height: 12px; border-radius: 2px; display: inline-block; }
</style>
