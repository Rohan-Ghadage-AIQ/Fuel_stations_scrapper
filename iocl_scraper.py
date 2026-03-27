"""
IOCL Fuel Station Scraper
=========================
Scrapes all Indian Oil (IOCL) fuel stations across India
from locator.iocl.com and exports to GeoJSON format.

Strategy:
1. The website is paginated from ?page=1 to ?page=6603
2. We iterate over these pages concurrently using ThreadPoolExecutor.
3. For each listing, extract Name, Address, Phone, Hours, and 
   the Google Maps link (which contains the CID / lat-lon).

Usage:
    python iocl_scraper.py

Output:
    ../iocl_fuel_stations.geojson
"""

import json
import time
import re
import os
import sys
import logging
from datetime import datetime
import concurrent.futures

import requests
from bs4 import BeautifulSoup

# ─── Configuration ───────────────────────────────────────────────────────────

BASE_URL = "https://locator.iocl.com/"
TOTAL_PAGES = 6610  # A safe upper bound based on current locator analysis

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "..", "iocl_fuel_stations.geojson")
PROGRESS_FILE = os.path.join(OUTPUT_DIR, "iocl_progress.json")

# Rate limiting / Threads
MAX_WORKERS = 20           # Number of pages to scrape concurrently
REQUEST_DELAY = 0.5        # Seconds to sleep between thread starts

# Retry config
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-5s │ %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("iocl_scraper")


# ─── Session Setup ───────────────────────────────────────────────────────────

