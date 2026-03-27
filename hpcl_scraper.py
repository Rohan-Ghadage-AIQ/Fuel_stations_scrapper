"""
HPCL Fuel Station Scraper
=========================
Scrapes all Hindustan Petroleum (HPCL) fuel stations across India
from petrolpump.hpretail.in and exports to GeoJSON format.

Strategy:
1. Discover all states from the Advanced Search dropdown
2. For each state, discover cities via the API endpoint
3. For each city, scrape the listing page for station links
4. For each station, extract name, address, phone, hours, lat/lon

Usage:
    python hpcl_scraper.py

Output:
    ../hpcl_fuel_stations.geojson
"""

import json
import time
import re
import os
import sys
import logging
from datetime import datetime
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

# ─── Configuration ───────────────────────────────────────────────────────────

BASE_URL = "https://petrolpump.hpretail.in"
CITIES_API = f"{BASE_URL}/getCitiesByMasterOutletIdAndStateName.php"
MASTER_OUTLET_ID = "96681"  # HPCL's master outlet ID on the platform

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "..", "hpcl_fuel_stations.geojson")
PROGRESS_FILE = os.path.join(OUTPUT_DIR, "hpcl_progress.json")

# Rate limiting
REQUEST_DELAY = 0.5        # seconds between requests
CITY_PAGE_DELAY = 0.3      # seconds between city page loads
STATION_PAGE_DELAY = 0.5   # seconds between station detail loads

# Retry config
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-5s │ %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("hpcl_scraper")

# ─── Session Setup ───────────────────────────────────────────────────────────

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE_URL,
})


# ─── Helper Functions ────────────────────────────────────────────────────────

def safe_request(url: str, retries: int = MAX_RETRIES, delay: float = REQUEST_DELAY) -> requests.Response | None:
    """Make an HTTP GET with retry logic and rate limiting."""
    for attempt in range(1, retries + 1):
        try:
            time.sleep(delay)
            resp = session.get(url, timeout=30)
            if resp.status_code == 200:
                return resp
            log.warning(f"HTTP {resp.status_code} for {url} (attempt {attempt}/{retries})")
        except requests.RequestException as e:
            log.warning(f"Request failed for {url}: {e} (attempt {attempt}/{retries})")
        if attempt < retries:
            time.sleep(RETRY_DELAY * attempt)
    log.error(f"All {retries} attempts failed for {url}")
    return None


