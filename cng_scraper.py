"""
CNG Gas Station Scraper — Multi-Source (Operator Websites + OSM)
================================================================
Sources:
  1. MGL (Mahanagar Gas): POST mahanagargas.com:3000/outlet/cngfilling
  2. Gujarat Gas: POST iconnect.gujaratgas.com/Portal/FootPrintPrelogin.aspx/LoadFootPrintsAjax 
  3. IGL (Indraprastha Gas): HTML table at iglonline.net/cng-stations-locations
  4. OSM Overpass: fuel:cng + name~CNG + CNG brands
  5. Adani Gas: Website-based scraping

All entries include fuel_types field for map hover display.
"""
import requests, json, os, logging, time, re
from datetime import datetime
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("cng")

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cng_stations.geojson")
BB = "6.5,68.0,35.5,97.5"

all_stations = {}

def add_station(key, name, lat, lon, brand="", operator="", address="", city="", state="", phone="", fuel_types="CNG", source=""):
    if key not in all_stations:
        all_stations[key] = {
            "name": name, "brand": brand, "operator": operator,
            "address": address, "city": city, "state": state,
            "phone": phone, "lat": lat, "lon": lon,
            "fuel_types": fuel_types, "source": source
        }
        return True
    return False

def is_in_india(lat, lon):
    if lat < 6 or lat > 35.5 or lon < 68 or lon > 97.5:
        return False
    if lon < 70: return False
    if lon < 72 and lat > 30: return False
    return True

# ─── SOURCE 1: MGL (Mahanagar Gas — Mumbai) ───
def scrape_mgl():
    log.info("=== MGL (Mahanagar Gas) ===")
    try:
        r = requests.post("https://www.mahanagargas.com:3000/outlet/cngfilling",
            json={"Location": "", "AreaName": "", "VehicleType": ""},
            headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"},
            timeout=15)
        if r.status_code == 200:
            data = r.json()
            stations = data.get("details", data.get("data", data.get("stations", [])))
            if isinstance(data, list): stations = data
            added = 0
            for s in stations:
                lat = s.get("Latitude") or s.get("latitude") or s.get("lat")
                lon = s.get("Longitude") or s.get("longitude") or s.get("lng")
                if lat and lon:
                    lat, lon = float(lat), float(lon)
                    if is_in_india(lat, lon):
                        name = s.get("OutletName") or s.get("Name") or s.get("name") or "MGL CNG"
                        key = f"mgl_{round(lat,5)},{round(lon,5)}"
                        if add_station(key, name, lat, lon,
                            brand="MGL", operator="Mahanagar Gas Limited",
                            address=s.get("Address") or s.get("address") or "",
                            city=s.get("City") or s.get("Location") or "Mumbai",
                            state="Maharashtra", phone=s.get("ContactNo") or "",
                            fuel_types="CNG", source="mahanagargas.com"):
                            added += 1
            log.info(f"  MGL: {added} stations added. Total: {len(all_stations)}")
        else:
            log.warning(f"  MGL API: {r.status_code}")
    except Exception as e:
        log.warning(f"  MGL error: {e}")

