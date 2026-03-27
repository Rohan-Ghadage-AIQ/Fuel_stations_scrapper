"""
Shell India Fuel Station Scraper
================================
API: GET https://shellgsllocator.geoapp.me/api/v2/locations/nearest_to
     ?lat=X&lng=Y&autoload=true&format=json
Returns: {locations: [{id, name, lat, lng, brand, address, city, state, ...}]}

Shell has ~350-400 stations in India. A coarse grid will capture them all.
"""
import requests, json, os, time, logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("shell")

API_URL = "https://shellgsllocator.geoapp.me/api/v2/locations/nearest_to"
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shell_fuel_stations.geojson")

def search(lat, lon):
    try:
        r = requests.get(API_URL, params={
            "lat": lat, "lng": lon, "autoload": "true",
            "travel_mode": "driving", "fuel_type": "", "avoid_tolls": "false",
            "avoid_highways": "false", "corridor_radius": "5", "format": "json"
        }, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            return r.json().get("locations", [])
    except:
        pass
    return []

def india_grid(step=2.0):
    pts = []
    lat = 7.0
    while lat <= 35.5:
        lon = 68.0
        while lon <= 97.5:
            pts.append((round(lat, 2), round(lon, 2)))
            lon += step
        lat += step
    return pts

def main():
    log.info("=== Shell India Scraper ===")
    grid = india_grid(step=2.0)
    log.info(f"Grid: {len(grid)} points (2° ~220km)")

    stations = {}
    for i, (lat, lon) in enumerate(grid):
        locs = search(lat, lon)
        for s in locs:
            if s.get("country_code") == "IN" and not s.get("inactive"):
                stations[s["id"]] = s
        if locs:
            log.info(f"[{i+1}/{len(grid)}] ({lat},{lon}): {len(locs)} found. Unique: {len(stations)}")
        time.sleep(0.2)

    log.info(f"\nTotal unique Shell stations: {len(stations)}")

    features = []
    for s in stations.values():
        features.append({
            "type": "Feature",
            "properties": {
                "name": s.get("name", "Shell"),
                "brand": "Shell", "brand_code": "Shell",
                "address": ", ".join(filter(None, [s.get("address"), s.get("city"), s.get("state")])),
                "state": s.get("state", ""), "city": s.get("city", ""),
                "postcode": s.get("postcode", ""), "phone": s.get("telephone", ""),
                "amenity": "fuel", "source": "shellgsllocator.geoapp.me"
            },
            "geometry": {"type": "Point", "coordinates": [s["lng"], s["lat"]]}
        })

    geojson = {
        "type": "FeatureCollection", "generator": "shell_scraper.py",
        "scraped_at": datetime.utcnow().isoformat() + "Z",
        "total_stations": len(features), "brand": "Shell", "features": features
    }
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    log.info(f"Saved {len(features)} stations → {OUTPUT}")

    # Cleanup probe file
    probe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shell_probe.py")
    if os.path.exists(probe):
        os.remove(probe)

if __name__ == "__main__":
    main()
