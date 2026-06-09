<template>
  <div>
    <h3 class="page-title">Company Comparison</h3>

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

    <!-- Radar Chart -->
    <el-card style="margin-bottom: 20px">
      <template #header><span style="font-weight: 600">Multi-Dimension Radar</span></template>

      <!-- Clickable Legend: toggle companies on/off -->
      <div class="legend-row">
        <span
          v-for="c in sortedCompanies"
          :key="c.company"
          class="legend-item"
          :class="{ inactive: !selectedCompanies.includes(c.company), asus: c.company === 'ASUS' }"
          @click="toggleCompany(c.company)"
        >
          <span class="legend-square" :style="{ background: getCompanyColor(c.company) }"></span>
          <span v-if="c.company === 'ASUS'" class="asus-star">★</span> {{ c.company }}
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
              <el-option v-for="name in companyNames" :key="name" :value="name">
                <span v-if="name === 'ASUS'" class="asus-star">★</span> {{ name }}
              </el-option>
            </el-select>
            <span style="margin: 0 6px; color: var(--text-secondary)">vs</span>
            <el-select v-model="companyB" size="small" style="width: 160px">
              <el-option v-for="name in companyNames" :key="name" :value="name">
                <span v-if="name === 'ASUS'" class="asus-star">★</span> {{ name }}
              </el-option>
            </el-select>
          </div>
        </div>
      </template>
      <el-table :data="gapData" stripe style="width: 100%">
        <el-table-column prop="dimension" label="Dimension" min-width="140" />
        <el-table-column min-width="100" align="center">
          <template #header>
            <span v-if="companyA === 'ASUS'" class="asus-star">★</span> {{ companyA }}
          </template>
          <template #default="{ row }">{{ row.valueA }}</template>
        </el-table-column>
        <el-table-column min-width="100" align="center">
          <template #header>
            <span v-if="companyB === 'ASUS'" class="asus-star">★</span> {{ companyB }}
          </template>
          <template #default="{ row }">{{ row.valueB }}</template>
        </el-table-column>
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
import { getOverviewByCategory } from '../api'
import { useDashboardStore } from '../stores/dashboard'
import { useCategoryStore } from '../stores/category'
import { useThemeStore } from '../stores/theme'
import type { CompanyOverview } from '../types'
import { type DimensionKey, DIMENSION_LABELS } from '../types'

use([RadarChart, TooltipComponent, LegendComponent, RadarComponent, CanvasRenderer])

// High-contrast color palette for better visual differentiation
const COMPANY_COLORS: Record<string, string> = {
  // ASUS - Cyan (most prominent)
  ASUS: '#00e5ff',
  // R&D in Taiwan - distinct hues
  Google: '#2979ff',     // Blue
  MSI: '#ff1744',        // Red
  'Trend Micro': '#d500f9', // Purple
  Acer: '#76ff03',       // Lime Green
  // Global Brands - distinct from Taiwan companies
  NVIDIA: '#ff9100',     // Orange
  'HP Inc.': '#18ffff',  // Cyan-Light
  'Dell Technologies': '#ff3d00', // Deep Orange
  Lenovo: '#ffea00',     // Yellow
  // Taiwan Tech OEMs - distinct hues (avoid blue/cyan which is too similar to ASUS)
  'Quanta Computer': '#ff4081', // Pink
  Wistron: '#76ff03',    // Lime Green
  'Compal Electronics': '#ff9100', // Orange
  Wiwynn: '#e91e63',     // Pink-Red (avoid blue tones)
  TSMC: '#ffd600',       // Amber
  'Delta Electronics': '#651fff', // Deep Purple (avoid blue tones)
  Inventec: '#1de9b6',   // Teal
  Pegatron: '#ff3d00',   // Deep Orange
  'AU Optronics': '#9c27b0', // Purple
}

const store = useDashboardStore()
const categoryStore = useCategoryStore()
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

const displayCompanies = computed(() => {
  const categoryCompanies = categoryStore.currentCategory?.companies || []
  const byName = new Map(
    companies.value.map(company => [company.company.toLowerCase(), company] as const)
  )
  return categoryCompanies.map(name => byName.get(name.toLowerCase()) || createPlaceholderCompany(name))
})

