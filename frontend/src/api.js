import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

const client = axios.create({ baseURL })

export async function planTrip(payload) {
  const { data } = await client.post('/trips/plan/', payload)
  return data
}

export async function fetchRecentTrips() {
  const { data } = await client.get('/trips/')
  return data
}

export function apiDocsUrl() {
  return `${baseURL.replace(/\/api\/?$/, '')}/api/docs/`
}

export async function suggestLocations(query, signal) {
  const { data } = await client.get('/geocode/suggest/', { params: { q: query }, signal })
  return data
}

export async function reverseGeocode(lat, lon) {
  const { data } = await client.get('/geocode/reverse/', { params: { lat, lon } })
  return data.display_name
}
