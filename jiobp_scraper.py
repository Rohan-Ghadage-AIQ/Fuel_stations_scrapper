"""
Jio-bp (Reliance) Fuel Station Scraper
======================================
Scrapes all Jio-bp and Reliance fuel stations across India and exports to GeoJSON.
Bypasses the Cloudflare WAF entirely by accessing an unlinked static JSON text file
left on their web server.
"""

import json
import os
import sys
import logging
from datetime import datetime

try:
    from curl_cffi import requests
except ImportError:
    print("Please install curl_cffi: pip install curl_cffi")
    sys.exit(1)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "..", "jiobp_fuel_stations.geojson")

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(levelname)-5s │ %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("jiobp_scraper")

def fetch_stations():
    url = "https://www.jiobp.com/themes/custom/jiobp/fuel-data-json/LocationAPIOutput.txt"
    log.info(f"Fetching unprotected static JSON dump: {url}")
    
    try:
        resp = requests.get(url, impersonate='chrome120', timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            ro_details = data.get('RO_Details', [])
            log.info(f"Successfully retrieved {len(ro_details)} stations.")
            return ro_details
        else:
            log.error(f"Failed to fetch static data. Status: {resp.status_code}")
            return []
            
    except Exception as e:
        log.error(f"Error fetching stations: {e}")
        return []

def export_geojson(stations_list: list, output_path: str):
    features = []
    
    for s in stations_list:
        try:
            lat = float(s.get('latitude', 0))
            lon = float(s.get('longitude', 0))
        except (ValueError, TypeError):
            continue
            
        if lat == 0 or lon == 0:
            continue

        feature = {
            "type": "Feature",
            "properties": {
                "name": (s.get('Roname') or '').strip(),
                "brand": "Jio-bp",
                "brand_code": "JIOBP",
                "address": (s.get('Roaddress1') or '').strip(),
                "state": (s.get('State') or '').strip(),
                "city": (s.get('City') or '').strip(),
                "ro_code": (s.get('Rocode') or '').strip(),
                "amenity": "fuel",
                "source": "jiobp.com"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            }
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "generator": "jiobp_scraper.py",
        "scraped_at": datetime.utcnow().isoformat() + "Z",
        "total_stations": len(features),
        "brand": "Jio-bp",
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
    log.info("  Jio-bp (Reliance) Fuel Station Scraper")
    log.info("  Source: jiobp.com")
    log.info("═══════════════════════════════════════════════")

    stations = fetch_stations()
    if stations:
        export_geojson(stations, OUTPUT_FILE)
    else:
        log.error("No stations found. Aborting export.")

if __name__ == "__main__":
    main()
