import { MapContainer, TileLayer, Polyline, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const COLORS = {
  current: '#2563eb',
  pickup: '#16a34a',
  dropoff: '#dc2626',
  'Fuel stop': '#f59e0b',
  'Required 30-minute break': '#7c3aed',
  '10-hour rest (daily reset)': '#0891b2',
  '34-hour restart (70-hour cycle reached)': '#4338ca',
}

function pin(color, label) {
  return L.divIcon({
    className: 'trip-marker',
    html: `<div class="trip-marker__dot" style="background:${color}" title="${label}"></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  })
}

export default function RouteMap({ waypoints, geometry, stops }) {
  if (!geometry || geometry.length === 0) return null

  const lats = geometry.map((p) => p[0])
  const lons = geometry.map((p) => p[1])
  const bounds = [
    [Math.min(...lats), Math.min(...lons)],
    [Math.max(...lats), Math.max(...lons)],
  ]

  const legendItems = [
    { label: 'Current', color: COLORS.current },
    { label: 'Pickup', color: COLORS.pickup },
    { label: 'Dropoff', color: COLORS.dropoff },
    { label: 'Fuel stop', color: COLORS['Fuel stop'] },
    { label: '30-min break', color: COLORS['Required 30-minute break'] },
    { label: '10-hr rest', color: COLORS['10-hour rest (daily reset)'] },
    { label: '34-hr restart', color: COLORS['34-hour restart (70-hour cycle reached)'] },
  ]

  return (
    <div className="route-map-wrap">
      <MapContainer bounds={bounds} boundsOptions={{ padding: [30, 30] }} className="route-map" scrollWheelZoom={true}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Polyline positions={geometry} pathOptions={{ color: '#2563eb', weight: 4, opacity: 0.8 }} />

        <Marker position={[waypoints.current.lat, waypoints.current.lon]} icon={pin(COLORS.current, 'Current')}>
          <Popup>Current: {waypoints.current.label}</Popup>
        </Marker>
        <Marker position={[waypoints.pickup.lat, waypoints.pickup.lon]} icon={pin(COLORS.pickup, 'Pickup')}>
          <Popup>Pickup: {waypoints.pickup.label}</Popup>
        </Marker>
        <Marker position={[waypoints.dropoff.lat, waypoints.dropoff.lon]} icon={pin(COLORS.dropoff, 'Dropoff')}>
          <Popup>Dropoff: {waypoints.dropoff.label}</Popup>
        </Marker>

        {stops.map((stop, i) =>
          stop.lat != null ? (
            <Marker key={i} position={[stop.lat, stop.lon]} icon={pin(COLORS[stop.label] || '#64748b', stop.label)}>
              <Popup>
                <strong>{stop.label}</strong>
                <br />
                {new Date(stop.start).toLocaleString()} &rarr; {new Date(stop.end).toLocaleString()}
                <br />
                Duration: {stop.duration_hours}h
              </Popup>
            </Marker>
          ) : null
        )}
      </MapContainer>
      <div className="route-map-legend">
        {legendItems.map((item) => (
          <span key={item.label} className="route-map-legend__item">
            <span className="route-map-legend__dot" style={{ background: item.color }} />
            {item.label}
          </span>
        ))}
      </div>
    </div>
  )
}
