import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

const STATIC_MODE = import.meta.env.VITE_STATIC_MODE === 'true'
const STATIC_BASE = import.meta.env.BASE_URL + 'static-data'

// In static mode, load pre-exported JSON files instead of calling the backend
async function staticGet(path: string) {
  const { data } = await axios.get(path)
  return { data }
}

function staticRunPath(run?: string) {
  const id = run || 'latest'
  return `${STATIC_BASE}/${id}`
}

const noop = () => Promise.resolve({ data: null })

export const getRuns = () =>
  STATIC_MODE ? staticGet(`${STATIC_BASE}/runs.json`) : api.get('/runs')

export const deleteRun = (_runId: string) =>
  STATIC_MODE ? noop() : api.delete(`/runs/${_runId}`)

export const getRunMetadata = (run: string) =>
  STATIC_MODE ? staticGet(`${staticRunPath(run)}/metadata.json`) : api.get(`/overview/run-metadata?run=${run}`)

export const getOverview = (run?: string) =>
  STATIC_MODE ? staticGet(`${staticRunPath(run)}/overview.json`) : api.get('/overview', { params: { run } })

export const getOverviewByLocation = (run?: string) =>
  STATIC_MODE ? staticGet(`${staticRunPath(run)}/by-location.json`) : api.get('/overview/by-location', { params: { run } })

export const getRatings = (run?: string, company?: string) =>
  STATIC_MODE ? staticGet(`${staticRunPath(run)}/by-location.json`) : api.get('/ratings', { params: { run, company } })

// Scraper — not available in static mode
export const getScraperStatus = () => STATIC_MODE ? noop() : api.get('/scraper/status')
export const startScraper = (_ports: string, _task: string, _source_mode?: string, _companies?: string) =>
  STATIC_MODE ? noop() : api.post('/scraper/start', null, { params: { ports: _ports, task: _task, source_mode: _source_mode, companies: _companies } })
export const stopScraper = () => STATIC_MODE ? noop() : api.post('/scraper/stop')
export const checkLogin = (_port: number) => STATIC_MODE ? noop() : api.get('/scraper/check-login', { params: { port: _port } })
export const getChromeStatus = () => STATIC_MODE ? noop() : api.get('/scraper/chrome-status')
export const launchChrome = (_port: number) => STATIC_MODE ? noop() : api.post('/scraper/launch-chrome', null, { params: { port: _port } })
export const closeAllChrome = () => STATIC_MODE ? noop() : api.post('/scraper/close-chrome')

// Settings — not available in static mode
export const getConfig = () => STATIC_MODE ? noop() : api.get('/settings/config')
export const updateConfig = (_payload: any) => STATIC_MODE ? noop() : api.post('/settings/config', _payload)
export const getCompanies = () => STATIC_MODE ? Promise.resolve({ data: { companies: [] } }) : api.get('/settings/companies')
export const removeCompany = (_filename: string) => STATIC_MODE ? noop() : api.delete(`/settings/companies/${_filename}`)
export const getCompaniesToMatch = () => STATIC_MODE ? noop() : api.get('/settings/companies-to-match')
export const addCompanyToMatch = (_name: string) => STATIC_MODE ? noop() : api.post('/settings/companies-to-match/add', null, { params: { name: _name } })
export const removeCompanyToMatch = (_name: string) => STATIC_MODE ? noop() : api.post('/settings/companies-to-match/remove', null, { params: { name: _name } })
export const getBaseline = (_file?: string) => STATIC_MODE ? noop() : api.get('/settings/baseline', { params: _file ? { file: _file } : undefined })
export const runFinderOffice = (_companies?: string[]) => STATIC_MODE ? noop() : api.post('/settings/finder/office', null, { params: { companies: _companies?.join(',') } })
export const runFinderCountry = (_companies?: string[]) => STATIC_MODE ? noop() : api.post('/settings/finder/country', null, { params: { companies: _companies?.join(',') } })
export const runFinderCity = (_companies?: string[]) => STATIC_MODE ? noop() : api.post('/settings/finder/city', null, { params: { companies: _companies?.join(',') } })
export const runFinderScan = (_companies?: string[]) => STATIC_MODE ? noop() : api.post('/settings/finder/scan', null, { params: { companies: _companies?.join(',') } })
export const getFinderStatus = () => STATIC_MODE ? noop() : api.get('/settings/finder/status')
export const stopFinder = () => STATIC_MODE ? noop() : api.post('/settings/finder/stop')

