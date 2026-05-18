<template>
  <div>
    <!-- View tabs -->
    <div class="view-tabs">
      <button class="view-tab" :class="{ active: viewMode === 'heatmap' }" @click="viewMode = 'heatmap'">Heatmap</button>
      <button class="view-tab" :class="{ active: viewMode === 'pivot' }" @click="viewMode = 'pivot'">Pivot Table</button>
      <button class="view-tab" :class="{ active: viewMode === 'detail' }" @click="viewMode = 'detail'">Detail</button>
    </div>

    <!-- Region tabs -->
    <div v-if="viewMode === 'heatmap'" class="controls-row">
      <div class="region-tabs">
        <button v-for="r in REGIONS" :key="r.key" class="region-tab" :class="{ active: selectedRegion === r.key }" @click="selectedRegion = r.key">
          {{ r.label }}
        </button>
      </div>
    </div>

    <!-- Heatmap View -->
    <div v-if="viewMode === 'heatmap'">
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
            <td v-for="dim in DIM_COLS" :key="dim.key" class="heat-cell" :style="row[dim.key] != null ? heatStyle(Number(row[dim.key])) : {}">
              {{ row[dim.key] != null ? Number(row[dim.key]).toFixed(1) : '—' }}
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
      <p v-if="REGION_NOTES[selectedRegion]" class="region-note">{{ REGION_NOTES[selectedRegion] }}</p>
    </div>

    <!-- Pivot Table View -->
    <div v-if="viewMode === 'pivot'">
      <el-card>
        <template #header><span>Pivot: Company x Location</span></template>
        <el-table :data="allRatings" stripe style="width: 100%" max-height="600">
          <el-table-column prop="company" label="Company" width="160" sortable fixed />
          <el-table-column prop="baseline_location" label="Location" width="180" sortable />
          <el-table-column prop="country" label="Country" width="140" sortable />
          <el-table-column prop="overall" label="Overall" width="80" align="center" sortable />
          <el-table-column prop="wlb" label="WLB" width="70" align="center" sortable />
          <el-table-column prop="culture" label="Culture" width="80" align="center" sortable />
          <el-table-column prop="career" label="Career" width="80" align="center" sortable />
          <el-table-column prop="salary" label="Salary" width="80" align="center" sortable />
          <el-table-column prop="management" label="Mgmt" width="75" align="center" sortable />
          <el-table-column prop="diversity" label="D&I" width="70" align="center" sortable />
          <el-table-column prop="recommend" label="Recommend%" width="110" align="center" sortable>
            <template #default="{ row }">
              {{ row.recommend != null ? row.recommend.toFixed(1) + '%' : 'N/A' }}
            </template>
          </el-table-column>
          <el-table-column prop="ceo_approval" label="CEO%" width="80" align="center" sortable>
            <template #default="{ row }">
              {{ row.ceo_approval != null ? row.ceo_approval.toFixed(1) + '%' : 'N/A' }}
            </template>
          </el-table-column>
          <el-table-column prop="total_reviews" label="Reviews" width="90" align="center" sortable />
        </el-table>
      </el-card>
    </div>

    <!-- Detail View -->
    <div v-if="viewMode === 'detail'">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>Detail View</span>
            <el-select v-model="detailCompany" placeholder="Filter company" clearable size="small" style="width: 200px">
              <el-option v-for="name in companyList" :key="name" :label="name" :value="name" />
            </el-select>
          </div>
        </template>
        <el-table :data="detailData" stripe style="width: 100%" max-height="600">
          <el-table-column prop="company" label="Company" width="160" sortable fixed />
          <el-table-column prop="baseline_location" label="Location" width="180" sortable />
          <el-table-column prop="country" label="Country" width="140" sortable />
          <el-table-column prop="overall" label="Overall" width="80" align="center" sortable />
          <el-table-column prop="wlb" label="WLB" width="70" align="center" sortable />
          <el-table-column prop="culture" label="Culture" width="80" align="center" sortable />
          <el-table-column prop="career" label="Career" width="80" align="center" sortable />
          <el-table-column prop="salary" label="Salary" width="80" align="center" sortable />
          <el-table-column prop="management" label="Mgmt" width="75" align="center" sortable />
          <el-table-column prop="diversity" label="D&I" width="70" align="center" sortable />
          <el-table-column prop="recommend" label="Recommend%" width="110" align="center" sortable>
            <template #default="{ row }">
              {{ row.recommend != null ? row.recommend.toFixed(1) + '%' : 'N/A' }}
            </template>
          </el-table-column>
          <el-table-column prop="ceo_approval" label="CEO%" width="80" align="center" sortable>
            <template #default="{ row }">
              {{ row.ceo_approval != null ? row.ceo_approval.toFixed(1) + '%' : 'N/A' }}
            </template>
          </el-table-column>
          <el-table-column prop="total_reviews" label="Reviews" width="90" align="center" sortable />
        </el-table>
      </el-card>
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
const viewMode = ref<'heatmap' | 'pivot' | 'detail'>('heatmap')
const selectedRegion = ref('north_america')
const detailCompany = ref('')

