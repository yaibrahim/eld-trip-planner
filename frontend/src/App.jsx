import { useEffect, useState } from 'react'
import TripForm from './components/TripForm'
import RouteMap from './components/RouteMap'
import TripSummary from './components/TripSummary'
import DailyLogSheet from './components/DailyLogSheet'
import RecentTrips from './components/RecentTrips'
import ErrorBoundary from './components/ErrorBoundary'
import { planTrip, fetchRecentTrips, apiDocsUrl } from './api'
import './App.css'

export default function App() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [recentTrips, setRecentTrips] = useState([])

  useEffect(() => {
    fetchRecentTrips().then(setRecentTrips).catch(() => {})
  }, [])

  async function handleSubmit(payload) {
    setLoading(true)
    setError(null)
    try {
      const data = await planTrip(payload)
      setResult(data)
      fetchRecentTrips().then(setRecentTrips).catch(() => {})
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong planning this trip. Please check the locations and try again.')
    } finally {
      setLoading(false)
    }
  }

  function handleSelectRecent(trip) {
    setResult({ id: trip.id, ...trip.result })
    setError(null)
  }

  return (
    <div className="app">
      <header className="app__header">
        <div>
          <h1>ELD Trip Planner</h1>
          <p>Property-carrying driver · 70hr/8-day cycle · no adverse driving conditions</p>
        </div>
        <a className="app__docs-link" href={apiDocsUrl()} target="_blank" rel="noreferrer">
          API Docs
        </a>
      </header>

      <div className="app__layout">
        <aside className="app__sidebar">
          <TripForm onSubmit={handleSubmit} loading={loading} />
          {error && <div className="error-banner">{error}</div>}
          <RecentTrips trips={recentTrips} onSelect={handleSelectRecent} />
        </aside>

        <main className="app__main">
          {!result && !loading && (
            <div className="empty-state">
              Enter a current location, pickup, dropoff and your current cycle hours used to generate a route and
              ELD daily logs.
            </div>
          )}

          {result && (
            <ErrorBoundary key={result.id ?? result.summary?.start_time}>
              <RouteMap waypoints={result.waypoints} geometry={result.route.geometry} stops={result.stops} />
              <TripSummary summary={result.summary} stops={result.stops} />
              <section className="daily-logs">
                <h2>Daily Log Sheets</h2>
                {result.daily_logs.map((day, i) => (
                  <DailyLogSheet key={day.date} day={day} dayIndex={i} />
                ))}
              </section>
            </ErrorBoundary>
          )}
        </main>
      </div>
    </div>
  )
}
