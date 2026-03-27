# 🛢️ India Fuel Stations Scraper

A collection of purpose-built Python scrapers that collect **fuel station data across India** from official OMC (Oil Marketing Company) locators and APIs, exporting everything to standard **GeoJSON** format.

---

## 📦 Scrapers

| Script | Brand | Source | Method | Output |
|--------|-------|--------|--------|--------|
| `hpcl_scraper.py` | Hindustan Petroleum (HPCL) | petrolpump.hpretail.in | HTML scraping, state→city→station | `hpcl_fuel_stations.geojson` |
| `iocl_scraper.py` | Indian Oil (IOCL) | locator.iocl.com | Paginated HTML (~6600 pages) | `iocl_fuel_stations.geojson` |
| `bpcl_scraper.py` | Bharat Petroleum (BPCL) | api.cep.bpcl.in | Grid-based REST API (HelloBPCL CEP) | `bpcl_fuel_stations.geojson` |
| `nayara_scraper.py` | Nayara Energy | nayaraenergy.com | Grid-based internal API + Cloudflare bypass | `nayara_fuel_stations.geojson` |
| `jiobp_scraper.py` | Jio-bp (Reliance) | jiobp.com | Unprotected static JSON dump | `jiobp_fuel_stations.geojson` |
| `shell_scraper.py` | Shell India | shellgsllocator.geoapp.me | Grid-based public REST API | `shell_fuel_stations.geojson` |
| `totalenergies_scraper.py` | TotalEnergies India | OpenStreetMap (Overpass) | OSM Overpass API queries | `totalenergies_fuel_stations.geojson` |
| `cng_scraper.py` | CNG Stations (Multi-Source) | MGL, Gujarat Gas, IGL, OSM | Multi-source API + HTML scraping | `cng_stations.geojson` |

---

## ⚙️ Installation

```bash
# Core dependencies
pip install requests beautifulsoup4

# Required for Nayara & Jio-bp (Cloudflare bypass)
pip install curl_cffi
```

---

## 🚀 Usage

Run any scraper independently:

```bash
python hpcl_scraper.py
python iocl_scraper.py
python bpcl_scraper.py
python nayara_scraper.py
python jiobp_scraper.py
python shell_scraper.py
python totalenergies_scraper.py
python cng_scraper.py
```

Each script is fully self-contained — no configuration needed.

---

## ✨ Features

- **Checkpoint / Resume** — Progress is saved to `*_progress.json` after every city/page/grid point. Re-run anytime to continue from where it left off.
- **Deduplication** — Stations are deduplicated by coordinate key or unique ID before export.
- **Rate Limiting** — Configurable delays between requests to avoid hammering servers.
- **Retry Logic** — Automatic retries with exponential back-off on network errors.
- **Cloudflare Bypass** — `nayara_scraper.py` and `jiobp_scraper.py` use `curl_cffi` with Chrome impersonation.
- **Concurrent Scraping** — `iocl_scraper.py`, `hpcl_scraper.py`, and `nayara_scraper.py` use `ThreadPoolExecutor` for faster collection.
- **GeoJSON Export** — Standard GeoJSON `FeatureCollection` with consistent properties: `name`, `brand`, `brand_code`, `address`, `state`, `city`, `phone`, `amenity`, `source`.

---

## 📂 GeoJSON Output Format

Each output file follows this structure:

```json
{
  "type": "FeatureCollection",
  "generator": "hpcl_scraper.py",
  "scraped_at": "2025-01-01T00:00:00Z",
  "total_stations": 14000,
  "features": [
    {
      "type": "Feature",
      "properties": {
        "name": "Station Name",
        "brand": "Hindustan Petroleum",
        "brand_code": "HPCL",
        "address": "...",
        "state": "Maharashtra",
        "city": "Mumbai",
        "phone": "...",
        "amenity": "fuel",
        "source": "petrolpump.hpretail.in"
      },
      "geometry": { "type": "Point", "coordinates": [72.8777, 19.0760] }
    }
  ]
}
```

> **Note:** GeoJSON files are excluded from Git due to size (up to ~28 MB each). Use [Git LFS](https://git-lfs.com/) to version them: `git lfs track "*.geojson"`.

---

## 📊 CNG Scraper Sources

`cng_scraper.py` aggregates CNG stations from multiple operators:

| Source | Operator | Region |
|--------|----------|--------|
| `mahanagargas.com` API | MGL | Mumbai & MMR |
| `gujaratgas.com` API | Gujarat Gas | Gujarat |
| `iglonline.net` HTML | IGL | Delhi/NCR |
| OSM Overpass API | Various | Pan-India |