// Region definitions
const REGIONS = [
  { key: 'north_america', label: 'North America', countries: ['United States', 'Canada'] },
  { key: 'europe', label: 'Europe', countries: ['United Kingdom', 'Germany', 'France', 'Netherlands', 'Italy', 'Spain', 'Hungary'] },
  { key: 'asia', label: 'Asia', countries: ['Taiwan', 'Japan', 'South Korea', 'India', 'Singapore', 'Thailand', 'Indonesia', 'Malaysia', 'Philippines', 'China', 'United Arab Emirates'] },
  { key: 'south_america', label: 'South America', countries: ['Brazil', 'Chile'] },
  { key: 'oceania', label: 'Oceania', countries: ['Australia'] },
  { key: 'global', label: 'Global', countries: [] },
]

const REGION_NOTES: Record<string, string> = {
  north_america: 'North America: ASUS from Fremont + Markham offices. \u2605 row = ASUS. "\u2014" = no data.',
  asia: 'Asia: Taiwan data from Taiwan-wide page. \u2605 row = ASUS. "\u2014" = no data.',
  global: 'Global: Company-wide aggregate pages. \u2605 row = ASUS. "\u2014" = no data.',
}

// Dimension columns shown in the heatmap (excluding overall as separate concept)
const DIM_COLS: { key: DimensionKey; label: string }[] = [
  { key: 'wlb',        label: 'Work-life balance' },
  { key: 'culture',    label: 'Culture & values' },
  { key: 'career',     label: 'Career opportunities' },
  { key: 'salary',     label: 'Compensation' },
  { key: 'management', label: 'Senior management' },
  { key: 'diversity',  label: 'Diversity & inclusion' },
]

// Preferred company order (ASUS first, then alphabetical)
const COMPANY_ORDER = ['ASUS', 'Acer', 'Dell Technologies', 'HP Inc.', 'Lenovo', 'MSI', 'Trend Micro', 'NVIDIA', 'Google', 'TSMC']

const legend = [
  { label: '4.4+',    color: '#2d6a2d' },
  { label: '4.0\u20134.3', color: '#4a9e4a' },
  { label: '3.7\u20133.9', color: '#8bc48b' },
  { label: '3.3\u20133.6', color: '#e8c97a' },
  { label: '3.0\u20133.2', color: '#e8956e' },
  { label: '<3.0',    color: '#c0392b' },
]

const companyList = computed(() => [...new Set(allRatings.value.map(r => r.company))].sort())

const detailData = computed(() => {
  if (!detailCompany.value) return allRatings.value
  return allRatings.value.filter(r => r.company === detailCompany.value)
})

// Region-filtered ratings
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

// Unique companies in region, sorted by preferred order
const regionCompanies = computed(() => {
  const set = new Set(regionRatings.value.map(r => r.company))
  const ordered = COMPANY_ORDER.filter(c => set.has(c))
  const rest = [...set].filter(c => !COMPANY_ORDER.includes(c)).sort()
  return [...ordered, ...rest]
})

// Aggregate per company across multiple locations in the region (simple avg)
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

// Heatmap color helpers
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

/* View tabs (top-level) */
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

/* Controls row */
.controls-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
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

/* Heatmap table */
.heatmap-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.heatmap-table th { padding: 8px 10px; text-align: center; color: var(--text-secondary); font-weight: 500; font-size: 12px; border-bottom: 1px solid var(--border-color); }
.heatmap-table td { padding: 6px 10px; text-align: center; border-bottom: 1px solid var(--border-color); }
.company-col { text-align: left !important; width: 180px; font-weight: 500; }
.company-col.highlight { color: var(--accent-blue-light); }
.heat-cell { font-weight: 600; font-size: 13px; border-radius: 4px; min-width: 50px; }

/* Legend */
.legend { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 14px; padding: 8px 0; }
.legend-item { display: flex; align-items: center; gap: 5px; font-size: 11px; color: var(--text-secondary); }
.legend-swatch { width: 14px; height: 14px; border-radius: 3px; display: inline-block; }
.region-note { font-size: 11px; color: var(--text-secondary); margin-top: 8px; font-style: italic; }

.card-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
</style>