class ScraperSession:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://locator.iocl.com/",
        })

    def safe_request(self, url: str) -> requests.Response | None:
        """Make an HTTP GET with retry logic."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # Add random slight delay to stagger threads
                import random
                time.sleep(REQUEST_DELAY + random.uniform(0, 0.5))
                resp = self.session.get(url, timeout=30)
                if resp.status_code == 200:
                    # The server sometimes returns 200 OK but the page says "Error - IndianOil"
                    if "Error - IndianOil" in resp.text:
                        log.debug(f"Server returned 200 but page is IndianOil Error text. Retrying... ({url})")
                        time.sleep(RETRY_DELAY * attempt)
                        continue
                    return resp
                if resp.status_code == 404:
                    log.debug(f"Page not found (404): {url} - likely past the last page.")
                    return None
            except requests.RequestException as e:
                pass
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
        log.error(f"All {MAX_RETRIES} attempts failed for {url}")
        return None

import threading
# Create a thread-local storage for sessions to reuse TCP connections efficiently
thread_local = threading.local()

def get_session():
    if not getattr(thread_local, "scraper_session", None):
        thread_local.scraper_session = ScraperSession()
    return thread_local.scraper_session


# ─── Progress Management ─────────────────────────────────────────────────────

def load_progress() -> dict:
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"completed_pages": [], "stations": [], "errors": []}

def save_progress(progress: dict):
    # Save to a temporary file first, then rename to prevent corruption
    temp_file = PROGRESS_FILE + ".tmp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
    
    try:
        os.replace(temp_file, PROGRESS_FILE)
    except PermissionError:
        # If the user has the file open in IDE, os.replace fails on Windows.
        # Fallback to direct write.
        try:
            import shutil
            shutil.copyfile(temp_file, PROGRESS_FILE)
        except Exception as e:
            log.warning(f"Failed to overwrite progress file (is it open?): {e}")


# ─── Scraping Logic ──────────────────────────────────────────────────────────

def scrape_page(page_num: int) -> list[dict]:
    """Scrape a single pagination page of locator.iocl.com."""
    session = get_session()
    url = f"{BASE_URL}?page={page_num}"
    
    resp = session.safe_request(url)
    if not resp:
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    page_stations = []

    # Locator uses <div class="store-info-box"> for each petrol pump
    store_cards = soup.find_all('div', class_=re.compile(r'store-info-box'))
    
    if not store_cards:
        # Fallback check - sometimes it's within a specific list
        list_items = soup.find_all('li', class_=lambda c: c and 'outlet' in c.lower())
        
        # If still nothing, it's either an empty page or structure changed
        if not list_items:
            # Let's try finding the standard outlet-name class anywhere
            names = soup.find_all(class_='outlet-name')
            if not names:
                return []
            
            # Reconstruct parents if we just found names
            store_cards = [n.find_parent('li') or n.find_parent('div', class_='store-locator-box') for n in names]
            store_cards = [c for c in store_cards if c]
        else:
            store_cards = list_items

    for card in store_cards:
        try:
            # 1. Name
            name_parts = []
            
            # Check outlet-name li
            name_li = card.find('li', class_='outlet-name')
            if name_li:
                text_div = name_li.find('div', class_='info-text')
                if text_div:
                    name_parts.append(text_div.get_text(strip=True))
                    
            # Check secondary name li (which has icn-outlet icon)
            outlet_icon = card.find('span', class_='icn-outlet')
            if outlet_icon:
                parent_li = outlet_icon.find_parent('li')
                if parent_li:
                    text_div = parent_li.find('div', class_='info-text')
                    if text_div:
                        name_parts.append(text_div.get_text(strip=True))
            
            # Combine names, stripping out generic 'indianoil' prefix if a unique name exists
            unique_names = [n for n in name_parts if n.lower() != 'indianoil']
            if unique_names:
                name = " - ".join(unique_names)
            elif name_parts:
                name = name_parts[0]
            else:
                name = ""

            # 2. Address & Pincode
            address = ""
            addr_li = card.find('li', class_='outlet-address')
            if addr_li:
                text_div = addr_li.find('div', class_='info-text')
                if text_div:
                    address = text_div.get_text(separator=', ', strip=True)
            
            pincode = ""
            pin_match = re.search(r'\b(\d{6})\b', address)
            if pin_match:
                pincode = pin_match.group(1)

            # 3. Phone
            phone = ""
            phone_li = card.find('li', class_='outlet-phone')
            if phone_li:
                phone_a = phone_li.find('a', href=re.compile(r'^tel:'))
                if phone_a:
                    phone = phone_a.get_text(strip=True)

            # 4. Operating Hours
            hours = ""
            time_li = card.find('li', class_=re.compile(r'outlet-timings|outlet-time'))
            if time_li:
                text_div = time_li.find('div', class_='info-text')
                if text_div:
                    hours = text_div.get_text(separator=' ', strip=True)

            # 5. Extract Details URL
            details_url = ""
            details_link = card.find('a', title='Details', href=True)
            if details_link:
                href = details_link['href']
                details_url = href if href.startswith('http') else f"https://locator.iocl.com{href}"

            # 6. Extract Map Link & exact Coordinates from hidden inputs
            map_url = ""
            lat_input = card.find('input', class_='outlet-latitude')
            lon_input = card.find('input', class_='outlet-longitude')
            
            lat, lon = None, None
            try:
                if lat_input and lat_input.get('value'):
                    lat = float(lat_input['value'])
                if lon_input and lon_input.get('value'):
                    lon = float(lon_input['value'])
            except ValueError:
                pass

            map_link = card.find('a', class_='btn-direction', href=True)
            if map_link:
                map_url = map_link['href']

            page_stations.append({
                "name": name,
                "address": address,
                "phone": phone,
                "pincode": pincode,
                "hours": hours,
                "source_url": details_url or url,
                "map_url": map_url,
                "lat": lat,
                "lon": lon
            })
        except Exception as e:
            log.debug(f"Error parsing a card on page {page_num}: {e}")

    return page_stations


# ─── GeoJSON Export ──────────────────────────────────────────────────────────

def export_geojson(stations: list[dict], output_path: str):
    """Export station list to GeoJSON format."""
    features = []
    stations_with_coords = 0
    stations_without_coords = 0

    for s in stations:
        lat = s.get("lat")
        lon = s.get("lon")

        # Create geometry if coordinates exist
        if lat is not None and lon is not None:
            stations_with_coords += 1
            geometry = {
                "type": "Point",
                "coordinates": [lon, lat]
            }
        else:
            stations_without_coords += 1
            # We still keep it in GeoJSON with a null geometry, so the data isn't lost.
            # The frontend can choose to geocode the address or ignore it.
            geometry = None  

        feature = {
            "type": "Feature",
            "properties": {
                "name": s.get("name", ""),
                "brand": "Indian Oil Corporation",
                "brand_code": "IOCL",
                "address": s.get("address", ""),
                "phone": s.get("phone", ""),
                "pincode": s.get("pincode", ""),
                "operating_hours": s.get("hours", ""),
                "amenity": "fuel",
                "source": "locator.iocl.com",
                "source_url": s.get("source_url", ""),
                "map_url": s.get("map_url", "")
            },
            "geometry": geometry,
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "generator": "iocl_scraper.py",
        "scraped_at": datetime.utcnow().isoformat() + "Z",
        "total_stations": len(features),
        "brand": "Indian Oil Corporation Limited (IOCL)",
        "features": features,
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    log.info(f"═══════════════════════════════════════════════")
    log.info(f"  GeoJSON exported: {output_path}")
    log.info(f"  Total features saved: {len(features)}")
    log.info(f"  (With coords: {stations_with_coords}, Missing coords: {stations_without_coords})")
    log.info(f"═══════════════════════════════════════════════")


# ─── Main Executor ───────────────────────────────────────────────────────────

def main():
    log.info("═══════════════════════════════════════════════")
    log.info("  IOCL Fuel Station Scraper")
    log.info("  Source: locator.iocl.com")
    log.info("═══════════════════════════════════════════════")

    progress = load_progress()
    all_stations = progress.get("stations", [])
    completed_pages = set(progress.get("completed_pages", []))

    if all_stations:
        log.info(f"Resuming: {len(all_stations)} stations scraped, {len(completed_pages)} pages done")

    # Determine pages left to scrape
    # Start checking page 1 to see the actual "Last" page number dynamically
    session = ScraperSession()
    resp = session.safe_request(f"{BASE_URL}?page=1")
    actual_total_pages = TOTAL_PAGES
    if resp:
        soup = BeautifulSoup(resp.text, 'html.parser')
        last_link = soup.find('a', string=re.compile('Last', re.I))
        if last_link and 'page=' in last_link['href']:
            match = re.search(r'page=(\d+)', last_link['href'])
            if match:
                actual_total_pages = int(match.group(1))
                log.info(f"Dynamically detected {actual_total_pages} total pages.")

    pages_to_scrape = [p for p in range(1, actual_total_pages + 1) if p not in completed_pages]
    
    if not pages_to_scrape:
        log.info("All pages already scraped!")
        export_geojson(all_stations, OUTPUT_FILE)
        return

    log.info(f"Starting scrape for {len(pages_to_scrape)} remaining pages with {MAX_WORKERS} workers...")

    # Thread-safe counter and lock
    scraped_count = 0
    progress_lock = threading.Lock()

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_page = {executor.submit(scrape_page, p): p for p in pages_to_scrape}
        
        for future in concurrent.futures.as_completed(future_to_page):
            page_num = future_to_page[future]
            try:
                page_stations = future.result()
                
                with progress_lock:
                    if page_stations:
                        all_stations.extend(page_stations)
                        scraped_count += len(page_stations)
                        log.info(f"  [Page {page_num:04d}] ✓ Found {len(page_stations)} stations (Total: {len(all_stations)})")
                    else:
                        log.warning(f"  [Page {page_num:04d}] ⚠ No stations found (Server might have rate-limited)")
                    
                    completed_pages.add(page_num)
                    
                    # Periodically save progress (every 50 pages)
                    if len(completed_pages) % 50 == 0:
                        progress["stations"] = all_stations
                        progress["completed_pages"] = list(completed_pages)
                        save_progress(progress)
                        
            except Exception as e:
                log.error(f"  [Page {page_num:04d}] Error: {e}")
                with progress_lock:
                    progress.setdefault("errors", []).append({"page": page_num, "error": str(e)})

    # Final Progress Save
    progress["stations"] = all_stations
    progress["completed_pages"] = list(completed_pages)
    save_progress(progress)

    # Export
    log.info(f"\nFinal tally: {len(all_stations)} stations collected.")
    export_geojson(all_stations, OUTPUT_FILE)


if __name__ == "__main__":
    main()
