"""
TotalEnergies India Fuel Station Scraper (v2)
=============================================
Uses bounding box + coordinate-based filtering to exclude Pakistan/Bangladesh.
TotalEnergies has very few retail fuel stations in India.
"""
import requests, json, os, logging, time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("total")

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "totalenergies_fuel_stations.geojson")

def query_overpass(query):
    try:
        r = requests.post("https://overpass-api.de/api/interpreter",
                           data={"data": query}, timeout=90)
        if r.status_code == 200:
            return r.json().get("elements", [])
        log.warning(f"Overpass: {r.status_code}")
    except Exception as e:
        log.warning(f"Overpass error: {e}")
    return []

def is_in_india(lat, lon):
    """Rough filter: India is roughly lat 6-35, lon 68-97.5 
    but Pakistan overlaps lon 60-77. Use tighter checks."""
    if lat < 6 or lat > 35.5:
        return False
    if lon < 68 or lon > 97.5:
        return False
    # Exclude Pakistan (lat 24-37, lon 60-77 mostly)
    if lon < 72 and lat > 23:  # Western Pakistan region
        return False
    if lon < 70:  # Deep western Pakistan/Balochistan
        return False
    # Exclude Bangladesh (east of ~88, south of ~26)
    # Most Bangladesh is lat 20-26, lon 88-92 — overlap with NE India, so keep those
    return True

def main():
    log.info("=== TotalEnergies India Scraper v2 ===")

    # Bounding box queries with longer timeout
    queries = [
        '[out:json][timeout:90];(node["amenity"="fuel"]["brand"~"Total",i](6.5,68.0,35.5,97.5);way["amenity"="fuel"]["brand"~"Total",i](6.5,68.0,35.5,97.5););out center body;',
        '[out:json][timeout:90];(node["amenity"="fuel"]["operator"~"Total",i](6.5,68.0,35.5,97.5);way["amenity"="fuel"]["operator"~"Total",i](6.5,68.0,35.5,97.5););out center body;',
        '[out:json][timeout:90];(node["amenity"="fuel"]["name"~"TotalEnergies|Total Energies",i](6.5,68.0,35.5,97.5);way["amenity"="fuel"]["name"~"TotalEnergies|Total Energies",i](6.5,68.0,35.5,97.5););out center body;',
    ]

    all_stations = {}
    for i, q in enumerate(queries):
        log.info(f"Query {i+1}/{len(queries)}...")
        elements = query_overpass(q)
        log.info(f"  Got {len(elements)} raw elements")
        for e in elements:
            tags = e.get("tags", {})
            lat = e.get("lat") or (e.get("center", {}) or {}).get("lat")
            lon = e.get("lon") or (e.get("center", {}) or {}).get("lon")
            if lat and lon and is_in_india(lat, lon):
                key = f"{round(lat,5)},{round(lon,5)}"
                all_stations[key] = {
                    "name": tags.get("name") or tags.get("brand") or "TotalEnergies",
                    "brand": tags.get("brand", "TotalEnergies"),
                    "operator": tags.get("operator", ""),
                    "address": tags.get("addr:full") or tags.get("addr:street") or "",
                    "city": tags.get("addr:city") or tags.get("addr:district") or "",
                    "state": tags.get("addr:state") or "",
                    "lat": lat, "lon": lon,
                    "osm_id": e.get("id"),
                }
        time.sleep(3)

    log.info(f"\nIndia-filtered TotalEnergies stations: {len(all_stations)}")
    for key, s in all_stations.items():
        log.info(f"  {s['name'][:40]:40s} | {s['city'][:15]:15s} | ({s['lat']:.4f},{s['lon']:.4f})")

    # Export GeoJSON
    features = []
    for s in all_stations.values():
        features.append({
            "type": "Feature",
            "properties": {
                "name": s["name"], "brand": "TotalEnergies", "brand_code": "TotalEnergies",
                "address": s["address"], "state": s["state"], "city": s["city"],
                "amenity": "fuel", "source": "openstreetmap.org",
                "osm_id": s["osm_id"]
            },
            "geometry": {"type": "Point", "coordinates": [s["lon"], s["lat"]]}
        })

    geojson = {
        "type": "FeatureCollection", "generator": "totalenergies_scraper.py",
        "scraped_at": datetime.utcnow().isoformat() + "Z",
        "total_stations": len(features), "brand": "TotalEnergies", "features": features
    }
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    log.info(f"Saved {len(features)} stations -> {OUTPUT}")

if __name__ == "__main__":
    main()
