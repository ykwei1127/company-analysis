import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const getRuns = () => api.get('/runs')
export const getOverview = (run?: string) => api.get('/overview', { params: { run } })
export const getOverviewByLocation = (run?: string) => api.get('/overview/by-location', { params: { run } })
export const getRatings = (run?: string, company?: string) => api.get('/ratings', { params: { run, company } })

// Scraper
export const getScraperStatus = () => api.get('/scraper/status')
export const startScraper = (ports: string, mode: string) => api.post('/scraper/start', null, { params: { ports, mode } })
export const stopScraper = () => api.post('/scraper/stop')
export const checkLogin = (port: number) => api.get('/scraper/check-login', { params: { port } })
export const getChromeStatus = () => api.get('/scraper/chrome-status')
export const launchChrome = (port: number) => api.post('/scraper/launch-chrome', null, { params: { port } })
export const closeAllChrome = () => api.post('/scraper/close-chrome')
