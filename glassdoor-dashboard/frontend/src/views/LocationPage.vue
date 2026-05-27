<template>
  <div>
    <h3 class="page-title">Location Breakdown</h3>

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

    <!-- View tabs -->
    <div class="view-tabs">
      <button class="view-tab" :class="{ active: viewMode === 'heatmap' }" @click="viewMode = 'heatmap'">Heatmap</button>
      <button class="view-tab" :class="{ active: viewMode === 'pivot' }" @click="viewMode = 'pivot'">Pivot Table</button>
      <button v-if="categoryStore.isWeightedCategory" class="view-tab" :class="{ active: viewMode === 'matrix' }" @click="viewMode = 'matrix'">Region Matrix</button>
    </div>

    <!-- ═══════ Heatmap View ═══════ -->
    <div v-if="viewMode === 'heatmap'">
      <!-- Region tabs - only show for global brands category -->
      <div v-if="categoryStore.selectedCategory === 'brand_global'" class="controls-row">
        <div class="region-tabs">
          <button v-for="r in REGIONS" :key="r.key" class="region-tab" :class="{ active: selectedRegion === r.key }" @click="selectedRegion = r.key">
            {{ r.label }}
          </button>
        </div>
      </div>
      <!-- For Taiwan-only categories, show Taiwan indicator -->
      <div v-else class="controls-row">
        <div class="taiwan-indicator">
          <span class="taiwan-badge">Taiwan Data Only</span>
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
          <tr v-for="row in heatmapRows" :key="String(row.company)" :class="{ asus: row.company === 'ASUS' }">
            <td class="company-col" :class="{ highlight: row.company === 'ASUS' }">
              <span v-if="row.company === 'ASUS'" class="asus-star">★</span> {{ row.company }}
            </td>
            <td v-for="dim in DIM_COLS" :key="dim.key" class="heat-cell">
              <el-tooltip v-if="row[dim.key] != null" placement="top" :show-after="200">
                <template #content>
                  <div style="max-width: 320px; font-size: 12px;">
                    <div style="font-weight: 600; margin-bottom: 4px; border-bottom: 1px solid #666; padding-bottom: 4px;">
                      {{ row.company }} - {{ dim.label }}: {{ Number(row[dim.key]).toFixed(2) }}
                      <span v-if="categoryStore.selectedCategory === 'brand_global' && row[`${dim.key}_totalWeight`]">
                        (weighted avg)
                      </span>
                    </div>
                    <div style="color: #aaa; font-size: 11px; margin-bottom: 8px;">
                      Data sources ({{ (row[`${dim.key}_sources`] as HeatmapSource[]).length }} locations):
                    </div>
                    <div v-for="(src, idx) in (row[`${dim.key}_sources`] as HeatmapSource[]).slice(0, 8)" :key="idx"
                         style="display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 3px;">
                      <span>{{ src.location }}{{ src.country && src.country !== src.location ? ` (${src.country})` : '' }}</span>
                      <span style="color: #409EFF;">{{ src.value.toFixed(2) }}</span>
                      <span v-if="categoryStore.selectedCategory === 'brand_global'" style="color: #888; font-size: 10px;">
                        w:{{ src.weight || src.reviews }}
                      </span>
                    </div>
                    <div v-if="(row[`${dim.key}_sources`] as HeatmapSource[]).length > 8" style="color: #888; font-style: italic; margin-top: 4px;">
                      ... and {{ (row[`${dim.key}_sources`] as HeatmapSource[]).length - 8 }} more
                    </div>
                    <div v-if="categoryStore.selectedCategory === 'brand_global' && row[`${dim.key}_totalWeight`]
                              && (row[`${dim.key}_sources`] as HeatmapSource[]).length > 1"
                         style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #666; font-size: 11px; color: #aaa;">
                      <div>Weighted calculation:</div>
                      <div style="color: #67C23A;">
                        Σ(value × reviews) / Σ(reviews) = {{ Number(row[dim.key]).toFixed(2) }}
                      </div>
                      <div style="font-size: 10px; margin-top: 2px;">
                        Total reviews: {{ row[`${dim.key}_totalWeight`] }}
                      </div>
                    </div>
                  </div>
                </template>
                <span class="heat-badge" :style="heatStyle(Number(row[dim.key]))">
                  {{ Number(row[dim.key]).toFixed(1) }}
                </span>
              </el-tooltip>
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
                <td class="loc-col">{{ locationDisplayLabel[loc] || loc }}</td>
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

    <!-- ═══════ Region Matrix View (Global Brands only) ═══════ -->
    <div v-if="viewMode === 'matrix' && categoryStore.selectedCategory === 'brand_global'">
      <el-card>
        <template #header>
          <span style="font-weight: 600">Region Performance Matrix</span>
          <span style="margin-left: 8px; font-size: 12px; color: var(--text-secondary)">Compare companies across all regions</span>
        </template>

        <div class="matrix-scroll">
          <table class="matrix-table">
            <thead>
              <tr>
                <th class="company-col">Company</th>
                <th v-for="region in MATRIX_REGIONS" :key="region.key" class="region-col">
                  {{ region.label }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in matrixRows" :key="row.company" :class="{ asus: row.company === 'ASUS' }">
                <td class="company-col" :class="{ highlight: row.company === 'ASUS' }">
                  <span v-if="row.company === 'ASUS'" class="asus-star">★</span> {{ row.company }}
                </td>
                <td v-for="region in MATRIX_REGIONS" :key="region.key" class="score-cell">
                  <span v-if="typeof row[region.key] === 'number'" class="matrix-score" :style="heatStyle(row[region.key] as number)">
                    {{ (row[region.key] as number).toFixed(2) }}
                  </span>
                  <span v-else class="matrix-na">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { getOverviewByLocation, getOverviewByCategory } from '../api'
import { useDashboardStore } from '../stores/dashboard'
import { useCategoryStore } from '../stores/category'
import type { LocationRating, DimensionKey } from '../types'

const store = useDashboardStore()
const categoryStore = useCategoryStore()
const allRatings = ref<LocationRating[]>([])
const viewMode = ref<'pivot' | 'heatmap' | 'matrix'>('heatmap')
const selectedRegion = ref('north_america')
const pivotCompanyFilter = ref<string[]>([])
const pivotDimension = ref<DimensionKey>('overall')

// Region definitions - only used for brand_global category
const REGIONS = [
  { key: 'north_america', label: 'North America', countries: ['United States', 'Canada'] },
  { key: 'europe', label: 'Europe', countries: ['United Kingdom', 'Germany', 'France', 'Netherlands', 'Italy', 'Spain', 'Hungary'] },
  { key: 'asia', label: 'Asia', countries: ['Taiwan', 'Japan', 'South Korea', 'India', 'Singapore', 'Thailand', 'Indonesia', 'Malaysia', 'Philippines', 'China', 'United Arab Emirates'] },
  { key: 'south_america', label: 'South America', countries: ['Brazil', 'Chile'] },
  { key: 'oceania', label: 'Oceania', countries: ['Australia'] },
  { key: 'global', label: 'Global', countries: [] },
]

// For Taiwan-only categories, use simplified region
const TAIWAN_REGION = { key: 'taiwan', label: 'Taiwan', countries: ['Taiwan'] }

// Matrix regions (for brand_global category)
const MATRIX_REGIONS = [
  { key: 'north_america', label: 'North America' },
  { key: 'europe', label: 'Europe' },
  { key: 'asia', label: 'Asia' },
  { key: 'south_america', label: 'South America' },
  { key: 'oceania', label: 'Oceania' },
  { key: 'global', label: 'Global' },
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

// Map baseline_location → display label
// For country-mode entries, show the country name instead of the city baseline
const locationDisplayLabel = computed(() => {
  const map: Record<string, string> = {}
  for (const r of allRatings.value) {
    if (!r.baseline_location) continue
    if (map[r.baseline_location]) continue
    if (r.source_mode === 'country' && r.country && r.baseline_location.toLowerCase() !== 'global') {
      map[r.baseline_location] = r.country
    } else {
      map[r.baseline_location] = r.baseline_location
    }
  }
  return map
})

const getPivotValue = (loc: string, company: string): number | null => {
  const row = allRatings.value.find(r => r.company === company && r.baseline_location === loc)
  if (!row) return null
  const val = row[pivotDimension.value]
  return val != null ? val : null
}

// ═══════ Heatmap Logic ═══════
const regionRatings = computed(() => {
  // For Taiwan-only categories, filter to Taiwan data only
  if (categoryStore.selectedCategory !== 'brand_global') {
    return allRatings.value.filter(r =>
      r.country === 'Taiwan' ||
      r.baseline_location?.toLowerCase() === 'taiwan' ||
      r.baseline_location?.toLowerCase() === 'global'
    )
  }
  // For brand_global, filter by selected region
  const region = REGIONS.find(r => r.key === selectedRegion.value)
  if (!region) return []
  if (region.key === 'global') {
    return allRatings.value.filter(r =>
      !r.baseline_location || r.baseline_location.toLowerCase() === 'global'
    )
  }
  return allRatings.value.filter(r => {
    // Check if baseline_location matches region key (for weighted region data)
    if (r.baseline_location === region.key) return true
    // Or check if country is in region countries list
    return r.country && region.countries.includes(r.country)
  })
})

const regionCompanies = computed(() => {
  // 獲取當前類別的所有公司（即使沒有資料也要顯示）
  const categoryCompanies = categoryStore.currentCategory?.companies || []

  // 獲取有資料的公司，並進行大小寫不敏感的去重
  const companiesWithData = new Set<string>()
  const normalizedDataMap = new Map<string, string>() // normalized -> original

  for (const r of regionRatings.value) {
    const normalized = r.company.toLowerCase()
    if (!normalizedDataMap.has(normalized)) {
      normalizedDataMap.set(normalized, r.company)
      companiesWithData.add(r.company)
    }
  }

  // 合併類別公司和有資料的公司（使用標準化的類別公司名）
  const allCompanies = new Set<string>(categoryCompanies)

  // 添加有資料的公司，如果其標準化名稱不在類別公司中
  for (const dataCompany of companiesWithData) {
    const normalizedData = dataCompany.toLowerCase()
    const isInCategory = categoryCompanies.some(c => c.toLowerCase() === normalizedData)
    if (!isInCategory) {
      allCompanies.add(dataCompany)
    }
  }

  // 排序：ASUS 第一，其他按字母順序
  const sorted = [...allCompanies].sort((a, b) => {
    if (a === 'ASUS') return -1
    if (b === 'ASUS') return 1
    return a.localeCompare(b)
  })

  return sorted
})

interface HeatmapSource {
  location: string
  country: string | null
  value: number
  reviews: number
  sourceMode: string
  weight?: number
}

interface HeatmapRow {
  company: string
  [key: string]: number | null | string | HeatmapSource[]
}

const heatmapRows = computed<HeatmapRow[]>(() => {
  // Taiwan-only 類別：只顯示 Taiwan 地點資料，每間公司一行
  if (categoryStore.selectedCategory !== 'brand_global') {
    // 獲取類別定義的所有公司
    const categoryCompanies = categoryStore.currentCategory?.companies || []
    // 排序：ASUS 第一
    const sortedCompanies = [...categoryCompanies].sort((a, b) => {
      if (a === 'ASUS') return -1
      if (b === 'ASUS') return 1
      return a.localeCompare(b)
    })
    // 為每個公司創建一行，只取 Taiwan 資料
    return sortedCompanies.map(company => {
      // 找出該公司的 Taiwan 資料（排除 Global）
      const taiwanRows = regionRatings.value.filter(r =>
        r.company.toLowerCase() === company.toLowerCase() &&
        r.baseline_location &&
        r.baseline_location.toLowerCase() !== 'global' &&
        (r.country === 'Taiwan' || r.baseline_location.toLowerCase().includes('taiwan'))
      )
      const row: HeatmapRow = { company }
      for (const dim of DIM_COLS) {
        // Taiwan 類別：取第一筆 Taiwan 資料（應該只有一筆）
        const r = taiwanRows.find(r => r[dim.key] != null)
        row[dim.key] = r ? r[dim.key] as number : null
        row[`${dim.key}_sources`] = r ? [{
          location: r.baseline_location || 'Taiwan',
          country: r.country,
          value: r[dim.key] as number,
          reviews: r.total_reviews || 0,
          sourceMode: r.source_mode || 'unknown'
        }] : []
      }
      return row
    })
  }
  // Global Brands：按區域加權平均，並保存原始地點資料
  return regionCompanies.value.map(company => {
    // 從 allRatings 獲取該公司在該區域的所有原始地點資料
    const region = REGIONS.find(r => r.key === selectedRegion.value)
    const rawRows = region
      ? allRatings.value.filter(r =>
          r.company.toLowerCase() === company.toLowerCase() &&
          (r.country && region.countries.includes(r.country))
        )
      : []

    const rows = regionRatings.value.filter(r =>
      r.company.toLowerCase() === company.toLowerCase()
    )
    const row: HeatmapRow = { company }
    for (const dim of DIM_COLS) {
      const validRows = rows.filter(r => r[dim.key] != null)
      const vals = validRows.map(r => r[dim.key] as number)
      const avg = vals.length ? parseFloat((vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(2)) : null
      row[dim.key] = avg

      // 保存原始地點資料和加權計算詳情
      const rawSources: HeatmapSource[] = rawRows
        .filter((r: LocationRating) => r[dim.key] != null)
        .map((r: LocationRating) => ({
          location: r.baseline_location || r.country || 'Unknown',
          country: r.country,
          value: r[dim.key] as number,
          reviews: r.total_reviews || 0,
          sourceMode: r.source_mode || 'unknown',
          weight: r.total_reviews || 0 // 用於加權計算
        }))

      // 計算總權重和加權平均
      const totalWeight = rawSources.reduce((sum, s) => sum + (s.weight || 0), 0)
      const weightedAvg = totalWeight > 0
        ? rawSources.reduce((sum, s) => sum + s.value * (s.weight || 0), 0) / totalWeight
        : null

      row[`${dim.key}_sources`] = rawSources
      row[`${dim.key}_weightedAvg`] = weightedAvg
      row[`${dim.key}_totalWeight`] = totalWeight
    }
    return row
  })
})

// Matrix data for region comparison
interface MatrixRow {
  company: string
  [key: string]: string | number | null
}

const matrixRows = computed<MatrixRow[]>(() => {
  const companies = categoryStore.currentCategory?.companies || []
  return companies.map(company => {
    const row: MatrixRow = { company }
    for (const region of MATRIX_REGIONS) {
      // Find data for this company in this region from allRatings
      const rating = allRatings.value.find(r =>
        r.company === company &&
        (r.baseline_location === region.key || r.country === region.key)
      )
      row[region.key] = rating?.overall ?? null
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
  // 獲取原始地點數據（用於 tooltip 顯示詳情）
  const { data: locationData } = await getOverviewByLocation(store.selectedRunId || undefined)
  
  // 過濾類別中的公司
  const categoryCompanies = categoryStore.currentCategory?.companies || []
  const normalizedCompanies = categoryCompanies.map(c => c.toLowerCase())
  allRatings.value = locationData.filter((r: LocationRating) =>
    normalizedCompanies.includes(r.company.toLowerCase())
  )
}

onMounted(loadData)
watch(() => store.selectedRunId, loadData)
watch(() => categoryStore.selectedCategory, () => {
  // 當切換到非加權類別時，如果當前在 Region Matrix，自動切換到 Heatmap
  if (!categoryStore.isWeightedCategory && viewMode.value === 'matrix') {
    viewMode.value = 'heatmap'
  }
  loadData()
})
</script>

<style scoped>
.page-title { font-size: 22px; font-weight: 600; color: var(--text-primary); margin: 0 0 14px 0; }

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

/* Taiwan indicator for non-global categories */
.taiwan-indicator {
  display: flex;
  align-items: center;
}
.taiwan-badge {
  background: var(--accent-blue);
  color: #fff;
  padding: 5px 14px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 500;
}

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
.heatmap-table tr:hover { background: var(--bg-card-hover); }
.heatmap-table tr.asus { background: rgba(64,158,255,0.08); }
.heatmap-table tr.asus:hover { background: rgba(64,158,255,0.15); }
.company-col { text-align: left !important; width: 180px; font-weight: 500; }
.company-col.highlight { color: var(--accent-blue-light); }
.heat-cell { min-width: 60px; }
.heat-badge { display: inline-block; padding: 4px 14px; border-radius: 4px; font-weight: 600; font-size: 13px; min-width: 48px; }
.heat-na { color: var(--text-muted); }

/* Legend */
.legend { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 14px; padding: 8px 0; }
.legend-item { display: flex; align-items: center; gap: 5px; font-size: 11px; color: var(--text-secondary); }
.legend-swatch { width: 14px; height: 14px; border-radius: 3px; display: inline-block; }

/* ═══ Region Matrix ═══ */
.matrix-scroll { overflow-x: auto; }
.matrix-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.matrix-table th { padding: 12px 8px; text-align: center; color: var(--text-secondary); font-weight: 600; font-size: 12px; border-bottom: 2px solid var(--border-color); background: var(--bg-secondary); white-space: nowrap; }
.matrix-table td { padding: 10px 8px; text-align: center; border-bottom: 1px solid var(--border-color); }
.matrix-table tr:hover { background: var(--bg-card-hover); }
.matrix-table tr.asus { background: rgba(64,158,255,0.08); }
.matrix-table tr.asus:hover { background: rgba(64,158,255,0.15); }
.matrix-table .region-col { min-width: 100px; }
.matrix-score { display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: 600; font-size: 13px; min-width: 52px; }
.matrix-na { color: var(--text-muted); }
.asus-star { color: gold; margin-right: 4px; }
</style>
