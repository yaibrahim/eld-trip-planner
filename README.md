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

## Live app

- **App**: https://eld-trip-planner-ruddy.vercel.app
- **API**: https://eld-trip-planner-api-ashy.vercel.app/api/
- **API docs (Swagger UI)**: https://eld-trip-planner-api-ashy.vercel.app/api/docs/
- **API docs (ReDoc)**: https://eld-trip-planner-api-ashy.vercel.app/api/redoc/
- **OpenAPI schema (JSON)**: https://eld-trip-planner-api-ashy.vercel.app/api/schema/

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

Full interactive docs are generated with [drf-spectacular](https://drf-spectacular.readthedocs.io/)
and served at `/api/docs/` (Swagger UI), `/api/redoc/` (ReDoc), and
`/api/schema/` (raw OpenAPI 3 YAML/JSON) — see the live links above.

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

Both the frontend and backend are deployed on **Vercel** as two separate
projects from the same GitHub repo (Render and Railway were tried first but
both now require a credit card on file even for their free tiers, which
this deployment avoids).

**Important**: each Vercel project's Git integration is intentionally
**disconnected**, so pushing to GitHub does *not* auto-deploy. This is a
monorepo with two apps living in one repo (`backend/`, `frontend/`); a
git-triggered deploy builds from the repo root and doesn't know which
subfolder is which project's root, which took the site down once already.
Deploy explicitly instead, from inside the right folder:

```bash
cd backend && vercel --prod   # deploy the API
cd frontend && vercel --prod  # deploy the app
```

### Backend → Vercel (Python serverless)

The backend deploys as a Python serverless function rather than a
long-running server:

- `backend/api/index.py` is the serverless entrypoint — it runs Django
  migrations against a SQLite file in `/tmp` on cold start (the only
  writable path in the serverless filesystem), then exposes the Django
  WSGI app.
- `backend/vercel.json` tells Vercel's `@vercel/python` builder to route
  all requests to that entrypoint.

To redeploy or set up your own copy:

```bash
cd backend
vercel link          # create/link a Vercel project rooted here
vercel env add SECRET_KEY production
vercel env add DEBUG production                # "false"
vercel env add ALLOWED_HOSTS production        # ".vercel.app"
vercel env add CORS_ALLOWED_ORIGINS production # your frontend's URL
vercel --prod
```

**Note on persistence**: Vercel's serverless filesystem is ephemeral, so
the SQLite-backed "Recent Trips" history only lives for the life of a warm
function instance and resets on redeploy/cold start. That's expected at
this demo scale — see the `current_cycle_used` simplification note above
for the same reasoning applied to the HOS cycle math.

A `backend/render.yaml` + `backend/build.sh` are also included as a ready
alternative if you do have a Render/Railway account with billing set up —
that path runs the same Django app as a normal long-running server with a
persistent-for-longer SQLite file instead of the `/tmp` workaround above.

### Frontend → Vercel

```bash
cd frontend
vercel link
vercel env add VITE_API_BASE_URL production   # https://<your-backend>.vercel.app/api
vercel --prod
```

Vercel auto-detects the Vite framework. After both are deployed, make sure
the backend's `CORS_ALLOWED_ORIGINS` matches the frontend's real URL (the
included `CORS_ALLOWED_ORIGIN_REGEXES` in `settings.py` already allows any
`*.vercel.app` origin as a convenience, so this mainly matters if you move
the frontend off Vercel).