def slugify(text: str) -> str:
    """Convert text to URL-safe slug (lowercase, hyphens)."""
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def load_progress() -> dict:
    """Load scraping progress from checkpoint file."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"completed_states": [], "stations": [], "errors": []}


def save_progress(progress: dict):
    """Save scraping progress to checkpoint file."""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


# ─── Step 1: Discover States ────────────────────────────────────────────────

def discover_states() -> list[dict]:
    """Get all states from the HPCL locator homepage dropdown."""
    log.info("Discovering states from homepage...")
    resp = safe_request(BASE_URL)
    if not resp:
        log.error("Failed to load homepage")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Find the state dropdown (#OutletState)
    state_select = soup.find('select', {'id': 'OutletState'})
    if not state_select:
        # Try alternate selectors
        state_select = soup.find('select', {'name': 'state'})
    if not state_select:
        # Fallback: search for any select containing state-like options
        for sel in soup.find_all('select'):
            options = sel.find_all('option')
            option_texts = [o.get_text(strip=True).lower() for o in options]
            if any(s in option_texts for s in ['maharashtra', 'delhi', 'karnataka', 'goa']):
                state_select = sel
                break

    if not state_select:
        log.error("Could not find state dropdown on homepage")
        # Fallback: use a hardcoded list of Indian states
        return get_fallback_states()

    states = []
    for option in state_select.find_all('option'):
        value = option.get('value', '').strip()
        text = option.get_text(strip=True)
        if value and text and value.lower() not in ('', 'select', 'select state', '--select--'):
            states.append({"name": text, "slug": slugify(text), "value": value})

    log.info(f"Found {len(states)} states")
    return states


def get_fallback_states() -> list[dict]:
    """Hardcoded Indian states/UTs as fallback."""
    state_names = [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
        "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh",
        "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra",
        "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha",
        "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
        "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
        "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
        "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
    ]
    return [{"name": s, "slug": slugify(s), "value": s} for s in state_names]


# ─── Step 2: Discover Cities for a State ─────────────────────────────────────

def discover_cities(state: dict) -> list[dict]:
    """Get cities for a given state using the HPCL API."""
    state_slug = state["slug"]
    state_name = state.get("value", state["name"])

    # Try the API endpoint first
    api_url = f"{CITIES_API}?master_outlet_id={MASTER_OUTLET_ID}&state_name={quote(state_slug)}"
    resp = safe_request(api_url, delay=CITY_PAGE_DELAY)

    cities = []

    if resp:
        try:
            data = resp.json()
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        city_name = item.get('city_name', item.get('name', '')).strip()
                        if city_name:
                            cities.append({
                                "name": city_name,
                                "slug": slugify(city_name),
                            })
                    elif isinstance(item, str):
                        cities.append({"name": item.strip(), "slug": slugify(item.strip())})
            elif isinstance(data, dict):
                for key, val in data.items():
                    if isinstance(val, str):
                        cities.append({"name": val.strip(), "slug": slugify(val.strip())})
        except (json.JSONDecodeError, ValueError):
            log.warning(f"API returned non-JSON for state {state_name}, trying HTML fallback")

    # Fallback: scrape the state listing page
    if not cities:
        state_page_url = f"{BASE_URL}/location/{state_slug}"
        resp = safe_request(state_page_url, delay=CITY_PAGE_DELAY)
        if resp:
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Look for city links in the page
            for link in soup.find_all('a', href=True):
                href = link['href']
                # Pattern: /location/{state}/{city}
                match = re.match(rf'/location/{re.escape(state_slug)}/([^/]+)', href)
                if match:
                    city_slug = match.group(1)
                    city_name = link.get_text(strip=True) or city_slug.replace('-', ' ').title()
                    cities.append({"name": city_name, "slug": city_slug})

    # Deduplicate
    seen_slugs = set()
    unique_cities = []
    for c in cities:
        if c["slug"] not in seen_slugs and c["slug"]:
            seen_slugs.add(c["slug"])
            unique_cities.append(c)

    log.info(f"  {state['name']}: {len(unique_cities)} cities found")
    return unique_cities


# ─── Step 3: Scrape Station Links from City Page ────────────────────────────

def scrape_city_stations(state: dict, city: dict) -> list[dict]:
    """Scrape all station links and basic info from a city listing page."""
    base_city_url = f"{BASE_URL}/location/{state['slug']}/{city['slug']}"
    
    all_stations = []
    page_num = 1
    
    while True:
        url = base_city_url if page_num == 1 else f"{base_city_url}?page={page_num}"
        resp = safe_request(url, delay=CITY_PAGE_DELAY)
        if not resp:
            break

        soup = BeautifulSoup(resp.text, 'html.parser')
        
        page_stations = []
        # Look for station links — pattern: /{station-slug}/Home
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/Home' in href and '/location/' not in href:
                station_url = href if href.startswith('http') else f"{BASE_URL}{href}"

                name = link.get_text(strip=True)

                # Skip navigation/generic links
                if not name or name.lower() in ('home', 'map', 'details', 'call'):
                    continue

                page_stations.append({
                    "url": station_url,
                    "name": name,
                    "state": state["name"],
                    "city": city["name"],
                })
        
        if not page_stations:
            break
            
        all_stations.extend(page_stations)
        
        # Check if there is a 'Next' page link in pagination
        pagination = soup.find(class_='pagination')
        has_next = False
        if pagination:
            for a in pagination.find_all('a', href=True):
                if a.get_text(strip=True).lower() == 'next':
                    has_next = True
                    break
                    
        if not has_next:
            break
            
        page_num += 1

    # Deduplicate by URL
    seen = set()
    unique = []
    for s in all_stations:
        if s["url"] not in seen:
            seen.add(s["url"])
            unique.append(s)

    return unique


# ─── Step 4: Scrape Station Details ──────────────────────────────────────────

def scrape_station_details(station: dict) -> dict | None:
    """Scrape detailed info for a single station including lat/lon."""
    resp = safe_request(station["url"], delay=STATION_PAGE_DELAY)
    if not resp:
        return None

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Extract coordinates from meta tag: <meta name="geo.position" content="lat; lon">
    lat, lon = None, None
    geo_meta = soup.find('meta', {'name': 'geo.position'})
    if geo_meta:
        content = geo_meta.get('content', '')
        parts = content.split(';')
        if len(parts) == 2:
            try:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
            except ValueError:
                pass

    # Also try ICBM meta tag
    if lat is None:
        icbm_meta = soup.find('meta', {'name': 'ICBM'})
        if icbm_meta:
            content = icbm_meta.get('content', '')
            parts = content.split(',')
            if len(parts) == 2:
                try:
                    lat = float(parts[0].strip())
                    lon = float(parts[1].strip())
                except ValueError:
                    pass

    # Extract address
    address = ""
    addr_elem = soup.find('address') or soup.find(class_=re.compile(r'address|addr', re.I))
    if addr_elem:
        address = addr_elem.get_text(separator=', ', strip=True)
    else:
        # Try looking for structured address in the page
        for elem in soup.find_all(['p', 'span', 'div']):
            text = elem.get_text(strip=True)
            if re.search(r'\d{6}', text) and len(text) > 20:  # Has pincode
                address = text
                break

    # Extract phone
    phone = ""
    tel_link = soup.find('a', href=re.compile(r'^tel:'))
    if tel_link:
        phone = tel_link.get_text(strip=True) or tel_link['href'].replace('tel:', '')

    # Extract operating hours
    hours = ""
    for elem in soup.find_all(['span', 'div', 'p']):
        text = elem.get_text(strip=True)
        if re.search(r'(Open\s+(24|until)|Hours)', text, re.I):
            hours = text
            break

    # Extract pincode from address
    pincode = ""
    pin_match = re.search(r'\b(\d{6})\b', address)
    if pin_match:
        pincode = pin_match.group(1)

    # Extract the station name from the page title if not already set
    name = station.get("name", "")
    title_tag = soup.find('title')
    if title_tag:
        title_text = title_tag.get_text(strip=True)
        # Usually format: "Station Name | Petrol Pump in City"
        title_name = title_text.split('|')[0].strip()
        if title_name and len(title_name) > len(name):
            name = title_name

    return {
        "name": name,
        "state": station["state"],
        "city": station["city"],
        "address": address,
        "phone": phone,
        "pincode": pincode,
        "hours": hours,
        "lat": lat,
        "lon": lon,
        "source_url": station["url"],
    }


# ─── GeoJSON Export ──────────────────────────────────────────────────────────

def export_geojson(stations: list[dict], output_path: str):
    """Export station list to GeoJSON format."""
    features = []

    stations_with_coords = 0
    stations_without_coords = 0

    for s in stations:
        lat = s.get("lat")
        lon = s.get("lon")

        if lat is not None and lon is not None:
            stations_with_coords += 1
            geometry = {
                "type": "Point",
                "coordinates": [lon, lat]  # GeoJSON is [lon, lat]
            }
        else:
            stations_without_coords += 1
            geometry = None  # Will skip these

        if geometry is None:
            continue

        feature = {
            "type": "Feature",
            "properties": {
                "name": s.get("name", ""),
                "brand": "Hindustan Petroleum",
                "brand_code": "HPCL",
                "state": s.get("state", ""),
                "city": s.get("city", ""),
                "address": s.get("address", ""),
                "phone": s.get("phone", ""),
                "pincode": s.get("pincode", ""),
                "operating_hours": s.get("hours", ""),
                "amenity": "fuel",
                "source": "petrolpump.hpretail.in",
                "source_url": s.get("source_url", ""),
            },
            "geometry": geometry,
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "generator": "hpcl_scraper.py",
        "scraped_at": datetime.utcnow().isoformat() + "Z",
        "total_stations": len(features),
        "brand": "Hindustan Petroleum Corporation Limited (HPCL)",
        "features": features,
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    log.info(f"═══════════════════════════════════════════════")
    log.info(f"  GeoJSON exported: {output_path}")
    log.info(f"  Stations with coordinates: {stations_with_coords}")
    log.info(f"  Stations without coordinates (skipped): {stations_without_coords}")
    log.info(f"  Total features in GeoJSON: {len(features)}")
    log.info(f"═══════════════════════════════════════════════")


# ─── Main Scraper ────────────────────────────────────────────────────────────

def main():
    log.info("═══════════════════════════════════════════════")
    log.info("  HPCL Fuel Station Scraper")
    log.info("  Source: petrolpump.hpretail.in")
    log.info("═══════════════════════════════════════════════")

    # Load any previous progress
    progress = load_progress()
    all_stations = progress.get("stations", [])
    completed_states = set(progress.get("completed_states", []))

    if all_stations:
        log.info(f"Resuming from checkpoint: {len(all_stations)} stations already scraped, "
                 f"{len(completed_states)} states completed")

    # Step 1: Discover states
    states = discover_states()
    if not states:
        log.error("No states found. Exiting.")
        sys.exit(1)

    log.info(f"\nStarting scrape for {len(states)} states...")
    log.info(f"Skipping {len(completed_states)} already-completed states\n")

    # Step 2-4: For each state → cities → stations → details
    for state_idx, state in enumerate(states, 1):
        if state["name"] in completed_states:
            continue

        log.info(f"\n[{state_idx}/{len(states)}] ── {state['name']} ──")

        # Discover cities
        cities = discover_cities(state)
        if not cities:
            log.warning(f"  No cities found for {state['name']}")
            completed_states.add(state["name"])
            continue

        state_station_count = 0

        for city_idx, city in enumerate(cities, 1):
            log.info(f"  [{city_idx}/{len(cities)}] {city['name']}...")

            # Get station links from city page
            station_links = scrape_city_stations(state, city)
            if not station_links:
                continue

            log.info(f"    Found {len(station_links)} station(s)")

            # Scrape each station's details concurrently
            import concurrent.futures
            
            # Using max_workers=15 to balance speed without overwhelming the server
            with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
                # Submit all station tasks
                future_to_station = {executor.submit(scrape_station_details, s_link): s_link for s_link in station_links}
                
                s_idx = 1
                for future in concurrent.futures.as_completed(future_to_station):
                    station_link = future_to_station[future]
                    try:
                        details = future.result()
                        if details:
                            all_stations.append(details)
                            state_station_count += 1

                            if details.get("lat"):
                                coord_str = f"({details['lat']:.4f}, {details['lon']:.4f})"
                            else:
                                coord_str = "(no coords)"

                            log.info(f"    [{s_idx}/{len(station_links)}] "
                                     f"{details['name'][:40]} {coord_str}")
                        else:
                            progress.setdefault("errors", []).append({
                                "url": station_link["url"],
                                "error": "Failed to scrape details"
                            })
                    except Exception as e:
                        log.error(f"    Error scraping {station_link['url']}: {e}")
                        progress.setdefault("errors", []).append({
                            "url": station_link["url"],
                            "error": str(e)
                        })
                    s_idx += 1

            # Save progress after each city
            progress["stations"] = all_stations
            progress["completed_states"] = list(completed_states)
            save_progress(progress)

        log.info(f"  ✓ {state['name']} complete: {state_station_count} stations")
        completed_states.add(state["name"])

        # Save progress after each state
        progress["stations"] = all_stations
        progress["completed_states"] = list(completed_states)
        save_progress(progress)

    # Export final GeoJSON
    log.info(f"\nTotal stations scraped: {len(all_stations)}")
    export_geojson(all_stations, OUTPUT_FILE)

    # Summary
    log.info(f"\n{'='*50}")
    log.info(f"  SCRAPING COMPLETE")
    log.info(f"  Total stations: {len(all_stations)}")
    log.info(f"  States covered: {len(completed_states)}")
    log.info(f"  Errors: {len(progress.get('errors', []))}")
    log.info(f"  Output: {OUTPUT_FILE}")
    log.info(f"{'='*50}")


if __name__ == "__main__":
    main()
