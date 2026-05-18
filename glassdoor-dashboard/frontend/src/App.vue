<template>
  <div class="app-layout">
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
        <div class="header-right">
          <span class="header-quarter">{{ currentQuarter }}</span>
          <button class="gear-btn" @click="themeStore.toggle()" :title="themeStore.mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'">&#9881;</button>
        </div>
      </header>
      <div class="page-content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useDashboardStore } from './stores/dashboard'
import { useThemeStore } from './stores/theme'

const dashboardStore = useDashboardStore()
const themeStore = useThemeStore()

const currentQuarter = computed(() => {
  const now = new Date()
  const q = Math.ceil((now.getMonth() + 1) / 3)
  return `${now.getFullYear()} Q${q}`
})

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
.header-quarter { font-size: 13px; color: var(--text-secondary); }
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

/* Element Plus overrides using CSS vars */
.el-card { background: var(--bg-card) !important; border-color: var(--border-color) !important; color: var(--text-primary) !important; transition: background 0.3s; }
.el-card__header { border-bottom-color: var(--border-color) !important; color: var(--text-primary) !important; }
.el-table { --el-table-bg-color: var(--bg-card); --el-table-tr-bg-color: var(--bg-card); --el-table-header-bg-color: var(--bg-secondary); --el-table-border-color: var(--border-color); --el-table-text-color: var(--text-primary); --el-table-header-text-color: var(--text-secondary); }
.el-table .el-table__row:hover > td { background: var(--bg-card-hover) !important; }
.el-select { --el-fill-color-blank: var(--bg-card); --el-text-color-regular: var(--text-primary); --el-border-color: var(--border-color); }
.el-tag { border-color: var(--border-color); }
.el-input__wrapper { background-color: var(--bg-card) !important; box-shadow: 0 0 0 1px var(--border-color) inset !important; }
.el-input__inner { color: var(--text-primary) !important; }
</style>
