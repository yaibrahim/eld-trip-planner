const ROWS = [
  { key: 'OFF_DUTY', number: 1, label: 'Off Duty' },
  { key: 'SLEEPER_BERTH', number: 2, label: 'Sleeper Berth' },
  { key: 'DRIVING', number: 3, label: 'Driving' },
  { key: 'ON_DUTY', number: 4, label: 'On Duty (not driving)' },
]

const GRID_LEFT = 150
const HOUR_WIDTH = 30
const ROW_HEIGHT = 34
const GRID_TOP = 30
const GRID_WIDTH = 24 * HOUR_WIDTH
const GRID_HEIGHT = ROWS.length * ROW_HEIGHT
const TOTALS_GAP = 20
const TOTALS_COL_WIDTH = 50
const SVG_WIDTH = GRID_LEFT + GRID_WIDTH + TOTALS_GAP + TOTALS_COL_WIDTH + 10
const SVG_HEIGHT = GRID_TOP + GRID_HEIGHT + 26

function x(hour) {
  return GRID_LEFT + hour * HOUR_WIDTH
}

function rowIndex(status) {
  return ROWS.findIndex((r) => r.key === status)
}

function rowY(status) {
  return GRID_TOP + rowIndex(status) * ROW_HEIGHT + ROW_HEIGHT / 2
}

function hourLabel(h) {
  const hour24 = h % 24
  if (hour24 === 0) return 'Mid night'
  if (hour24 === 12) return 'Noon'
  if (hour24 < 12) return String(hour24)
  return String(hour24 - 12)
}

function buildPolyline(segments) {
  const points = []
  segments.forEach((seg, i) => {
    const y = rowY(seg.status)
    points.push(`${x(seg.start_hour)},${y}`)
    points.push(`${x(seg.end_hour)},${y}`)
    const next = segments[i + 1]
    if (next) {
      points.push(`${x(seg.end_hour)},${rowY(next.status)}`)
    }
  })
  return points.join(' ')
}

export default function DailyLogSheet({ day, dayIndex }) {
  const { date, segments, totals, recap, remarks } = day

  return (
    <div className="log-sheet">
      <div className="log-sheet__header">
        <h3>Daily Log — Day {dayIndex + 1}</h3>
        <span className="log-sheet__date">{date}</span>
      </div>

      <svg width={SVG_WIDTH} height={SVG_HEIGHT} className="log-sheet__svg" role="img" aria-label={`Duty status grid for ${date}`}>
        {/* hour labels */}
        {Array.from({ length: 25 }).map((_, h) => (
          <text key={`label-${h}`} x={x(h)} y={GRID_TOP - 10} fontSize="9" textAnchor="middle" fill="#334155">
            {hourLabel(h)}
          </text>
        ))}

        {/* vertical grid lines: quarter hours */}
        {Array.from({ length: 24 * 4 + 1 }).map((_, q) => {
          const hour = q / 4
          const isHour = q % 4 === 0
          return (
            <line
              key={`grid-${q}`}
              x1={x(hour)}
              y1={GRID_TOP}
              x2={x(hour)}
              y2={GRID_TOP + GRID_HEIGHT}
              stroke={isHour ? '#334155' : '#cbd5e1'}
              strokeWidth={isHour ? 1 : 0.5}
            />
          )
        })}

        {/* row lines + labels */}
        {ROWS.map((row, i) => (
          <g key={row.key}>
            <line
              x1={GRID_LEFT}
              y1={GRID_TOP + i * ROW_HEIGHT}
              x2={GRID_LEFT + GRID_WIDTH}
              y2={GRID_TOP + i * ROW_HEIGHT}
              stroke="#334155"
              strokeWidth={1}
            />
            <text x={8} y={GRID_TOP + i * ROW_HEIGHT + ROW_HEIGHT / 2 + 4} fontSize="11" fill="#0f172a">
              {row.number}. {row.label}
            </text>
            <text
              x={GRID_LEFT + GRID_WIDTH + TOTALS_GAP + TOTALS_COL_WIDTH / 2}
              y={GRID_TOP + i * ROW_HEIGHT + ROW_HEIGHT / 2 + 4}
              fontSize="11"
              textAnchor="middle"
              fill="#0f172a"
              fontWeight="600"
            >
              {(totals[row.label] ?? 0).toFixed(2)}
            </text>
          </g>
        ))}
        <line
          x1={GRID_LEFT}
          y1={GRID_TOP + GRID_HEIGHT}
          x2={GRID_LEFT + GRID_WIDTH}
          y2={GRID_TOP + GRID_HEIGHT}
          stroke="#334155"
        />
        <text x={GRID_LEFT + GRID_WIDTH + TOTALS_GAP + TOTALS_COL_WIDTH / 2} y={GRID_TOP - 10} fontSize="9" textAnchor="middle" fill="#334155">
          Total
        </text>

        {/* duty status step line */}
        <polyline points={buildPolyline(segments)} fill="none" stroke="#dc2626" strokeWidth={2.5} strokeLinejoin="round" />
      </svg>

      <div className="log-sheet__remarks">
        <strong>Remarks</strong>
        <ul>
          {remarks.map((r, i) => (
            <li key={i}>
              {r.time} — {r.label}
            </li>
          ))}
        </ul>
      </div>

      <div className="log-sheet__recap">
        <div>
          <span className="recap-label">On duty hours today</span>
          <span className="recap-value">{recap.on_duty_hours_today}</span>
        </div>
        <div>
          <span className="recap-label">70hr/8-day total used through today</span>
          <span className="recap-value">{recap.cycle_hours_used_through_today}</span>
        </div>
        <div>
          <span className="recap-label">Hours available tomorrow</span>
          <span className="recap-value">{recap.hours_available_tomorrow}</span>
        </div>
      </div>
    </div>
  )
}
