<template>
  <div>
    <h3 class="page-title">Company Overview</h3>

    <!-- Category Selector -->
    <div class="category-selector-row">
      <div class="category-tabs">
        <button
          v-for="cat in categoryStore.categories"
          :key="cat.key"
          class="category-tab"
          :class="{ active: categoryStore.selectedCategory === cat.key }"
          @click="categoryStore.selectCategory(cat.key)"
        >
          {{ cat.name }}
        </button>
      </div>
    </div>

    <!-- Run Info Banner -->
    <div class="run-info-bar">
      <span class="run-info-title">{{ currentRunId || 'Latest' }}</span>
      <span class="run-info-divider">|</span>
      <span><strong>Category:</strong> {{ categoryStore.currentCategory?.name }}</span>
      <span class="run-info-divider">|</span>
      <span><strong>Companies:</strong> {{ filteredCompanies.length }}</span>
      <span v-if="categoryStore.isWeightedCategory" class="run-info-divider">|</span>
      <span v-if="categoryStore.isWeightedCategory">
        <strong>Mode:</strong> <el-tag type="success" size="small">Region-Weighted</el-tag>
      </span>
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

    <!-- ASUS Regional Performance (only for weighted categories) -->
    <el-card v-if="categoryStore.isWeightedCategory && asusRegionData.length > 0" style="margin-bottom: 20px">
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
          <div>
            <span style="font-weight: 600">ASUS Performance by Region</span>
            <span style="margin-left: 8px; font-size: 12px; color: var(--text-secondary)">
              (vs Regional Avg / Best)
            </span>
          </div>
          <div style="font-size: 11px; color: var(--text-muted); display: flex; gap: 12px;">
            <span><strong>ASUS:</strong> ASUS regional score</span>
            <span><strong>Avg:</strong> Average of all companies in this region</span>
            <span><strong>Best:</strong> Top company in this region</span>
            <span><strong>Gap:</strong> ASUS score minus regional average</span>
          </div>
        </div>
      </template>
      <div class="asus-region-grid">
        <div v-for="region in asusRegionData" :key="region.key" class="asus-region-card">
          <div class="asus-region-header">
            <span class="asus-region-name">{{ region.label }}</span>
            <span class="asus-region-rank">#{{ region.asusRank }} of {{ region.totalCompanies }}</span>
          </div>
          <div class="asus-region-body">
            <div class="asus-score-row">
              <span class="label">ASUS</span>
              <span class="score asus" :class="getScoreClass(region.asusScore)">{{ region.asusScore.toFixed(2) }}</span>
            </div>
            <div class="asus-score-row">
              <span class="label">Avg</span>
              <span class="score">{{ region.avgScore.toFixed(2) }}</span>
            </div>
            <div class="asus-score-row">
              <span class="label">Best</span>
              <span class="score best">{{ region.bestScore.toFixed(2) }}</span>
              <span class="best-company">{{ region.bestCompany }}</span>
            </div>
            <div class="asus-gap-bar" :class="{ positive: region.asusGap >= 0, negative: region.asusGap < 0 }">
              <span class="gap-label">{{ region.asusGap >= 0 ? '+' : '' }}{{ region.asusGap.toFixed(2) }} vs avg</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Category Info -->
    <el-alert
      :title="categoryStore.currentCategory?.name"
      type="info"
      :closable="false"
      style="margin-bottom: 16px;"
    >
      <div style="font-size: 13px; line-height: 1.6;">
        Comparing: {{ categoryStore.currentCategory?.companies.join(', ') }}
        <span v-if="categoryStore.isWeightedCategory">
          <br><strong>Weighted Mode:</strong> Scores are calculated using review-weighted averages across all regions.
        </span>
      </div>
    </el-alert>

    <!-- Bar Chart: Overall Rating -->
    <el-card style="margin-bottom: 20px">
      <template #header><span style="font-weight: 600">Overall Rating Ranking</span></template>
      <v-chart :option="barOption" style="height: 400px" autoresize />
    </el-card>

    <!-- Company Summary Table -->
    <el-card>
      <template #header><span style="font-weight: 600">Company Summary</span></template>
      <el-table :data="filteredCompanies" stripe style="width: 100%" :default-sort="{ prop: 'overall', order: 'descending' }">
        <el-table-column prop="rank" label="#" width="45" align="center" sortable>
          <template #default="{ row }">
            {{ row.rank > 0 ? row.rank : '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="company" label="Company" min-width="120" sortable>
          <template #default="{ row }">
            <span v-if="row.company === 'ASUS'" class="asus-star">★</span>
            <span :class="{ 'asus-name': row.company === 'ASUS' }">{{ row.company }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="source_mode" label="Type" width="90" align="center" sortable>
          <template #default="{ row }">
            <el-tag
              v-if="row.source_mode"
              :type="row.source_mode === 'country' ? 'success' : row.source_mode === 'scan' ? 'warning' : row.source_mode === 'city' ? 'danger' : 'info'"
              size="small"
            >
              {{ row.source_mode }}
            </el-tag>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column prop="overall" label="Overall" min-width="70" align="center" sortable>
          <template #default="{ row }">{{ formatScore(row.overall) }}</template>
        </el-table-column>
        <el-table-column prop="culture" label="Culture" min-width="70" align="center" sortable>
          <template #default="{ row }">{{ formatScore(row.culture) }}</template>
        </el-table-column>
        <el-table-column prop="wlb" label="WLB" min-width="60" align="center" sortable>
          <template #default="{ row }">{{ formatScore(row.wlb) }}</template>
        </el-table-column>
        <el-table-column prop="salary" label="Salary" min-width="60" align="center" sortable>
          <template #default="{ row }">{{ formatScore(row.salary) }}</template>
        </el-table-column>
        <el-table-column prop="career" label="Career" min-width="60" align="center" sortable>
          <template #default="{ row }">{{ formatScore(row.career) }}</template>
        </el-table-column>
        <el-table-column prop="diversity" label="D&I" min-width="55" align="center" sortable>
          <template #default="{ row }">{{ formatScore(row.diversity) }}</template>
        </el-table-column>
        <el-table-column prop="management" label="Mgmt" min-width="60" align="center" sortable>
          <template #default="{ row }">{{ formatScore(row.management) }}</template>
        </el-table-column>
        <el-table-column prop="recommend" label="Recommend%" min-width="95" align="center" sortable>
          <template #default="{ row }">
            {{ row.recommend != null ? row.recommend.toFixed(0) + '%' : '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="ceo_approval" label="CEO%" min-width="65" align="center" sortable>
          <template #default="{ row }">
            {{ row.ceo_approval != null ? row.ceo_approval.toFixed(0) + '%' : '—' }}
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
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { getOverviewByCategory, getOverviewByLocation } from '../api'
import { useDashboardStore } from '../stores/dashboard'
import { useCategoryStore } from '../stores/category'
import { useThemeStore } from '../stores/theme'
import type { CompanyOverview } from '../types'

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
const categoryStore = useCategoryStore()
const themeStore = useThemeStore()
const companies = ref<CompanyOverview[]>([])
const regionData = ref<RegionInfo[]>([])

// Case-insensitive color lookup
function getCompanyColor(name: string): string {
  if (COMPANY_COLORS[name]) return COMPANY_COLORS[name]
  const entry = Object.entries(COMPANY_COLORS).find(([k]) => k.toLowerCase() === name.toLowerCase())
  return entry?.[1] ?? '#409eff'
}

// Region info type
interface RegionCompany {
  company: string
  overall: number | null
  total_reviews: number
}

interface RegionInfo {
  key: string
  label: string
  companies: RegionCompany[]
  avgOverall: number
}

interface AsusRegionData {
  key: string
  label: string
  asusScore: number
  asusRank: number
  totalCompanies: number
  avgScore: number
  bestScore: number
  bestCompany: string
  asusGap: number // vs average
}

function createPlaceholderCompany(company: string): CompanyOverview {
  return {
    company,
    rank: 0,
    overall: null,
    culture: null,
    wlb: null,
    salary: null,
    career: null,
    diversity: null,
    management: null,
    recommend: null,
    ceo_approval: null,
    total_reviews: null,
    source_mode: 'unknown',
  }
}

const filteredCompanies = computed(() => {
  const categoryCompanies = categoryStore.currentCategory?.companies || []
  const byName = new Map(
    companies.value.map(company => [company.company.toLowerCase(), company] as const)
  )

  return categoryCompanies.map(name => byName.get(name.toLowerCase()) || createPlaceholderCompany(name))
})

const asusRegionData = computed<AsusRegionData[]>(() => {
  return regionData.value.map(region => {
    const sorted = [...region.companies].sort((a, b) => (b.overall || 0) - (a.overall || 0))
    const asusIdx = sorted.findIndex(c => c.company.toLowerCase() === 'asus')
    const asusEntry = asusIdx >= 0 ? sorted[asusIdx] : null
    const asusScore = asusEntry?.overall || 0
    const avgScore = region.avgOverall
    const best = sorted[0]

    return {
      key: region.key,
      label: region.label,
      asusScore,
      asusRank: asusIdx >= 0 ? asusIdx + 1 : 0,
      totalCompanies: sorted.length,
      avgScore,
      bestScore: best?.overall || 0,
      bestCompany: best?.company || '',
      asusGap: asusScore - avgScore
    }
  }).filter(r => r.asusScore > 0)
})

const hasMixedModes = computed(() => false) // Simplified for category mode

// Get current run ID from dashboard store
const currentRunId = computed(() => store.selectedRunId || 'Latest')

const asusOverall = computed(() => {
  const asus = filteredCompanies.value.find(c => c.company?.toLowerCase() === 'asus')
  return asus?.overall?.toFixed(2) ?? '—'
})

const asusRank = computed(() => {
  const asus = filteredCompanies.value.find(c => c.company?.toLowerCase() === 'asus')
  return asus?.rank ? `#${asus.rank}` : '—'
})

const topCompany = computed(() => {
  const sorted = [...filteredCompanies.value]
    .filter(c => c.overall != null)
    .sort((a, b) => (b.overall || 0) - (a.overall || 0))
  return sorted[0]?.company ?? '—'
})

function getScoreClass(score: number): string {
  if (score >= 4.4) return 'excellent'
  if (score >= 4.0) return 'good'
  if (score >= 3.7) return 'average'
  if (score >= 3.3) return 'below-average'
  return 'poor'
}

function formatScore(score: number | null | undefined): string {
  return score != null ? score.toFixed(2) : '—'
}

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
        value: c.overall ?? 0,
        displayValue: c.overall,
        itemStyle: { color: getCompanyColor(c.company) },
      })),
      barWidth: '50%',
      label: {
        show: true,
        position: 'top',
        color: textColor,
        fontSize: 11,
        formatter: (p: any) => p.data?.displayValue != null ? p.data.displayValue.toFixed(2) : '—',
      },
    }],
  }
})

