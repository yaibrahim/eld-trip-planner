# ELD Trip Planner

A full-stack app for a property-carrying truck driver: enter a current
location, pickup, dropoff and how many hours are already used in the
70-hour/8-day cycle, and get back a driving route (map + stops/rests) and
FMCSA-style Daily Log Sheets, auto-filled and drawn exactly like the paper
ELD grid.

- **Backend**: Django + Django REST Framework — geocoding, routing, and the
  Hours-of-Service (HOS) simulation engine.
- **Frontend**: React (Vite) — trip form, an interactive map, and an SVG
  rendering of the daily log grid.
- **Map data**: [OSRM](https://project-osrm.org/) (routing) and
  [Nominatim/OpenStreetMap](https://nominatim.org/) (geocoding) — both free,
  keyless, called server-side.

## How it works

1. The React form posts `current_location`, `pickup_location`,
   `dropoff_location`, `current_cycle_used` to `POST /api/trips/plan/`.
2. Django geocodes all three locations (Nominatim) and fetches the driving
   route for current → pickup → dropoff in one call (OSRM).
3. `trips/hos.py` simulates the trip minute-by-minute against the HOS rules
   below, producing a timeline of Driving / On Duty / Sleeper Berth / Off
   Duty events with real timestamps and locations.
4. The timeline is split at midnight into calendar days. Each day becomes
   one Daily Log Sheet: duty-status segments for the SVG grid, per-status
   totals, remarks, and the 70-hour recap numbers.
5. The trip and its computed result are saved to the database and shown in
   a "Recent Trips" list.

## HOS rules implemented

Property-carrying driver, 70-hour/8-day cycle, no adverse driving
conditions exception (per the assessment brief):

- 11-hour driving limit and 14-hour on-duty window per shift
- 30-minute break required after 8 cumulative hours of driving
- 10 consecutive hours off duty to reset the shift clocks
- 34-hour restart if the 70-hour cycle would otherwise be exceeded
- 1 hour on-duty (not driving) for pickup and for dropoff
- A fuel stop at least once every 1,000 miles

**Simplification, called out explicitly:** the 70-hour/8-day limit is
tracked as a single running total seeded by the driver's reported
"current cycle used" hours, not a true rolling 8-day window — the API only
receives one cycle-used number, not eight days of prior logs. A 34-hour
restart zeroes it, which mirrors how a driver actually regains hours on the
road. Average driving speed per leg is derived from OSRM's own
distance/duration for that leg, so simulated drive time matches real road
time rather than a flat mph guess.

## Project layout

```
backend/    Django + DRF API (trips app: models, hos.py engine, geocode.py, views)
frontend/   React (Vite) app (TripForm, RouteMap, DailyLogSheet, TripSummary)
```

## Local development

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

Runs the API at `http://localhost:8000/api/`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs the app at `http://localhost:5173`; Vite proxies `/api` to
`http://localhost:8000` in development (see `vite.config.js`).

## API

`POST /api/trips/plan/`

```json
{
  "current_location": "Chicago, IL",
  "pickup_location": "Indianapolis, IN",
  "dropoff_location": "Dallas, TX",
  "current_cycle_used": 20
}
```

Returns `{ summary, waypoints, route: { geometry }, stops, daily_logs }`.

`GET /api/trips/` — the 10 most recently computed trips.

## Deployment

### Backend → Render

1. Push this repo to GitHub.
2. On [Render](https://render.com), New → Blueprint, point it at this repo
   (it will read `backend/render.yaml`) — or New → Web Service with:
   - Root directory: `backend`
   - Build command: `./build.sh`
   - Start command: `gunicorn config.wsgi:application`
3. Set environment variables (see `backend/.env.example`):
   - `SECRET_KEY` — Render can auto-generate this
   - `DEBUG=false`
   - `ALLOWED_HOSTS=.onrender.com`
   - `CORS_ALLOWED_ORIGINS=https://<your-frontend>.vercel.app`
4. Note the deployed URL, e.g. `https://eld-trip-planner-api.onrender.com`.

### Frontend → Vercel

1. Import this repo on [Vercel](https://vercel.com), set the project root
   to `frontend`.
2. Set the environment variable `VITE_API_BASE_URL` to
   `https://<your-render-service>.onrender.com/api`.
3. Deploy. Vercel auto-detects the Vite framework.

Once both are live, update the backend's `CORS_ALLOWED_ORIGINS` with the
real Vercel URL and redeploy the backend.

**Note on persistence**: Render's free tier uses an ephemeral filesystem,
so the SQLite-backed "Recent Trips" history resets on redeploy/restart.
That's expected for this demo-scale deployment.
