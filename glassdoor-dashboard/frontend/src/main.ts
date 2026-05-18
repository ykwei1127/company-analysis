import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'

import App from './App.vue'

const routes = [
  { path: '/', redirect: '/overview' },
  { path: '/overview', component: () => import('./views/OverviewPage.vue') },
  { path: '/comparison', component: () => import('./views/ComparisonPage.vue') },
  { path: '/locations', component: () => import('./views/LocationPage.vue') },
  { path: '/scraper', component: () => import('./views/ScraperPage.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
