"""
Nayara Energy Fuel Station Scraper
==================================
Scrapes all Nayara Energy fuel stations across India and exports to GeoJSON.
Uses curl_cffi to bypass Cloudflare bot protections.

Strategy:
Creates a grid of coordinates across India and queries the internal
`get-code-ro-radius` API with a generous radius to sweep all stations.
"""

import json
import os
import sys
import time
import logging
from datetime import datetime
import concurrent.futures

try:
    from curl_cffi import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Please install required packages: pip install curl_cffi beautifulsoup4")
    sys.exit(1)

# ─── Configuration ───────────────────────────────────────────────────────────

BASE_URL = "https://www.nayaraenergy.com"
MAP_URL = f"{BASE_URL}/petrol-pump-near-me"

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "..", "nayara_fuel_stations.geojson")
PROGRESS_FILE = os.path.join(OUTPUT_DIR, "nayara_progress.json")

# Bounding box for India
LAT_START = 8.0
LAT_END = 37.0
LON_START = 68.0
LON_END = 97.0

# 1.5 degree is ~166km. We use radius 300 to heavily overlap and miss nothing.
GRID_STEP = 1.5
SEARCH_RADIUS = 300 

MAX_WORKERS = 10
REQUEST_DELAY = 1.0     # sleep between requests
MAX_RETRIES = 3
RETRY_DELAY = 5

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-5s │ %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("nayara_scraper")

# ─── Session Setup ───────────────────────────────────────────────────────────

def create_session():
    # Chrome spoofing bypasses Cloudflare generic blocks
    s = requests.Session(impersonate="chrome120", timeout=30)
    s.headers.update({
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Referer": MAP_URL,
        "X-Requested-With": "XMLHttpRequest",
    })
    return s

def get_api_credentials(session):
    """Fetches the dynamic API endpoint and CSRF token required for POST requests."""
    log.info("Fetching CSRF token and internal API endpoint...")
    for _ in range(3):
        try:
            resp = session.get(MAP_URL)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                csrf = soup.find('meta', {'name': 'csrf-token'})
                api_input = soup.find(class_='ro-code-radius')
                
                if csrf and api_input:
                    token = csrf['content']
                    endpoint = api_input['value']
                    log.info(f"API Endpoint: {endpoint}")
                    
                    # Update session headers with token
                    session.headers.update({'X-CSRF-TOKEN': token})
                    return endpoint
            log.warning(f"Failed to extract tokens (HTTP {resp.status_code}). Retrying...")
            time.sleep(2)
        except Exception as e:
            log.warning(f"Request failed: {e}. Retrying...")
            time.sleep(2)
            
    log.error("Failed to retrieve API credentials.")
    return None

# ─── Data Types ──────────────────────────────────────────────────────────────

def load_progress() -> dict:
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"stations": {}, "completed_grids": []}

def save_progress(progress: dict):
    temp_file = PROGRESS_FILE + ".tmp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
    try:
        os.replace(temp_file, PROGRESS_FILE)
    except PermissionError:
        import shutil
        shutil.copyfile(temp_file, PROGRESS_FILE)


def generate_grid() -> list:
    """Creates a list of (lat, lon) coordinates covering India."""
    points = []
    lat = LAT_START
    while lat <= LAT_END:
        lon = LON_START
        while lon <= LON_END:
            points.append((round(lat, 4), round(lon, 4)))
            lon += GRID_STEP
        lat += GRID_STEP
    return points


def fetch_stations_for_grid(session, api_url: str, lat: float, lon: float) -> list:
    """Hits the Nayara API for a specific coordinate and radius."""
    data = {
        'curr_lat': str(lat),
        'curr_long': str(lon),
        'radius': str(SEARCH_RADIUS)
    }

    import random
    time.sleep(REQUEST_DELAY + random.uniform(0, 0.5))

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.post(api_url, data=data)
            if resp.status_code == 200:
                result = resp.json()
                if isinstance(result, list):
                    return result
                if isinstance(result, dict) and "error" in result:
                    # Some endpoints return {"error": "No Petrol Pump found."}
                    return []
            
            # 500 or generic error
            log.debug(f"HTTP {resp.status_code} at {lat},{lon}")
            
        except requests.RequestsError as e:
            log.debug(f"Request Error at {lat},{lon}: {e}")
        except json.JSONDecodeError:
            log.debug(f"Non-JSON response at {lat},{lon}")

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY * attempt)

    log.warning(f"Failed to fetch grid {lat},{lon} after {MAX_RETRIES} attempts.")
    return []


