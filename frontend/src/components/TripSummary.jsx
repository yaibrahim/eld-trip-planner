export default function TripSummary({ summary, stops }) {
  return (
    <div className="trip-summary">
      <h2>Trip Summary</h2>
      <div className="trip-summary__stats">
        <Stat label="Distance" value={`${summary.total_distance_miles} mi`} />
        <Stat label="Driving time" value={`${summary.total_driving_hours} hrs`} />
        <Stat label="Total trip duration" value={`${summary.total_trip_duration_hours} hrs`} />
        <Stat label="Days" value={summary.num_days} />
        <Stat label="Fuel stops" value={summary.fuel_stops} />
        <Stat label="30-min breaks" value={summary.rest_breaks} />
        <Stat label="Resets/restarts" value={summary.reset_stops} />
      </div>

      <h3>Stops &amp; Rests</h3>
      <ul className="stops-list">
        {stops.map((s, i) => (
          <li key={i}>
            <span className="stops-list__label">{s.label}</span>
            <span className="stops-list__time">
              {new Date(s.start).toLocaleString()} &rarr; {new Date(s.end).toLocaleString()} ({s.duration_hours}h)
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div className="stat">
      <div className="stat__value">{value}</div>
      <div className="stat__label">{label}</div>
    </div>
  )
}
