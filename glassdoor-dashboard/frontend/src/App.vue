<template>
  <div class="app-layout dark">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-brand">Glassdoor</div>
      <nav class="sidebar-nav">
        <router-link to="/overview" class="nav-item" active-class="active">
          <span class="nav-icon">&#9776;</span> Overview
        </router-link>
        <router-link to="/comparison" class="nav-item" active-class="active">
          <span class="nav-icon">&#8644;</span> Comparison
        </router-link>
        <router-link to="/locations" class="nav-item" active-class="active">
          <span class="nav-icon">&#9873;</span> Locations
        </router-link>
        <router-link to="/scraper" class="nav-item" active-class="active">
          <span class="nav-icon">&#9881;</span> Scraper
        </router-link>
      </nav>
    </aside>

    <!-- Main content -->
    <main class="main-content">
      <header class="top-bar">
        <h2 class="app-title">Glassdoor Multi-Company Dashboard</h2>
        <div class="run-selector">
          <el-select
            :model-value="store.selectedRunId"
            @change="(val: string) => store.selectRun(val)"
            placeholder="Select run"
            size="small"
            style="width: 180px"
          >
            <el-option
              v-for="run in store.runs"
              :key="run.id"
              :label="run.label"
              :value="run.id"
            />
          </el-select>
        </div>
      </header>
      <div class="page-content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useDashboardStore } from './stores/dashboard'

const store = useDashboardStore()

onMounted(() => {
  store.fetchRuns()
})
</script>

<style>
:root {
  --bg-primary: #0d0d0d;
  --bg-secondary: #141414;
  --bg-card: #1a1a1a;
  --text-primary: #e0e0e0;
  --text-secondary: #888;
  --border-color: #2a2a2a;
  --accent-blue: #409eff;
  --accent-blue-light: #66b1ff;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.app-layout {
  display: flex;
  min-height: 100vh;
}

/* Sidebar */
.sidebar {
  width: 180px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  padding: 16px 0;
  flex-shrink: 0;
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

.nav-item:hover { color: var(--text-primary); background: rgba(255,255,255,0.04); }
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
}

.app-title { font-size: 16px; font-weight: 600; }

.page-content { padding: 24px; flex: 1; overflow-y: auto; }

/* Element Plus dark overrides */
.el-card { background: var(--bg-card) !important; border-color: var(--border-color) !important; color: var(--text-primary) !important; }
.el-card__header { border-bottom-color: var(--border-color) !important; }
.el-table { --el-table-bg-color: var(--bg-card); --el-table-tr-bg-color: var(--bg-card); --el-table-header-bg-color: #1f1f1f; --el-table-border-color: var(--border-color); --el-table-text-color: var(--text-primary); --el-table-header-text-color: var(--text-secondary); }
.el-select { --el-fill-color-blank: var(--bg-card); --el-text-color-regular: var(--text-primary); --el-border-color: var(--border-color); }
</style>