async function loadData() {
  try {
    const category = categoryStore.selectedCategory
    const { data } = await getOverviewByCategory(category, store.selectedRunId || undefined)

    companies.value = data.companies || []

    // Build region data for weighted categories
    if (data.regions && categoryStore.isWeightedCategory) {
      const regionMap: Record<string, string> = {
        north_america: 'North America',
        europe: 'Europe',
        asia: 'Asia',
        south_america: 'South America',
        oceania: 'Oceania',
        global: 'Global'
      }

      const regions = data.regions as Record<string, RegionCompany[]>
      regionData.value = Object.entries(regions)
        .filter(([_, comps]) => comps && Array.isArray(comps) && comps.length > 0)
        .map(([key, comps]) => {
          const regionCompanies = comps
          const avgOverall = regionCompanies.reduce((sum: number, c: RegionCompany) => sum + (c.overall || 0), 0) / regionCompanies.length
          return {
            key,
            label: regionMap[key] || key,
            companies: regionCompanies.sort((a: RegionCompany, b: RegionCompany) => (b.overall || 0) - (a.overall || 0)),
            avgOverall
          }
        })
        .sort((a: RegionInfo, b: RegionInfo) => b.avgOverall - a.avgOverall)
    } else {
      regionData.value = []
    }
  } catch (e) {
    console.error('Failed to load data', e)
  }
}

