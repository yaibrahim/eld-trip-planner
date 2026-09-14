"""HOS (Hours of Service) trip simulation engine.

Simulates a property-carrying driver's trip (current -> pickup -> dropoff)
under the FMCSA rules assumed by the assessment brief:
  - 70-hour/8-day cycle, no adverse driving conditions exception
  - 11-hour driving limit / 14-hour on-duty window per shift
  - 30-minute break required after 8 cumulative hours of driving
  - 10 consecutive hours off duty to reset the 11/14-hour shift clocks
  - 34-hour restart when the 70-hour cycle would otherwise be exceeded
  - 1 hour on-duty (not driving) for pickup and for dropoff
  - Fuel stop at least once every 1,000 miles

Documented simplification: the 70-hour/8-day limit is tracked as a single
running total seeded by the driver's reported "current cycle used" hours,
not a true rolling 8-day window (the API only receives one cycle-used
number, not 8 days of prior logs). A 34-hour restart zeroes it, matching
how a driver would actually regain hours on a real trip.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from . import geocode as geo

OFF_DUTY = "OFF_DUTY"
SLEEPER_BERTH = "SLEEPER_BERTH"
DRIVING = "DRIVING"
ON_DUTY = "ON_DUTY"

STATUS_LABELS = {
    OFF_DUTY: "Off Duty",
    SLEEPER_BERTH: "Sleeper Berth",
    DRIVING: "Driving",
    ON_DUTY: "On Duty (Not Driving)",
}

DRIVING_LIMIT_HOURS = 11.0
WINDOW_LIMIT_HOURS = 14.0
BREAK_TRIGGER_HOURS = 8.0
BREAK_DURATION_HOURS = 0.5
OFF_DUTY_RESET_HOURS = 10.0
RESTART_HOURS = 34.0
CYCLE_LIMIT_HOURS = 70.0
FUEL_INTERVAL_MILES = 1000.0
FUEL_STOP_HOURS = 0.5
PICKUP_DROPOFF_HOURS = 1.0
DEFAULT_AVG_SPEED_MPH = 50.0
EPSILON = 1e-6
MAX_ITERATIONS = 2000


@dataclass
class _Leg:
    label: str
    miles: float
    avg_speed_mph: float


@dataclass
class _Event:
    status: str
    start: datetime
    end: datetime
    label: str
    cumulative_miles: float  # distance travelled along the whole trip at event end
    cycle_hours_used: float  # snapshot of the 70hr/8day running total at event end

    @property
    def hours(self):
        return (self.end - self.start).total_seconds() / 3600.0


@dataclass
class _SimState:
    now: datetime
    shift_start: datetime
    driving_hours_shift: float = 0.0
    drive_since_break: float = 0.0
    cycle_hours_used: float = 0.0
    distance_since_fuel: float = 0.0
    cumulative_miles: float = 0.0
    events: list = field(default_factory=list)

    @property
    def window_hours_used(self):
        return (self.now - self.shift_start).total_seconds() / 3600.0

    def add_event(self, status, hours, label):
        start = self.now
        end = self.now + timedelta(hours=hours)
        self.now = end
        self.events.append(_Event(status, start, end, label, self.cumulative_miles, self.cycle_hours_used))
        return self.events[-1]

    def drive(self, hours, avg_speed_mph, label):
        miles = hours * avg_speed_mph
        self.driving_hours_shift += hours
        self.drive_since_break += hours
        self.cycle_hours_used += hours
        self.distance_since_fuel += miles
        self.cumulative_miles += miles
        self.add_event(DRIVING, hours, label)

    def on_duty(self, hours, label, counts_toward_break=True):
        self.cycle_hours_used += hours
        if counts_toward_break and hours >= BREAK_DURATION_HOURS - EPSILON:
            self.drive_since_break = 0.0
        self.add_event(ON_DUTY, hours, label)

    def off_duty(self, hours, label, status=OFF_DUTY):
        self.add_event(status, hours, label)
        if hours >= OFF_DUTY_RESET_HOURS - EPSILON:
            self.driving_hours_shift = 0.0
            self.drive_since_break = 0.0
            self.shift_start = self.now
        elif hours >= BREAK_DURATION_HOURS - EPSILON:
            self.drive_since_break = 0.0


def _build_legs(route_data, pickup_label, dropoff_label):
    legs = []
    leg_labels = [f"Drive to {pickup_label}", f"Drive to {dropoff_label}"]
    for leg, label in zip(route_data["legs"], leg_labels):
        speed = leg["distance_miles"] / leg["duration_hours"] if leg["duration_hours"] > EPSILON else DEFAULT_AVG_SPEED_MPH
        legs.append(_Leg(label=label, miles=leg["distance_miles"], avg_speed_mph=speed or DEFAULT_AVG_SPEED_MPH))
    return legs


def _simulate(legs, cycle_used_hours, start_dt):
    state = _SimState(now=start_dt, shift_start=start_dt, cycle_hours_used=cycle_used_hours)

    for leg_index, leg in enumerate(legs):
        remaining_miles = leg.miles
        iterations = 0
        while remaining_miles > EPSILON:
            iterations += 1
            if iterations > MAX_ITERATIONS:
                raise RuntimeError("HOS simulation did not converge")

            if state.distance_since_fuel >= FUEL_INTERVAL_MILES - 1e-3:
                state.on_duty(FUEL_STOP_HOURS, "Fuel stop")
                state.distance_since_fuel = 0.0
                continue

            if state.cycle_hours_used >= CYCLE_LIMIT_HOURS - EPSILON:
                state.off_duty(RESTART_HOURS, "34-hour restart (70-hour cycle reached)", status=OFF_DUTY)
                state.cycle_hours_used = 0.0
                continue

            if state.driving_hours_shift >= DRIVING_LIMIT_HOURS - EPSILON or state.window_hours_used >= WINDOW_LIMIT_HOURS - EPSILON:
                state.off_duty(OFF_DUTY_RESET_HOURS, "10-hour rest (daily reset)", status=SLEEPER_BERTH)
                continue

            if state.drive_since_break >= BREAK_TRIGGER_HOURS - EPSILON:
                state.off_duty(BREAK_DURATION_HOURS, "Required 30-minute break", status=OFF_DUTY)
                continue

            time_to_leg_end = remaining_miles / leg.avg_speed_mph
            time_to_11hr = DRIVING_LIMIT_HOURS - state.driving_hours_shift
            time_to_14hr = WINDOW_LIMIT_HOURS - state.window_hours_used
            time_to_break = BREAK_TRIGGER_HOURS - state.drive_since_break
            time_to_cycle = CYCLE_LIMIT_HOURS - state.cycle_hours_used
            miles_to_fuel = FUEL_INTERVAL_MILES - state.distance_since_fuel
            time_to_fuel = miles_to_fuel / leg.avg_speed_mph if miles_to_fuel > 0 else 0.0

            chunk_hours = min(time_to_leg_end, time_to_11hr, time_to_14hr, time_to_break, time_to_cycle, time_to_fuel)
            chunk_hours = max(chunk_hours, EPSILON)

            state.drive(chunk_hours, leg.avg_speed_mph, leg.label)
            remaining_miles -= chunk_hours * leg.avg_speed_mph

        if leg_index == 0:
            state.on_duty(PICKUP_DROPOFF_HOURS, "Pickup (loading)")
        else:
            state.on_duty(PICKUP_DROPOFF_HOURS, "Dropoff (unloading)")

    return _merge_adjacent(state.events)


def _merge_adjacent(events):
    merged = []
    for e in events:
        if merged and merged[-1].status == e.status and merged[-1].label == e.label and abs((merged[-1].end - e.start).total_seconds()) < 1:
            merged[-1] = _Event(e.status, merged[-1].start, e.end, e.label, e.cumulative_miles, e.cycle_hours_used)
        else:
            merged.append(e)
    return merged


def _split_at_midnight(events):
    split = []
    for e in events:
        start, end = e.start, e.end
        while start.date() != end.date():
            midnight = datetime(start.year, start.month, start.day) + timedelta(days=1)
            split.append(_Event(e.status, start, midnight, e.label, e.cumulative_miles, e.cycle_hours_used))
            start = midnight
        split.append(_Event(e.status, start, end, e.label, e.cumulative_miles, e.cycle_hours_used))
    return split


def _daily_logs(events):
    days = {}
    for e in events:
        days.setdefault(e.start.date(), []).append(e)

    logs = []
    for day in sorted(days.keys()):
        day_events = days[day]
        segments = [
            {
                "status": e.status,
                "status_label": STATUS_LABELS[e.status],
                "start_hour": _decimal_hour(e.start, day),
                "end_hour": _decimal_hour(e.end, day),
                "label": e.label,
                "start_time": e.start.strftime("%H:%M"),
                "end_time": e.end.strftime("%H:%M"),
            }
            for e in day_events
        ]
        totals = {status: 0.0 for status in STATUS_LABELS}
        for e in day_events:
            totals[e.status] += e.hours

        on_duty_today = totals[DRIVING] + totals[ON_DUTY]
        cycle_used_through_today = day_events[-1].cycle_hours_used
        hours_available_tomorrow = max(0.0, CYCLE_LIMIT_HOURS - cycle_used_through_today)

        remarks = [
            {"time": e.start.strftime("%H:%M"), "label": e.label}
            for e in day_events
        ]

        logs.append({
            "date": day.isoformat(),
            "segments": segments,
            "totals": {STATUS_LABELS[k]: round(v, 2) for k, v in totals.items()},
            "recap": {
                "on_duty_hours_today": round(on_duty_today, 2),
                "cycle_hours_used_through_today": round(cycle_used_through_today, 2),
                "hours_available_tomorrow": round(hours_available_tomorrow, 2),
            },
            "remarks": remarks,
        })
    return logs


def _decimal_hour(dt, day):
    if dt.date() != day:
        return 24.0
    return dt.hour + dt.minute / 60.0 + dt.second / 3600.0


def _interpolate_point(geometry, cumulative_distances, target_miles):
    if not geometry:
        return None
    if target_miles <= 0:
        return geometry[0]
    if target_miles >= cumulative_distances[-1]:
        return geometry[-1]
    for i in range(1, len(cumulative_distances)):
        if cumulative_distances[i] >= target_miles:
            d0, d1 = cumulative_distances[i - 1], cumulative_distances[i]
            p0, p1 = geometry[i - 1], geometry[i]
            frac = (target_miles - d0) / (d1 - d0) if d1 > d0 else 0
            lat = p0[0] + (p1[0] - p0[0]) * frac
            lon = p0[1] + (p1[1] - p0[1]) * frac
            return [lat, lon]
    return geometry[-1]


def _cumulative_geometry_distances(geometry):
    from math import radians, sin, cos, asin, sqrt

    def haversine_miles(a, b):
        lat1, lon1, lat2, lon2 = map(radians, [a[0], a[1], b[0], b[1]])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        return 2 * 3958.8 * asin(sqrt(h))

    distances = [0.0]
    for i in range(1, len(geometry)):
        distances.append(distances[-1] + haversine_miles(geometry[i - 1], geometry[i]))
    return distances


def plan_trip(current_location, pickup_location, dropoff_location, current_cycle_used, start_dt=None):
    start_dt = start_dt or datetime.now().replace(minute=0, second=0, microsecond=0)

    current = geo.geocode(current_location)
    pickup = geo.geocode(pickup_location)
    dropoff = geo.geocode(dropoff_location)

    route_data = geo.route([(current[0], current[1]), (pickup[0], pickup[1]), (dropoff[0], dropoff[1])])
    legs = _build_legs(route_data, pickup_location, dropoff_location)

    events = _simulate(legs, current_cycle_used, start_dt)
    events = _split_at_midnight(events)
    daily_logs = _daily_logs(events)

    geometry = route_data["geometry"]
    cum_distances = _cumulative_geometry_distances(geometry)

    stops = []
    for e in events:
        if e.status == DRIVING:
            continue
        point = _interpolate_point(geometry, cum_distances, e.cumulative_miles)
        stops.append({
            "label": e.label,
            "status": e.status,
            "status_label": STATUS_LABELS[e.status],
            "start": e.start.isoformat(),
            "end": e.end.isoformat(),
            "duration_hours": round(e.hours, 2),
            "lat": point[0] if point else None,
            "lon": point[1] if point else None,
        })

    total_driving_hours = sum(e.hours for e in events if e.status == DRIVING)
    total_on_duty_hours = sum(e.hours for e in events if e.status == ON_DUTY)
    trip_end = events[-1].end if events else start_dt

    summary = {
        "total_distance_miles": round(route_data["distance_miles"], 1),
        "total_driving_hours": round(total_driving_hours, 2),
        "total_on_duty_hours": round(total_on_duty_hours, 2),
        "total_trip_duration_hours": round((trip_end - start_dt).total_seconds() / 3600.0, 2),
        "num_days": len(daily_logs),
        "fuel_stops": sum(1 for s in stops if s["label"] == "Fuel stop"),
        "rest_breaks": sum(1 for s in stops if "break" in s["label"].lower()),
        "reset_stops": sum(1 for s in stops if "reset" in s["label"].lower() or "restart" in s["label"].lower()),
        "start_time": start_dt.isoformat(),
        "end_time": trip_end.isoformat(),
    }

    waypoints = {
        "current": {"label": current_location, "display_name": current[2], "lat": current[0], "lon": current[1]},
        "pickup": {"label": pickup_location, "display_name": pickup[2], "lat": pickup[0], "lon": pickup[1]},
        "dropoff": {"label": dropoff_location, "display_name": dropoff[2], "lat": dropoff[0], "lon": dropoff[1]},
    }

    return {
        "summary": summary,
        "waypoints": waypoints,
        "route": {"geometry": geometry},
        "stops": stops,
        "daily_logs": daily_logs,
    }
