<template>
  <div>
    <h3 class="page-title">Overview</h3>

    <!-- KPI Cards -->
    <div class="kpi-row">
      <div class="kpi-card" v-for="kpi in kpis" :key="kpi.label">
        <div class="kpi-value">{{ kpi.value }}</div>
        <div class="kpi-label">{{ kpi.label }}</div>
      </div>
    </div>

    <!-- Bar Chart: Overall Rating -->
    <el-card style="margin-bottom: 20px">
      <template #header><span>Company Overall Rating Rankings</span></template>
      <v-chart :option="barOption" style="height: 350px" autoresize />
    </el-card>

    <!-- Company Summary Table -->
    <el-card>
      <template #header><span>Company Summary</span></template>
      <el-table :data="companies" stripe style="width: 100%" :default-sort="{ prop: 'overall', order: 'descending' }">
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
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { getOverview } from '../api'
import { useDashboardStore } from '../stores/dashboard'
import { useThemeStore } from '../stores/theme'
import type { CompanyOverview } from '../types'

use([BarChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const store = useDashboardStore()
const themeStore = useThemeStore()
const companies = ref<CompanyOverview[]>([])

const kpis = computed(() => {
  const n = companies.value.length
  if (!n) return []
  const avgOverall = companies.value.reduce((s: number, c: CompanyOverview) => s + (c.overall || 0), 0) / n
  const top = companies.value[0]
  return [
    { label: 'Companies', value: n },
    { label: 'Avg Overall', value: avgOverall.toFixed(2) },
    { label: 'Top Rated', value: top?.company || '-' },
  ]
})

const barOption = computed(() => {
  const sorted = [...companies.value].sort((a, b) => (b.overall || 0) - (a.overall || 0))
  const isDark = themeStore.mode === 'dark'
  const textColor = isDark ? '#A0A0A0' : '#606060'
  const gridColor = isDark ? '#2A2A2A' : '#E0E0E0'

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: isDark ? '#1A1A1A' : '#FFF',
      borderColor: isDark ? '#2A2A2A' : '#E0E0E0',
      textStyle: { color: isDark ? '#F5F5F5' : '#1A1A1A' },
    },
    grid: { left: 140, right: 50, top: 10, bottom: 30 },
    xAxis: { type: 'value', min: 2, max: 5, axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor } } },
    yAxis: { type: 'category', data: sorted.map(c => c.company).reverse(), axisLabel: { color: textColor, fontSize: 12 } },
    series: [{
      type: 'bar',
      data: sorted.map(c => c.overall || 0).reverse(),
      barWidth: 18,
      itemStyle: { color: '#409eff', borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: 'right', color: textColor, fontSize: 11, formatter: (p: any) => p.value?.toFixed(1) },
    }],
  }
})

async function loadData() {
  const { data } = await getOverview(store.selectedRunId || undefined)
  companies.value = data
}

onMounted(loadData)
watch(() => store.selectedRunId, loadData)
</script>

<style scoped>
.page-title { font-size: 22px; font-weight: 600; color: var(--text-primary); margin: 0 0 14px 0; }

.kpi-row { display: flex; gap: 16px; margin-bottom: 20px; }
.kpi-card {
  flex: 1;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px 20px;
}
.kpi-value { font-size: 24px; font-weight: 700; color: var(--accent-blue-light); }
.kpi-label { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }
</style>
