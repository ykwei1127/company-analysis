<template>
  <div>
    <h3 class="page-title">Company Comparison</h3>

    <!-- Radar Chart -->
    <el-card style="margin-bottom: 20px">
      <template #header>
        <div class="card-header">
          <span>Multi-Dimension Radar</span>
          <div class="radar-controls">
            <span class="ctrl-label">Companies (max 8):</span>
            <el-select
              v-model="selectedCompanies"
              multiple
              collapse-tags
              collapse-tags-tooltip
              :max-collapse-tags="4"
              placeholder="Select"
              size="small"
              style="width: 340px"
            >
              <el-option v-for="name in companyNames" :key="name" :label="name" :value="name" />
            </el-select>
          </div>
        </div>
      </template>

      <!-- Legend -->
      <div class="legend-row">
        <span v-for="c in visibleCompanies" :key="c.company" class="legend-item">
          <span class="legend-dot" :style="{ background: COMPANY_COLORS[c.company] || '#555' }"></span>
          {{ c.company }}
        </span>
      </div>

      <v-chart :option="radarOption" style="height: 420px" autoresize />
    </el-card>

    <!-- Gap Analysis -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Gap Analysis</span>
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
        <el-table-column prop="dimension" label="Dimension" width="180" />
        <el-table-column prop="valueA" :label="companyA" width="120" align="center" />
        <el-table-column prop="valueB" :label="companyB" width="120" align="center" />
        <el-table-column label="Gap" width="120" align="center">
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
import { TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { getOverview } from '../api'
import { useDashboardStore } from '../stores/dashboard'
import type { CompanyOverview } from '../types'
import { type DimensionKey, DIMENSION_LABELS } from '../types'

use([RadarChart, TooltipComponent, LegendComponent, CanvasRenderer])

const COMPANY_COLORS: Record<string, string> = {
  ASUS: '#00bcd4',
  Acer: '#8bc34a',
  'Dell Technologies': '#ff9800',
  'HP Inc.': '#2196f3',
  Lenovo: '#e91e63',
  MSI: '#f44336',
  'Trend Micro': '#9c27b0',
  NVIDIA: '#76b900',
  Google: '#4285f4',
  TSMC: '#795548',
  Pegatron: '#607d8b',
  Inventec: '#ff5722',
  Wistron: '#009688',
}

const DEFAULT_COMPANIES = ['ASUS', 'NVIDIA', 'Google', 'Dell Technologies', 'HP Inc.', 'Acer']

const store = useDashboardStore()
const companies = ref<CompanyOverview[]>([])
const selectedCompanies = ref<string[]>([...DEFAULT_COMPANIES])
const companyA = ref('ASUS')
const companyB = ref('NVIDIA')

const companyNames = computed(() => companies.value.map(c => c.company))
const visibleCompanies = computed(() =>
  companies.value.filter(c => selectedCompanies.value.includes(c.company))
)

const DIMS: DimensionKey[] = ['overall', 'culture', 'wlb', 'salary', 'career', 'diversity', 'management']

// Normalize dimension value for radar chart (CEO Approval % -> 1-5 scale)
const getRadarValue = (c: CompanyOverview, d: DimensionKey): number => {
  const val = c[d]
  if (val == null) return 0
  if (d === 'ceo_approval') return val / 20
  return val
}

const radarOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: { trigger: 'item' },
  legend: { show: false },
  radar: {
    indicator: DIMS.map(d => ({ name: DIMENSION_LABELS[d], max: 5, min: 2 })),
    axisName: { color: '#A0A0A0', fontSize: 12 },
    splitLine: { lineStyle: { color: '#2A2A2A' } },
    splitArea: { show: false },
    axisLine: { lineStyle: { color: '#333' } },
    radius: '65%',
  },
  series: [{
    type: 'radar',
    data: visibleCompanies.value.map(c => ({
      name: c.company,
      value: DIMS.map(d => getRadarValue(c, d)),
      lineStyle: { color: COMPANY_COLORS[c.company] ?? '#555', width: 2 },
      areaStyle: { color: (COMPANY_COLORS[c.company] ?? '#555') + '18' },
      itemStyle: { color: COMPANY_COLORS[c.company] ?? '#555' },
      symbol: 'circle',
      symbolSize: 5,
    })),
  }],
}))

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
  const available = new Set(data.map((c: CompanyOverview) => c.company))
  selectedCompanies.value = DEFAULT_COMPANIES.filter(c => available.has(c))
  if (selectedCompanies.value.length === 0) selectedCompanies.value = data.slice(0, 6).map((c: CompanyOverview) => c.company)
}

onMounted(loadData)
watch(() => store.selectedRunId, loadData)
</script>

<style scoped>
.page-title { font-size: 22px; font-weight: 600; color: var(--text-primary); margin: 0 0 14px 0; }
.card-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
.radar-controls, .gap-controls { display: flex; align-items: center; gap: 8px; }
.ctrl-label { font-size: 12px; color: var(--text-secondary); }
.legend-row { display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 8px; padding: 0 8px; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--text-secondary); }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
</style>
