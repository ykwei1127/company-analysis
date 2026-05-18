<template>
  <div>
    <h3 class="page-title">Company Overview</h3>

    <!-- Filter -->
    <div class="filter-row">
      <el-select v-model="locationFilter" placeholder="Filter by location" clearable size="default" style="width: 260px">
        <el-option label="Global (All)" value="global" />
        <el-option v-for="loc in locationOptions" :key="loc" :label="loc" :value="loc" />
      </el-select>
    </div>

    <!-- KPI Cards -->
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-value blue">{{ filteredCompanies.length }}</div>
        <div class="kpi-label">COMPANIES</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value blue">{{ asusOverall }}</div>
        <div class="kpi-label">ASUS OVERALL</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value blue">{{ asusRank }}</div>
        <div class="kpi-label">ASUS RANK</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value blue">{{ topCompany }}</div>
        <div class="kpi-label">TOP COMPANY</div>
      </div>
    </div>

    <!-- Bar Chart: Overall Rating -->
    <el-card style="margin-bottom: 20px">
      <template #header><span style="font-weight: 600">Overall Rating Ranking</span></template>
      <v-chart :option="barOption" style="height: 400px" autoresize />
    </el-card>

    <!-- Company Summary Table -->
    <el-card>
      <template #header><span style="font-weight: 600">Company Summary</span></template>
      <el-table :data="filteredCompanies" stripe style="width: 100%" :default-sort="{ prop: 'overall', order: 'descending' }">
        <el-table-column prop="rank" label="#" width="50" align="center" sortable />
        <el-table-column prop="company" label="Company" width="180" sortable />
        <el-table-column prop="overall" label="Overall" width="90" align="center" sortable />
        <el-table-column prop="culture" label="Culture" width="90" align="center" sortable />
        <el-table-column prop="wlb" label="WLB" width="80" align="center" sortable />
        <el-table-column prop="salary" label="Salary" width="80" align="center" sortable />
        <el-table-column prop="career" label="Career" width="80" align="center" sortable />
        <el-table-column prop="diversity" label="D&I" width="70" align="center" sortable />
        <el-table-column prop="management" label="Mgmt" width="75" align="center" sortable />
        <el-table-column prop="recommend" label="Recommend%" width="110" align="center" sortable>
          <template #default="{ row }">
            {{ row.recommend != null ? row.recommend.toFixed(0) + '%' : '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="ceo_approval" label="CEO%" width="80" align="center" sortable>
          <template #default="{ row }">
            {{ row.ceo_approval != null ? row.ceo_approval.toFixed(0) + '%' : '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="total_reviews" label="Reviews" width="90" align="center" sortable />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { getOverview, getOverviewByLocation } from '../api'
import { useDashboardStore } from '../stores/dashboard'
import { useThemeStore } from '../stores/theme'
import type { CompanyOverview, LocationRating } from '../types'

use([BarChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

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

const store = useDashboardStore()
const themeStore = useThemeStore()
const companies = ref<CompanyOverview[]>([])
const allLocationRatings = ref<LocationRating[]>([])
const locationFilter = ref('global')

const locationOptions = computed(() => {
  const locs = new Set(allLocationRatings.value.map(r => r.baseline_location).filter(Boolean))
  locs.delete('Global')
  return [...locs].sort()
})

const filteredCompanies = computed(() => {
  if (!locationFilter.value || locationFilter.value === 'global') {
    return companies.value
  }
  const locData = allLocationRatings.value.filter(r => r.baseline_location === locationFilter.value)
  return locData.map((r, i) => ({ ...r, rank: i + 1 })).sort((a, b) => (b.overall || 0) - (a.overall || 0)).map((r, i) => ({ ...r, rank: i + 1 }))
})

const asusOverall = computed(() => {
  const asus = filteredCompanies.value.find(c => c.company === 'ASUS')
  return asus?.overall?.toFixed(2) ?? '—'
})

const asusRank = computed(() => {
  const sorted = [...filteredCompanies.value].sort((a, b) => (b.overall || 0) - (a.overall || 0))
  const idx = sorted.findIndex(c => c.company === 'ASUS')
  return idx >= 0 ? `#${idx + 1}` : '—'
})

const topCompany = computed(() => {
  const sorted = [...filteredCompanies.value].sort((a, b) => (b.overall || 0) - (a.overall || 0))
  return sorted[0]?.company ?? '—'
})

const barOption = computed(() => {
  const sorted = [...filteredCompanies.value].sort((a, b) => (b.overall || 0) - (a.overall || 0))
  const isDark = themeStore.mode === 'dark'
  const textColor = isDark ? '#A0A0A0' : '#606060'
  const gridColor = isDark ? '#2A2A2A' : '#E0E0E0'

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: isDark ? '#1A1A1A' : '#FFF',
      borderColor: isDark ? '#2A2A2A' : '#E0E0E0',
      textStyle: { color: isDark ? '#F5F5F5' : '#1A1A1A' },
    },
    grid: { left: 20, right: 20, top: 40, bottom: 80, containLabel: true },
    xAxis: {
      type: 'category',
      data: sorted.map(c => c.company),
      axisLabel: { color: textColor, fontSize: 11, rotate: 40, interval: 0 },
      axisLine: { lineStyle: { color: gridColor } },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 5,
      axisLabel: { color: textColor },
      splitLine: { lineStyle: { color: gridColor } },
    },
    series: [{
      type: 'bar',
      data: sorted.map(c => ({
        value: c.overall || 0,
        itemStyle: { color: COMPANY_COLORS[c.company] || '#409eff' },
      })),
      barWidth: '50%',
      label: {
        show: true,
        position: 'top',
        color: textColor,
        fontSize: 11,
        formatter: (p: any) => p.value?.toFixed(2),
      },
    }],
  }
})

async function loadData() {
  const [overview, byLoc] = await Promise.all([
    getOverview(store.selectedRunId || undefined),
    getOverviewByLocation(store.selectedRunId || undefined),
  ])
  companies.value = overview.data
  allLocationRatings.value = byLoc.data
}

onMounted(loadData)
watch(() => store.selectedRunId, loadData)
</script>

<style scoped>
.page-title { font-size: 22px; font-weight: 600; color: var(--text-primary); margin: 0 0 14px 0; }
.filter-row { margin-bottom: 16px; }

.kpi-row { display: flex; gap: 16px; margin-bottom: 20px; }
.kpi-card {
  flex: 1;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 20px 24px;
  text-align: center;
}
.kpi-value { font-size: 28px; font-weight: 700; }
.kpi-value.blue { color: var(--accent-blue-light); }
.kpi-label { font-size: 11px; color: var(--text-secondary); margin-top: 6px; letter-spacing: 0.5px; text-transform: uppercase; }
</style>
