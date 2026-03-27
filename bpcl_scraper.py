"""
BPCL Fuel Station Scraper
=========================
Uses the HelloBPCL CEP API (confirmed working GET endpoint):
  GET https://api.cep.bpcl.in/retail/v2/bpcl/retail/rolocators
      ?latitude=X&longitude=Y&radius=50000
      &amenities=All_Amenities&fuelStationCategory=All&channel=Web&accountId=

Covers India with a geographic grid, deduplicates by station name.
"""
import requests, json, os, time, logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("bpcl")

API_URL = "https://api.cep.bpcl.in/retail/v2/bpcl/retail/rolocators"
AUTH_URL = "https://api.cep.bpcl.in/authorizationserver/oauth/token"
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bpcl_fuel_stations.geojson")

def get_token():
    r = requests.post(AUTH_URL,
        data="client_id=hybris2&client_secret=nimda&grant_type=client_credentials",
        headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=15)
    return r.json().get("access_token")

def search(token, lat, lon, radius=50000):
    try:
        r = requests.get(API_URL, params={
            "latitude": lat, "longitude": lon, "radius": radius,
            "amenities": "All_Amenities", "fuelStationCategory": "All",
            "channel": "Web", "accountId": ""
        }, headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0.0.0",
            "Origin": "https://hellobpcl.in",
            "Referer": "https://hellobpcl.in/"
        }, timeout=15)
        if r.status_code == 200:
            return r.json().get("pointOfServices", [])
        elif r.status_code == 401:
            return "REAUTH"
    except:
        pass
    return []

def india_grid(step=0.7):
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
    log.info("=== BPCL Scraper (HelloBPCL CEP API) ===")
    token = get_token()
    if not token:
        log.error("Auth failed"); return
    log.info(f"Token OK: {token[:15]}...")

    grid = india_grid(step=0.7)
    log.info(f"Grid: {len(grid)} points (0.7° ~78km)")

    stations = {}
    for i, (lat, lon) in enumerate(grid):
        result = search(token, lat, lon)
        if result == "REAUTH":
            token = get_token()
            result = search(token, lat, lon)
        if isinstance(result, list):
            for s in result:
                key = s.get("name", f"{lat},{lon}")
                if key not in stations:
                    stations[key] = s
        if (i+1) % 20 == 0:
            log.info(f"[{i+1}/{len(grid)}] Unique: {len(stations)}")
        time.sleep(0.1)

    log.info(f"\nTotal unique stations: {len(stations)}")

    # Export GeoJSON
    features = []
    for s in stations.values():
        gp = s.get("geoPoint") or {}
        lat = gp.get("latitude") or s.get("latitude")
        lon = gp.get("longitude") or s.get("longitude")
        if not lat or not lon: continue
        addr = s.get("address") or {}
        region = addr.get("region") or {}
        features.append({
            "type": "Feature",
            "properties": {
                "name": s.get("displayName") or s.get("name") or "BPCL",
                "brand": "Bharat Petroleum", "brand_code": "BPCL",
                "address": ", ".join(filter(None, [addr.get("line1"), addr.get("town"), addr.get("district"), region.get("name")])),
                "state": region.get("name", ""), "city": addr.get("town") or addr.get("district") or "",
                "phone": addr.get("cellphone") or "", "amenity": "fuel", "source": "hellobpcl.in"
            },
            "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]}
        })

    geojson = {
        "type": "FeatureCollection", "generator": "bpcl_scraper.py",
        "scraped_at": datetime.utcnow().isoformat() + "Z",
        "total_stations": len(features), "brand": "BPCL", "features": features
    }
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    log.info(f"Saved {len(features)} stations → {OUTPUT}")

if __name__ == "__main__":
    main()
