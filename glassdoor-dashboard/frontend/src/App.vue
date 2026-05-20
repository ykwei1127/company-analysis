<template>
  <div class="app-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-brand">Glassdoor</div>
      <nav class="sidebar-nav">
        <router-link to="/overview" class="nav-item" active-class="active">
          <el-icon class="nav-icon"><DataBoard /></el-icon> Overview
        </router-link>
        <router-link to="/comparison" class="nav-item" active-class="active">
          <el-icon class="nav-icon"><TrendCharts /></el-icon> Comparison
        </router-link>
        <router-link to="/locations" class="nav-item" active-class="active">
          <el-icon class="nav-icon"><Location /></el-icon> Locations
        </router-link>
        <router-link to="/scraper" class="nav-item" active-class="active">
          <el-icon class="nav-icon"><Monitor /></el-icon> Scraper
        </router-link>
        <router-link to="/settings" class="nav-item" active-class="active">
          <el-icon class="nav-icon"><Setting /></el-icon> Settings
        </router-link>
      </nav>
    </aside>

    <!-- Main content -->
    <main class="main-content">
      <header class="top-bar">
        <h2 class="app-title">Glassdoor Multi-Company Dashboard</h2>
        <div class="header-right">
          <el-select
            :model-value="dashboardStore.selectedRunId"
            @change="(val: string) => dashboardStore.selectRun(val)"
            placeholder="Select run"
            size="small"
            style="width: 180px"
          >
            <el-option
              v-for="run in dashboardStore.runs"
              :key="run.id"
              :label="run.label"
              :value="run.id"
            />
          </el-select>
          <el-popconfirm
            :title="`Delete run '${dashboardStore.selectedRunId}'?`"
            @confirm="dashboardStore.removeRun(dashboardStore.selectedRunId)"
            confirm-button-text="Delete"
            cancel-button-text="Cancel"
          >
            <template #reference>
              <el-button size="small" type="danger" plain :disabled="!dashboardStore.selectedRunId" title="Delete this run">
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-popconfirm>
          <button class="gear-btn" @click="themeStore.toggle()" :title="themeStore.mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'">&#9881;</button>
        </div>
      </header>

      <!-- Global Finder Status Bar -->
      <div v-if="finderStore.isRunning" class="finder-status-bar">
        <div class="finder-status-content">
          <el-icon class="is-loading" style="font-size: 16px;"><Loading /></el-icon>
          <span class="finder-status-title">{{ finderStore.statusTitle }}</span>
          <span class="finder-status-text">{{ finderStore.statusText }}</span>
          <span class="finder-status-meta">({{ finderStore.logs.length }} lines, {{ finderStore.elapsedTime }})</span>
          <el-button 
            size="small" 
            type="danger" 
            plain 
            @click="handleStopFinder"
            style="margin-left: 12px;"
          >
            Stop
          </el-button>
        </div>
      </div>

      <div class="page-content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { DataBoard, TrendCharts, Location, Monitor, Setting, Delete, Loading } from '@element-plus/icons-vue'
import { useDashboardStore } from './stores/dashboard'
import { useThemeStore } from './stores/theme'
import { useFinderStore } from './stores/finder'
import { stopFinder } from './api'

const dashboardStore = useDashboardStore()
const themeStore = useThemeStore()
const finderStore = useFinderStore()

async function handleStopFinder() {
  try {
    await stopFinder()
    finderStore.stop()
  } catch (e) {
    console.error('Failed to stop finder', e)
  }
}

onMounted(() => {
  dashboardStore.fetchRuns()
})
</script>

<style>
/* ── Dark Mode (default) ── */
:root,
[data-theme="dark"] {
  --bg-primary: #0A0A0A;
  --bg-secondary: #141414;
  --bg-card: #1A1A1A;
  --bg-card-hover: #222222;
  --bg-sidebar: #111111;
  --border-color: #2A2A2A;
  --text-primary: #F5F5F5;
  --text-secondary: #A0A0A0;
  --text-muted: #666666;
  --accent-blue: #409eff;
  --accent-blue-light: #66b1ff;
  --accent-green: #4ADE80;
  --accent-red: #F87171;
  --shadow: 0 2px 8px rgba(0,0,0,0.3);
}

/* ── Light Mode ── */
[data-theme="light"] {
  --bg-primary: #F5F5F7;
  --bg-secondary: #FFFFFF;
  --bg-card: #FFFFFF;
  --bg-card-hover: #F0F0F2;
  --bg-sidebar: #FAFAFA;
  --border-color: #E0E0E0;
  --text-primary: #1A1A1A;
  --text-secondary: #606060;
  --text-muted: #999999;
  --accent-blue: #409eff;
  --accent-blue-light: #0088E0;
  --accent-green: #16A34A;
  --accent-red: #DC2626;
  --shadow: 0 2px 8px rgba(0,0,0,0.08);
}

* { margin: 0; padding: 0; box-sizing: border-box; }

html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: background 0.3s, color 0.3s;
}

.app-layout {
  display: flex;
  min-height: 100vh;
}

/* Sidebar */
.sidebar {
  width: 180px;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  padding: 16px 0;
  flex-shrink: 0;
  transition: background 0.3s;
}

.sidebar-brand {
  padding: 0 20px 20px;
  font-size: 18px;
  font-weight: 700;
  color: var(--accent-blue-light);
}

.sidebar-nav { display: flex; flex-direction: column; gap: 2px; }

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.2s;
}

.nav-item:hover { color: var(--text-primary); background: var(--bg-card-hover); }
.nav-item.active { color: var(--accent-blue-light); background: rgba(64,158,255,0.08); border-left: 3px solid var(--accent-blue); }
.nav-icon { font-size: 16px; width: 20px; text-align: center; }

