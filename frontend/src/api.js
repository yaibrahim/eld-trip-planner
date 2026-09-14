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