onMounted(loadData)
watch(() => store.selectedRunId, loadData)
watch(() => categoryStore.selectedCategory, loadData)
</script>

<style scoped>
.page-title { font-size: 22px; font-weight: 600; color: var(--text-primary); margin: 0 0 14px 0; }
.filter-row { margin-bottom: 16px; }

.run-info-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 14px;
  margin-bottom: 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}
.run-info-title {
  font-weight: 600;
  color: var(--text-primary);
  font-family: monospace;
  font-size: 13px;
}
.run-info-divider {
  color: var(--border-color);
  font-size: 16px;
}

/* ASUS Regional Performance Cards */
.asus-region-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}
.asus-region-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 14px;
}
.asus-region-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-color);
}
.asus-region-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}
.asus-region-rank {
  font-size: 11px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  padding: 2px 8px;
  border-radius: 10px;
}
.asus-region-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.asus-score-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}
.asus-score-row .label {
  color: var(--text-secondary);
}
.asus-score-row .score {
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  min-width: 40px;
  text-align: center;
}
.asus-score-row .score.asus {
  font-size: 16px;
}
.asus-score-row .score.best {
  background: var(--bg-secondary);
}
.asus-score-row .best-company {
  font-size: 11px;
  color: var(--text-secondary);
  margin-left: 4px;
}
.asus-gap-bar {
  margin-top: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  text-align: center;
}
.asus-gap-bar.positive {
  background: #2d6a2d;
  color: #fff;
}
.asus-gap-bar.negative {
  background: #c0392b;
  color: #fff;
}

/* Category Selector */
.category-selector-row {
  margin-bottom: 16px;
}
.category-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.category-tab {
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-card);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
}
.category-tab:hover {
  border-color: var(--accent-blue);
  color: var(--text-primary);
}
.category-tab.active {
  background: var(--accent-blue);
  color: #fff;
  border-color: var(--accent-blue);
}

/* Region Cards */
.region-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}
.region-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 14px;
}
.region-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
}
.region-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}
.region-score {
  font-size: 18px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}
.region-score.excellent { background: #2d6a2d; color: #fff; }
.region-score.good { background: #4a9e4a; color: #fff; }
.region-score.average { background: #8bc48b; color: #1a1a1a; }
.region-score.below-average { background: #e8c97a; color: #1a1a1a; }
.region-score.poor { background: #c0392b; color: #fff; }

.region-companies {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.region-company {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}
.company-name {
  color: var(--text-secondary);
}
.company-score {
  font-weight: 600;
  color: var(--text-primary);
}

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