const companyNames = computed(() => displayCompanies.value.map(c => c.company))

// Sort companies with ASUS first for legend display
const sortedCompanies = computed(() => {
  const list = [...displayCompanies.value]
  const asusIndex = list.findIndex(c => c.company === 'ASUS')
  if (asusIndex > 0) {
    const asus = list.splice(asusIndex, 1)[0]
    list.unshift(asus)
  }
  return list
})

const visibleCompanies = computed(() =>
  displayCompanies.value.filter(c => selectedCompanies.value.includes(c.company))
)

const radarCompanies = computed(() =>
  visibleCompanies.value.filter(c => DIMS.some(d => c[d] != null))
)

// Get default selected companies based on category
// Always include ASUS, then select top 2 companies by overall rating (max 3 total)
const getDefaultSelected = () => {
  const category = categoryStore.currentCategory
  if (!category) return []

  // Always include ASUS first
  const result = ['ASUS']

  // Get other companies with data, sorted by overall rating (descending)
  const otherCompanies = displayCompanies.value
    .filter(c => c.company !== 'ASUS' && c.overall != null)
    .sort((a, b) => (b.overall || 0) - (a.overall || 0))
    .slice(0, 2)
    .map(c => c.company)

  // Add top ranked companies until we have 3 total
  for (const company of otherCompanies) {
    if (result.length < 3 && !result.includes(company)) {
      result.push(company)
    }
  }

  // If still not enough, fill from category definition
  if (result.length < 3) {
    for (const company of category.companies) {
      if (result.length < 3 && !result.includes(company)) {
        result.push(company)
      }
    }
  }

  return result
}

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
      data: radarCompanies.value.map(c => ({
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
  const a = displayCompanies.value.find(c => c.company === companyA.value)
  const b = displayCompanies.value.find(c => c.company === companyB.value)
  if (!a || !b) return []
  return DIMS.map(key => ({
    dimension: DIMENSION_LABELS[key],
    valueA: a[key]?.toFixed(2) ?? 'N/A',
    valueB: b[key]?.toFixed(2) ?? 'N/A',
    gap: a[key] != null && b[key] != null ? a[key]! - b[key]! : null,
  }))
})

async function loadData() {
  const category = categoryStore.selectedCategory
  const { data } = await getOverviewByCategory(category, store.selectedRunId || undefined)
  companies.value = data.companies || []

  // Set default selected companies based on category
  const available: string[] = displayCompanies.value.map((c: CompanyOverview) => c.company)
  const defaults = getDefaultSelected()
  const matched = available.filter((n: string) =>
    defaults.some(d => d.toLowerCase() === n.toLowerCase())
  )
  selectedCompanies.value = matched.length > 0 ? matched : available.slice(0, 6)

  // Set gap analysis defaults - ASUS vs first competitor in category
  const asusName = available.find((n: string) => n.toLowerCase() === 'asus')
  const competitor = defaults.find(d => d.toLowerCase() !== 'asus') ?? available.find((n: string) => n.toLowerCase() !== 'asus')
  companyA.value = asusName ?? available[0] ?? ''
  companyB.value = competitor ?? available.find((n: string) => n !== companyA.value) ?? available[1] ?? ''
}

onMounted(loadData)
watch(() => store.selectedRunId, loadData)
watch(() => categoryStore.selectedCategory, loadData)
</script>

<style scoped>
.page-title { font-size: 22px; font-weight: 600; color: var(--text-primary); margin: 0 0 14px 0; }
.card-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
.gap-controls { display: flex; align-items: center; gap: 8px; }
.legend-row { display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 8px; padding: 0 8px; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--text-secondary); cursor: pointer; user-select: none; transition: opacity 0.2s; }
.legend-item.inactive { opacity: 0.35; }
.legend-item.asus { color: var(--accent-blue-light); font-weight: 600; background: rgba(64,158,255,0.08); padding: 2px 8px; border-radius: 4px; }
.legend-square { width: 12px; height: 12px; border-radius: 2px; display: inline-block; }
.asus-star { color: gold; margin-right: 4px; }

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
</style>
