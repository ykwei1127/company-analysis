import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const getRuns = () => api.get('/runs')
export const deleteRun = (runId: string) => api.delete(`/runs/${runId}`)
export const getRunMetadata = (run: string) => api.get(`/overview/run-metadata?run=${run}`)
export const getOverview = (run?: string) => api.get('/overview', { params: { run } })
export const getOverviewByLocation = (run?: string) => api.get('/overview/by-location', { params: { run } })
export const getRatings = (run?: string, company?: string) => api.get('/ratings', { params: { run, company } })

// Scraper
export const getScraperStatus = () => api.get('/scraper/status')
export const startScraper = (ports: string, task: string, source_mode?: string, companies?: string) => api.post('/scraper/start', null, { params: { ports, task, source_mode, companies } })
export const stopScraper = () => api.post('/scraper/stop')
export const checkLogin = (port: number) => api.get('/scraper/check-login', { params: { port } })
export const getChromeStatus = () => api.get('/scraper/chrome-status')
export const launchChrome = (port: number) => api.post('/scraper/launch-chrome', null, { params: { port } })
export const closeAllChrome = () => api.post('/scraper/close-chrome')

// Settings
export const getConfig = () => api.get('/settings/config')
export const updateConfig = (payload: any) => api.post('/settings/config', payload)
export const getCompanies = () => api.get('/settings/companies')
export const removeCompany = (filename: string) => api.delete(`/settings/companies/${filename}`)
export const getCompaniesToMatch = () => api.get('/settings/companies-to-match')
export const addCompanyToMatch = (name: string) => api.post('/settings/companies-to-match/add', null, { params: { name } })
export const removeCompanyToMatch = (name: string) => api.post('/settings/companies-to-match/remove', null, { params: { name } })
export const getBaseline = (file?: string) => api.get('/settings/baseline', { params: file ? { file } : undefined })
export const runFinderOffice = (companies?: string[]) => api.post('/settings/finder/office', null, { params: { companies: companies?.join(',') } })
export const runFinderCountry = (companies?: string[]) => api.post('/settings/finder/country', null, { params: { companies: companies?.join(',') } })
export const runFinderCity = (companies?: string[]) => api.post('/settings/finder/city', null, { params: { companies: companies?.join(',') } })
export const runFinderScan = (companies?: string[]) => api.post('/settings/finder/scan', null, { params: { companies: companies?.join(',') } })
export const getFinderStatus = () => api.get('/settings/finder/status')
export const stopFinder = () => api.post('/settings/finder/stop')
