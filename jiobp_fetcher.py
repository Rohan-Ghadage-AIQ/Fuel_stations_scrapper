from playwright.sync_api import sync_playwright
import json
import logging
from datetime import datetime
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "..", "jiobp_fuel_stations.geojson")

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("jiobp")

def fetch_stations_via_browser():
    with sync_playwright() as p:
        log.info("Launching headless browser...")
        browser = p.chromium.launch(args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            # Add anti-detection scripts
        )
        
        # Overwrite webdriver 
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """)
        
        page = context.new_page()
        log.info("Navigating to Jio-bp locator...")
        
        try:
            # We don't need networkidle. domcontentloaded is enough to execute JS.
            page.goto("https://www.jiobp.com/locate-fuel-station", wait_until="domcontentloaded", timeout=45000)
            log.info("Page loaded. Executing fetch request inside browser context...")
            
            # Use native fetch to get the data, exactly as the browser would.
            # This perfectly inherits cookies, headers, and WAF clearance.
            data = page.evaluate("""
                async () => {
                    try {
                        const response = await fetch('/locatorapi.php', {
                            method: 'POST',
                            headers: {
                                'X-Requested-With': 'XMLHttpRequest'
                            }
                        });
                        return await response.json();
                    } catch (e) {
                        return { error: e.toString() };
                    }
                }
            """)
            
            if 'error' in data:
                log.error(f"JavaScript Fetch Error: {data['error']}")
                return []
                
            stations = data.get('RO_Details', [])
            log.info(f"Success! Retrieved {len(stations)} stations via browser fetch.")
            return stations
            
        except Exception as e:
            log.error(f"Playwright error: {e}")
            return []
        finally:
            browser.close()

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
        "generator": "jiobp_fetcher.py",
        "scraped_at": datetime.utcnow().isoformat() + "Z",
        "total_stations": len(features),
        "brand": "Jio-bp",
        "features": features,
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    log.info(f"GeoJSON exported: {output_path}")
    log.info(f"Total features saved: {len(features)}")

if __name__ == "__main__":
    log.info("Starting Jio-bp Scraper...")
    stations = fetch_stations_via_browser()
    if stations:
        export_geojson(stations, OUTPUT_FILE)