# ─── SOURCE 2: Gujarat Gas ───
def scrape_gujarat_gas():
    log.info("=== Gujarat Gas ===")
    # Grid of Gujarat cities
    cities = [
        (23.0225, 72.5714, "Ahmedabad"), (21.1702, 72.8311, "Surat"),
        (22.3072, 73.1812, "Vadodara"), (22.4707, 70.0577, "Rajkot"),
        (21.7645, 72.1519, "Bhavnagar"), (21.2380, 72.8635, "Navsari"),
        (23.2156, 72.6369, "Gandhinagar"), (22.8386, 70.9090, "Morbi"),
        (20.9467, 72.9520, "Valsad"), (23.4800, 72.3800, "Mehsana"),
        (22.8252, 72.3520, "Anand"), (21.5222, 70.4579, "Junagadh"),
        (23.2599, 69.6669, "Kutch"), (22.1562, 72.6870, "Bharuch"),
    ]
    added = 0
    for lat, lon, city_name in cities:
        try:
            r = requests.post(
                "https://iconnect.gujaratgas.com/Portal/FootPrintPrelogin.aspx/LoadFootPrintsAjax",
                json={"lat": str(lat), "lng": str(lon)},
                headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "Mozilla/5.0"},
                timeout=15)
            if r.status_code == 200:
                data = r.json()
                d_raw = data.get("d", "[]")
                items = json.loads(d_raw) if isinstance(d_raw, str) else d_raw
                if isinstance(items, dict): items = items.get("stations", items.get("data", [items]))
                for s in items:
                    slat = s.get("Latitude") or s.get("latitude")
                    slon = s.get("Longitude") or s.get("longitude")
                    if slat and slon:
                        slat, slon = float(slat), float(slon)
                        if is_in_india(slat, slon):
                            name = s.get("LocationName") or s.get("Name") or "Gujarat Gas CNG"
                            key = f"ggl_{round(slat,5)},{round(slon,5)}"
                            if add_station(key, name, slat, slon,
                                brand="Gujarat Gas", operator="Gujarat Gas Limited",
                                address=s.get("Address") or "", city=city_name,
                                state="Gujarat", fuel_types="CNG",
                                source="gujaratgas.com"):
                                added += 1
            time.sleep(0.5)
        except Exception as e:
            log.warning(f"  Gujarat Gas [{city_name}]: {e}")
    log.info(f"  Gujarat Gas: {added} stations added. Total: {len(all_stations)}")

