export default function RecentTrips({ trips, onSelect }) {
  if (!trips || trips.length === 0) return null

  return (
    <div className="recent-trips">
      <h2>Recent Trips</h2>
      <ul>
        {trips.map((trip) => (
          <li key={trip.id}>
            <button type="button" onClick={() => onSelect(trip)}>
              <span>
                {trip.current_location} → {trip.pickup_location} → {trip.dropoff_location}
              </span>
              <span className="recent-trips__meta">
                {trip.current_cycle_used}h used · {new Date(trip.created_at).toLocaleString()}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