def export_geojson(stations_dict: dict, output_path: str):
    """Exports deduplicated stations to GeoJSON."""
    features = []
    for ro_code, s in stations_dict.items():
        try:
            lat = float(s.get('latitude', 0))
            lon = float(s.get('longitude', 0))
        except ValueError:
            continue
            
        if lat == 0 or lon == 0:
            continue

        feature = {
            "type": "Feature",
            "properties": {
                "name": (s.get('ro_name') or '').strip(),
                "brand": "Nayara Energy",
                "brand_code": "NAYARA",
                "address": (s.get('address') or s.get('address1') or '').strip(),
                "state": (s.get('state_name') or '').strip(),
                "city": (s.get('district_name') or '').strip(),
                "ro_code": (s.get('cms_code') or str(ro_code)).strip(),
                "amenity": "fuel",
                "source": "nayaraenergy.com"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            }
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "generator": "nayara_scraper.py",
        "scraped_at": datetime.utcnow().isoformat() + "Z",
        "total_stations": len(features),
        "brand": "Nayara Energy",
        "features": features,
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    log.info(f"═══════════════════════════════════════════════")
    log.info(f"  GeoJSON exported: {output_path}")
    log.info(f"  Total features saved: {len(features)}")
    log.info(f"═══════════════════════════════════════════════")


def main():
    log.info("═══════════════════════════════════════════════")
    log.info("  Nayara Energy Fuel Station Scraper")
    log.info("  Source: nayaraenergy.com")
    log.info("═══════════════════════════════════════════════")

    progress = load_progress()
    all_stations = progress.get("stations", {})  # Use dict keyed by cms_code for deduplication
    completed_grids = set(progress.get("completed_grids", []))

    session = create_session()
    api_url = get_api_credentials(session)
    if not api_url:
        return

    grid_points = generate_grid()
    log.info(f"Generated {len(grid_points)} grid points to scan across India")

    points_to_scan = [p for p in grid_points if f"{p[0]}_{p[1]}" not in completed_grids]
    
    if not points_to_scan:
        log.info("All grid points already scanned!")
        export_geojson(all_stations, OUTPUT_FILE)
        return

    log.info(f"Resuming scan for {len(points_to_scan)} remaining grids with {MAX_WORKERS} workers...")

    import threading
    lock = threading.Lock()

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {
            executor.submit(fetch_stations_for_grid, session, api_url, p[0], p[1]): p 
            for p in points_to_scan
        }

        count = 0
        for future in concurrent.futures.as_completed(future_map):
            lat, lon = future_map[future]
            grid_id = f"{lat}_{lon}"
            count += 1
            
            try:
                stations = future.result()
                
                with lock:
                    new_found = 0
                    for s in stations:
                        # Use cms_code or combination of name+location as unique ID
                        uid = s.get('cms_code') or f"{s.get('latitude')}_{s.get('longitude')}"
                        if uid not in all_stations:
                            all_stations[uid] = s
                            new_found += 1
                    
                    completed_grids.add(grid_id)
                    total_unique = len(all_stations)
                    
                    log.info(f"  [{count}/{len(points_to_scan)}] Grid ({lat}, {lon}) "
                             f"→ Found {len(stations)} ({new_found} new). Total Unique: {total_unique}")

                    # Periodically save
                    if count % 20 == 0:
                        progress["stations"] = all_stations
                        progress["completed_grids"] = list(completed_grids)
                        save_progress(progress)

            except Exception as e:
                log.error(f"  Grid ({lat}, {lon}) failed fatally: {e}")

    # Final Save
    progress["stations"] = all_stations
    progress["completed_grids"] = list(completed_grids)
    save_progress(progress)

    log.info(f"\nScan complete. Total unique Nayara stations found: {len(all_stations)}")
    export_geojson(all_stations, OUTPUT_FILE)

if __name__ == "__main__":
    main()