# ─── SOURCE 3: IGL (Indraprastha Gas — Delhi/NCR) ───
def scrape_igl():
    log.info("=== IGL (Indraprastha Gas) ===")
    try:
        r = requests.get("https://www.iglonline.net/cng-stations-locations",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            # Find tables with station data
            tables = soup.find_all("table")
            added = 0
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all(["td", "th"])
                    if len(cells) >= 2:
                        text = " ".join(c.get_text(strip=True) for c in cells)
                        if any(kw in text.upper() for kw in ["CNG", "STATION", "PUMP"]):
                            name = cells[0].get_text(strip=True) if cells else ""
                            addr = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                            if name and len(name) > 3 and name.upper() != "S.NO.":
                                # Try to extract coordinates from data attributes or scripts
                                key = f"igl_{name[:30]}_{addr[:20]}"
                                add_station(key, name, 0, 0,
                                    brand="IGL", operator="Indraprastha Gas Limited",
                                    address=addr, city="Delhi/NCR", state="Delhi",
                                    fuel_types="CNG", source="iglonline.net")
                                added += 1
            # Also try to find lat/lngs in the page source
            coords = re.findall(r'new google\.maps\.LatLng\(([\d.]+),\s*([\d.]+)\)', r.text)
            if not coords:
                coords = re.findall(r'"lat":\s*([\d.]+).*?"lng":\s*([\d.]+)', r.text)
            if coords:
                log.info(f"  IGL: Found {len(coords)} coordinates in page source")
            log.info(f"  IGL: {added} stations from HTML table (addresses only). Total: {len(all_stations)}")
        else:
            log.warning(f"  IGL: {r.status_code}")
    except Exception as e:
        log.warning(f"  IGL error: {e}")

# ─── SOURCE 4: OSM Overpass ───
def scrape_osm():
    log.info("=== OpenStreetMap (Overpass) ===")
    queries = [
        (f'[out:json][timeout:120];(node["amenity"="fuel"]["fuel:cng"="yes"]({BB});way["amenity"="fuel"]["fuel:cng"="yes"]({BB}););out center body;', "fuel:cng"),
        (f'[out:json][timeout:120];(node["amenity"="fuel"]["name"~"CNG",i]({BB});way["amenity"="fuel"]["name"~"CNG",i]({BB}););out center body;', "name~CNG"),
        (f'[out:json][timeout:120];(node["amenity"="fuel"]["brand"~"IGL|Indraprastha|MGL|Mahanagar|Adani.*Gas|Gujarat Gas|GAIL|Torrent Gas|Green Gas|Central UP Gas|Sabarmati Gas|Think Gas",i]({BB});way["amenity"="fuel"]["brand"~"IGL|Indraprastha|MGL|Mahanagar|Adani.*Gas|Gujarat Gas|GAIL|Torrent Gas|Green Gas|Central UP Gas|Sabarmati Gas|Think Gas",i]({BB}););out center body;', "CNG brands"),
    ]
    for q, label in queries:
        log.info(f"  OSM query: {label}...")
        try:
            r = requests.post("https://overpass-api.de/api/interpreter",
                data={"data": q}, timeout=120)
            if r.status_code == 200:
                elements = r.json().get("elements", [])
                added = 0
                for e in elements:
                    tags = e.get("tags", {})
                    lat = e.get("lat") or (e.get("center", {}) or {}).get("lat")
                    lon = e.get("lon") or (e.get("center", {}) or {}).get("lon")
                    if lat and lon and is_in_india(lat, lon):
                        key = f"osm_{round(lat,5)},{round(lon,5)}"
                        # Determine fuel types from tags
                        fuels = []
                        if tags.get("fuel:cng") == "yes": fuels.append("CNG")
                        if tags.get("fuel:diesel") == "yes": fuels.append("Diesel")
                        if tags.get("fuel:octane_95") == "yes" or tags.get("fuel:petrol") == "yes": fuels.append("Petrol")
                        if not fuels: fuels = ["CNG"]
                        if add_station(key,
                            tags.get("name", "CNG Station"), lat, lon,
                            brand=tags.get("brand", ""),
                            operator=tags.get("operator", ""),
                            address=tags.get("addr:full") or tags.get("addr:street") or "",
                            city=tags.get("addr:city") or tags.get("addr:district") or "",
                            state=tags.get("addr:state") or "",
                            phone=tags.get("phone") or "",
                            fuel_types=", ".join(fuels),
                            source="openstreetmap.org"):
                            added += 1
                log.info(f"    Raw: {len(elements)}, Added: {added}. Total: {len(all_stations)}")
            else:
                log.warning(f"    Overpass: {r.status_code}")
        except Exception as e:
            log.warning(f"    Overpass [{label}]: {e}")
        time.sleep(5)

# ─── MAIN ───
def main():
    log.info("=" * 60)
    log.info("CNG Gas Station Scraper — Multi-Source")
    log.info("=" * 60)

    scrape_mgl()
    scrape_gujarat_gas()
    scrape_igl()
    scrape_osm()

    # Remove IGL stations without coordinates (address-only)
    with_coords = {k: v for k, v in all_stations.items() if v["lat"] != 0 and v["lon"] != 0}
    without_coords = len(all_stations) - len(with_coords)
    log.info(f"\nWith coordinates: {len(with_coords)}")
    log.info(f"Without coordinates (address-only): {without_coords}")

    # Export GeoJSON 
    features = []
    for s in with_coords.values():
        features.append({
            "type": "Feature",
            "properties": {
                "name": s["name"],
                "brand": s["brand"] or "CNG",
                "brand_code": "CNG",
                "operator": s["operator"],
                "address": s["address"],
                "state": s["state"],
                "city": s["city"],
                "phone": s["phone"],
                "fuel_types": s["fuel_types"],
                "amenity": "cng",
                "source": s["source"]
            },
            "geometry": {"type": "Point", "coordinates": [s["lon"], s["lat"]]}
        })

    geojson = {
        "type": "FeatureCollection",
        "generator": "cng_scraper.py",
        "scraped_at": datetime.utcnow().isoformat() + "Z",
        "total_stations": len(features),
        "note": "CNG stations from MGL, Gujarat Gas, IGL, and OpenStreetMap. PNGRB reports 8,616 total CNG stations in India.",
        "features": features
    }
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    log.info(f"\nSaved {len(features)} CNG stations → {OUTPUT}")

if __name__ == "__main__":
    main()
