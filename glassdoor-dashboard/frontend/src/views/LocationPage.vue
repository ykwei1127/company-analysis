<template>
  <div>
    <h3 class="page-title">Location Breakdown</h3>

    <!-- View tabs -->
    <div class="view-tabs">
      <button class="view-tab" :class="{ active: viewMode === 'pivot' }" @click="viewMode = 'pivot'">Pivot Table</button>
      <button class="view-tab" :class="{ active: viewMode === 'heatmap' }" @click="viewMode = 'heatmap'">Heatmap</button>
    </div>

    <!-- ═══════ Pivot Table View ═══════ -->
    <div v-if="viewMode === 'pivot'">
      <!-- Filters -->
      <div class="controls-row">
        <el-select v-model="pivotCompanyFilter" placeholder="Filter by company" clearable multiple collapse-tags size="default" style="width: 280px">
          <el-option v-for="name in companyList" :key="name" :label="name" :value="name" />
        </el-select>
        <el-select v-model="pivotDimension" size="default" style="width: 200px">
          <el-option v-for="dim in PIVOT_DIMS" :key="dim.key" :label="dim.label" :value="dim.key" />
        </el-select>
      </div>

      <!-- Pivot: Location × Company -->
      <el-card>
        <template #header><span style="font-weight: 600">{{ pivotDimLabel }} by Location × Company</span></template>
        <div class="pivot-scroll">
          <table class="pivot-table">
            <thead>
              <tr>
                <th class="loc-col">Location</th>
                <th v-for="company in pivotCompanies" :key="company">{{ company }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="loc in pivotLocations" :key="loc">
                <td class="loc-col">{{ loc }}</td>
                <td v-for="company in pivotCompanies" :key="company">
                  <span v-if="getPivotValue(loc, company) != null" class="pivot-cell" :style="heatStyle(getPivotValue(loc, company)!)">
                    {{ getPivotValue(loc, company)!.toFixed(2) }}
                  </span>
                  <span v-else class="pivot-empty">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </el-card>
    </div>

    <!-- ═══════ Heatmap View ═══════ -->
    <div v-if="viewMode === 'heatmap'">
      <!-- Region tabs -->
      <div class="controls-row">
        <div class="region-tabs">
          <button v-for="r in REGIONS" :key="r.key" class="region-tab" :class="{ active: selectedRegion === r.key }" @click="selectedRegion = r.key">
            {{ r.label }}
          </button>
        </div>
      </div>

      <table class="heatmap-table">
        <thead>
          <tr>
            <th class="company-col">Company</th>
            <th v-for="dim in DIM_COLS" :key="dim.key">{{ dim.label }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in heatmapRows" :key="String(row.company)">
            <td class="company-col" :class="{ highlight: row.company === 'ASUS' }">
              <span v-if="row.company === 'ASUS'">&#9733; </span>{{ row.company }}
            </td>
            <td v-for="dim in DIM_COLS" :key="dim.key" class="heat-cell">
              <span v-if="row[dim.key] != null" class="heat-badge" :style="heatStyle(Number(row[dim.key]))">
                {{ Number(row[dim.key]).toFixed(1) }}
              </span>
              <span v-else class="heat-na">—</span>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Legend -->
      <div class="legend">
        <span v-for="l in legend" :key="l.label" class="legend-item">
          <span class="legend-swatch" :style="{ background: l.color }"></span> {{ l.label }}
        </span>
        <span class="legend-item"><span class="legend-swatch" style="background: #333"></span> n/a</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { getOverviewByLocation } from '../api'
import { useDashboardStore } from '../stores/dashboard'
import type { LocationRating, DimensionKey } from '../types'

const store = useDashboardStore()
const allRatings = ref<LocationRating[]>([])
const viewMode = ref<'pivot' | 'heatmap'>('pivot')
const selectedRegion = ref('north_america')
const pivotCompanyFilter = ref<string[]>([])
const pivotDimension = ref<DimensionKey>('overall')

// Region definitions
const REGIONS = [
  { key: 'north_america', label: 'North America', countries: ['United States', 'Canada'] },
  { key: 'europe', label: 'Europe', countries: ['United Kingdom', 'Germany', 'France', 'Netherlands', 'Italy', 'Spain', 'Hungary'] },
  { key: 'asia', label: 'Asia', countries: ['Taiwan', 'Japan', 'South Korea', 'India', 'Singapore', 'Thailand', 'Indonesia', 'Malaysia', 'Philippines', 'China', 'United Arab Emirates'] },
  { key: 'south_america', label: 'South America', countries: ['Brazil', 'Chile'] },
  { key: 'oceania', label: 'Oceania', countries: ['Australia'] },
  { key: 'global', label: 'Global', countries: [] },
]

// Pivot dimension options
const PIVOT_DIMS: { key: DimensionKey; label: string }[] = [
  { key: 'overall',    label: 'Overall' },
  { key: 'wlb',       label: 'Work/Life Balance' },
  { key: 'culture',   label: 'Culture & Values' },
  { key: 'career',    label: 'Career Opportunities' },
  { key: 'salary',    label: 'Compensation' },
  { key: 'management', label: 'Senior Management' },
  { key: 'diversity', label: 'Diversity & Inclusion' },
]

// Heatmap dimension columns
const DIM_COLS: { key: DimensionKey; label: string }[] = [
  { key: 'wlb',        label: 'Work-life balance' },
  { key: 'culture',    label: 'Culture & values' },
  { key: 'career',     label: 'Career opportunities' },
  { key: 'salary',     label: 'Compensation' },
  { key: 'management', label: 'Senior management' },
  { key: 'diversity',  label: 'Diversity & inclusion' },
]

const COMPANY_ORDER = ['ASUS', 'Acer', 'AU Optronics', 'Compal Electronics', 'Dell Technologies', 'Delta Electronics', 'Google', 'HP Inc.', 'Inventec', 'Lenovo', 'MSI', 'NVIDIA', 'Pegatron', 'Quanta Computer', 'Trend Micro', 'TSMC', 'Wistron', 'Wiwynn']

const legend = [
  { label: '4.4+',    color: '#2d6a2d' },
  { label: '4.0\u20134.3', color: '#4a9e4a' },
  { label: '3.7\u20133.9', color: '#8bc48b' },
  { label: '3.3\u20133.6', color: '#e8c97a' },
  { label: '3.0\u20133.2', color: '#e8956e' },
  { label: '<3.0',    color: '#c0392b' },
]

const companyList = computed(() => {
  const set = new Set(allRatings.value.map(r => r.company))
  return COMPANY_ORDER.filter(c => set.has(c)).concat([...set].filter(c => !COMPANY_ORDER.includes(c)).sort())
})

// ═══════ Pivot Table Logic ═══════
const pivotDimLabel = computed(() => PIVOT_DIMS.find(d => d.key === pivotDimension.value)?.label ?? 'Overall')

const pivotCompanies = computed(() => {
  if (pivotCompanyFilter.value.length > 0) return pivotCompanyFilter.value
  return companyList.value
})

const pivotLocations = computed(() => {
  const locs = new Set(allRatings.value.map(r => r.baseline_location).filter(Boolean))
  return [...locs].sort()
})

const getPivotValue = (loc: string, company: string): number | null => {
  const row = allRatings.value.find(r => r.company === company && r.baseline_location === loc)
  if (!row) return null
  const val = row[pivotDimension.value]
  return val != null ? val : null
}

// ═══════ Heatmap Logic ═══════
const regionRatings = computed(() => {
  const region = REGIONS.find(r => r.key === selectedRegion.value)
  if (!region) return []
  if (region.key === 'global') {
    return allRatings.value.filter(r =>
      !r.baseline_location || r.baseline_location.toLowerCase() === 'global'
    )
  }
  return allRatings.value.filter(r =>
    r.country && region.countries.includes(r.country)
  )
})

const regionCompanies = computed(() => {
  const set = new Set(regionRatings.value.map(r => r.company))
  const ordered = COMPANY_ORDER.filter(c => set.has(c))
  const rest = [...set].filter(c => !COMPANY_ORDER.includes(c)).sort()
  return [...ordered, ...rest]
})

const heatmapRows = computed(() => {
  return regionCompanies.value.map(company => {
    const rows = regionRatings.value.filter(r => r.company === company)
    const row: Record<string, number | null | string> = { company }
    for (const dim of DIM_COLS) {
      const vals = rows.map(r => r[dim.key]).filter((v): v is number => v != null)
      row[dim.key] = vals.length ? parseFloat((vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(2)) : null
    }
    return row
  })
})

const heatStyle = (val: number) => {
  if (val >= 4.4) return { background: '#2d6a2d', color: '#fff' }
  if (val >= 4.0) return { background: '#4a9e4a', color: '#fff' }
  if (val >= 3.7) return { background: '#8bc48b', color: '#1a1a1a' }
  if (val >= 3.3) return { background: '#e8c97a', color: '#1a1a1a' }
  if (val >= 3.0) return { background: '#e8956e', color: '#1a1a1a' }
  return { background: '#c0392b', color: '#fff' }
}

async function loadData() {
  const { data } = await getOverviewByLocation(store.selectedRunId || undefined)
  allRatings.value = data
}

onMounted(loadData)
watch(() => store.selectedRunId, loadData)
</script>

<style scoped>
.page-title { font-size: 22px; font-weight: 600; color: var(--text-primary); margin: 0 0 14px 0; }

/* View tabs */
.view-tabs { display: flex; gap: 6px; margin-bottom: 16px; border-bottom: 1px solid var(--border-color); padding-bottom: 0; }
.view-tab {
  padding: 7px 20px;
  border: none;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
  margin-bottom: -1px;
}
.view-tab:hover { color: var(--accent-blue-light); }
.view-tab.active { color: var(--accent-blue-light); border-bottom-color: var(--accent-blue-light); font-weight: 600; }

/* Controls */
.controls-row {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}
.region-tabs { display: flex; gap: 6px; }
.region-tab {
  padding: 5px 14px;
  border: 1px solid var(--border-color);
  border-radius: 16px;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}
.region-tab:hover { border-color: var(--accent-blue); color: var(--text-primary); }
.region-tab.active { background: var(--accent-blue); color: #fff; border-color: var(--accent-blue); }

/* ═══ Pivot Table ═══ */
.pivot-scroll { overflow-x: auto; }
.pivot-table { width: 100%; border-collapse: collapse; font-size: 13px; white-space: nowrap; }
.pivot-table th { padding: 10px 12px; text-align: center; color: var(--text-secondary); font-weight: 600; font-size: 12px; border-bottom: 1px solid var(--border-color); background: var(--bg-secondary); position: sticky; top: 0; }
.pivot-table td { padding: 8px 12px; text-align: center; border-bottom: 1px solid var(--border-color); }
.loc-col { text-align: left !important; min-width: 160px; font-weight: 500; color: var(--text-primary); }
.pivot-cell { display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: 600; font-size: 12px; min-width: 48px; }
.pivot-empty { color: var(--text-muted); }

/* ═══ Heatmap ═══ */
.heatmap-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.heatmap-table th { padding: 10px 12px; text-align: center; color: var(--text-secondary); font-weight: 500; font-size: 12px; border-bottom: 1px solid var(--border-color); }
.heatmap-table td { padding: 8px 12px; text-align: center; border-bottom: 1px solid var(--border-color); }
.company-col { text-align: left !important; width: 180px; font-weight: 500; }
.company-col.highlight { color: var(--accent-blue-light); }
.heat-cell { min-width: 60px; }
.heat-badge { display: inline-block; padding: 4px 14px; border-radius: 4px; font-weight: 600; font-size: 13px; min-width: 48px; }
.heat-na { color: var(--text-muted); }

/* Legend */
.legend { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 14px; padding: 8px 0; }
.legend-item { display: flex; align-items: center; gap: 5px; font-size: 11px; color: var(--text-secondary); }
.legend-swatch { width: 14px; height: 14px; border-radius: 3px; display: inline-block; }
</style>
