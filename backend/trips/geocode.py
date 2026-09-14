"""Thin wrappers around two free, keyless map services:

- Nominatim (OpenStreetMap) for geocoding place names -> lat/lng
- OSRM public demo server for driving routes -> geometry/distance/duration

Both are called server-side (never from the browser) so we can set a proper
User-Agent per Nominatim's usage policy and keep API details out of the
frontend.
"""

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
USER_AGENT = "eld-trip-planner-assessment/1.0 (contact: mitch.i@scriberunner.com)"

METERS_PER_MILE = 1609.344


class GeocodeError(Exception):
    pass


class RoutingError(Exception):
    pass


def geocode(place_name):
    """Return (lat, lon, display_name) for a free-text place name."""
    resp = requests.get(
        NOMINATIM_URL,
        params={"q": place_name, "format": "json", "limit": 1},
        headers={"User-Agent": USER_AGENT},
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json()
    if not results:
        raise GeocodeError(f"Could not find a location matching '{place_name}'")
    top = results[0]
    return float(top["lat"]), float(top["lon"]), top.get("display_name", place_name)


def route(coords):
    """coords: list of (lat, lon) in travel order. Returns dict with
    distance_miles, duration_hours, geometry (list of [lat, lon]) and
    per-leg distance_miles/duration_hours for len(coords)-1 legs.
    """
    lon_lat_pairs = ";".join(f"{lon},{lat}" for lat, lon in coords)
    url = f"{OSRM_URL}/{lon_lat_pairs}"
    resp = requests.get(
        url,
        params={"overview": "full", "geometries": "geojson", "steps": "false"},
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise RoutingError(f"OSRM could not compute a route: {data.get('message', data.get('code'))}")

    route_data = data["routes"][0]
    geometry = [[lat, lon] for lon, lat in route_data["geometry"]["coordinates"]]
    legs = [
        {
            "distance_miles": leg["distance"] / METERS_PER_MILE,
            "duration_hours": leg["duration"] / 3600.0,
        }
        for leg in route_data["legs"]
    ]
    return {
        "distance_miles": route_data["distance"] / METERS_PER_MILE,
        "duration_hours": route_data["duration"] / 3600.0,
        "geometry": geometry,
        "legs": legs,
    }