/* Main */
.main-content { flex: 1; display: flex; flex-direction: column; min-width: 0; }

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
  transition: background 0.3s;
}

.app-title { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.header-right { display: flex; align-items: center; gap: 12px; }
.gear-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  transition: color 0.2s;
}
.gear-btn:hover { color: var(--text-primary); }

.page-content { padding: 24px; flex: 1; overflow-y: auto; }

/* Global Finder Status Bar */
.finder-status-bar {
  background: var(--el-color-warning-light-9);
  border-bottom: 1px solid var(--el-color-warning-light-5);
  padding: 8px 24px;
}

.finder-status-content {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
}

.finder-status-title {
  font-weight: 600;
  color: var(--el-color-warning-dark-2);
}

.finder-status-text {
  color: var(--el-text-color-regular);
}

.finder-status-meta {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

/* Element Plus overrides using CSS vars */
.el-card { background: var(--bg-card) !important; border-color: var(--border-color) !important; color: var(--text-primary) !important; transition: background 0.3s; }
.el-card__header { border-bottom-color: var(--border-color) !important; color: var(--text-primary) !important; }
.el-table {
  --el-table-bg-color: var(--bg-card);
  --el-table-tr-bg-color: var(--bg-card);
  --el-table-header-bg-color: var(--bg-secondary);
  --el-table-border-color: var(--border-color);
  --el-table-text-color: var(--text-primary);
  --el-table-header-text-color: var(--text-secondary);
  --el-table-row-hover-bg-color: var(--bg-card-hover);
  --el-table-current-row-bg-color: var(--bg-card-hover);
  --el-fill-color-lighter: var(--bg-secondary);
}
.el-table th.el-table__cell { background-color: var(--bg-secondary) !important; }
.el-table td.el-table__cell { background-color: var(--bg-card) !important; }
.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell { background-color: var(--bg-secondary) !important; }
.el-table .el-table__row:hover > td.el-table__cell { background-color: var(--bg-card-hover) !important; }
.el-select { --el-fill-color-blank: var(--bg-card); --el-text-color-regular: var(--text-primary); --el-border-color: var(--border-color); }
.el-tag { border-color: var(--border-color); }
.el-input__wrapper { background-color: var(--bg-card) !important; box-shadow: 0 0 0 1px var(--border-color) inset !important; }
.el-input__inner { color: var(--text-primary) !important; }
.el-tabs__nav-wrap::after { background-color: var(--border-color) !important; }
.el-tabs__item { color: var(--text-secondary) !important; font-size: 14px; }
.el-tabs__item.is-active { color: var(--accent-blue-light) !important; }
.el-tabs__item:hover { color: var(--text-primary) !important; }
.el-tabs__active-bar { background-color: var(--accent-blue) !important; }
.el-tabs__content { color: var(--text-primary) !important; padding-top: 16px; }
.el-divider { border-top-color: var(--border-color) !important; }

/* ── Additional dark mode overrides ── */
/* el-alert */
.el-alert { background-color: var(--bg-secondary) !important; border-color: var(--border-color) !important; }
.el-alert .el-alert__title, .el-alert .el-alert__description { color: var(--text-primary) !important; }
.el-alert.el-alert--info { background-color: rgba(64, 158, 255, 0.08) !important; border-color: rgba(64, 158, 255, 0.2) !important; }
.el-alert.el-alert--success { background-color: rgba(74, 222, 128, 0.08) !important; border-color: rgba(74, 222, 128, 0.2) !important; }
.el-alert.el-alert--warning { background-color: rgba(230, 162, 60, 0.08) !important; border-color: rgba(230, 162, 60, 0.2) !important; }
.el-alert.el-alert--error { background-color: rgba(248, 113, 113, 0.08) !important; border-color: rgba(248, 113, 113, 0.2) !important; }

/* el-collapse */
.el-collapse { border-color: var(--border-color) !important; background: transparent !important; }
.el-collapse-item__header { background-color: var(--bg-secondary) !important; color: var(--text-primary) !important; border-color: var(--border-color) !important; }
.el-collapse-item__wrap { background-color: var(--bg-card) !important; border-color: var(--border-color) !important; }
.el-collapse-item__content { color: var(--text-primary) !important; }

/* el-checkbox */
.el-checkbox { color: var(--text-primary) !important; }
.el-checkbox__label { color: var(--text-primary) !important; }
.el-checkbox.is-bordered { border-color: var(--border-color) !important; background: var(--bg-card) !important; }
.el-checkbox.is-bordered.is-checked { border-color: var(--accent-blue) !important; }
.el-checkbox__inner { background-color: var(--bg-card) !important; border-color: var(--border-color) !important; }
.el-checkbox-group { color: var(--text-primary) !important; }

/* el-form */
.el-form-item__label { color: var(--text-secondary) !important; }

/* el-popconfirm / el-popover / el-tooltip */
.el-popover { background: var(--bg-card) !important; border-color: var(--border-color) !important; color: var(--text-primary) !important; }
.el-popover__title { color: var(--text-primary) !important; }

/* el-empty */
.el-empty__description p { color: var(--text-secondary) !important; }

/* el-switch label */
.el-switch__label { color: var(--text-secondary) !important; }

/* el-select dropdown */
.el-select-dropdown { background: var(--bg-card) !important; border-color: var(--border-color) !important; }
.el-select-dropdown__item { color: var(--text-primary) !important; background: var(--bg-card) !important; }
.el-select-dropdown__item:hover, .el-select-dropdown__item.hover { background: var(--bg-card-hover) !important; }
.el-select-v2__popper { background: var(--bg-card) !important; border-color: var(--border-color) !important; }
.el-select-v2__option-item { color: var(--text-primary) !important; }
.el-select-v2__option-item:hover { background: var(--bg-card-hover) !important; }
</style>
