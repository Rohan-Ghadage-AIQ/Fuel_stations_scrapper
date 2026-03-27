import requests, json

# Probe MGL API
print("=== MGL ===")
try:
    r = requests.post("https://www.mahanagargas.com:3000/outlet/cngfilling",
        json={"Location": "", "AreaName": "", "VehicleType": ""},
        headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"},
        timeout=15)
    print(f"Status: {r.status_code}")
    print(f"Type: {type(r.json())}")
    d = r.json()
    if isinstance(d, list):
        print(f"Array of {len(d)} items")
        if d: print(f"Keys: {list(d[0].keys())}")
        if d: print(f"Sample: {json.dumps(d[0], ensure_ascii=False)[:300]}")
    elif isinstance(d, dict):
        print(f"Dict keys: {list(d.keys())}")
        for k, v in d.items():
            if isinstance(v, list) and v:
                print(f"  {k}: list of {len(v)}, keys={list(v[0].keys()) if isinstance(v[0], dict) else 'N/A'}")
                print(f"  Sample: {json.dumps(v[0], ensure_ascii=False)[:300]}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== Gujarat Gas ===")
try:
    r = requests.post("https://iconnect.gujaratgas.com/Portal/FootPrintPrelogin.aspx/LoadFootPrintsAjax",
        json={"lat": "23.0225", "lng": "72.5714"},
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "Mozilla/5.0"},
        timeout=15)
    print(f"Status: {r.status_code}")
    d = r.json()
    print(f"Type: {type(d)}")
    if isinstance(d, dict):
        print(f"Keys: {list(d.keys())}")
        dd = d.get("d")
        if dd:
            print(f"  d type: {type(dd)}")
            if isinstance(dd, str):
                parsed = json.loads(dd)
                print(f"  Parsed d: {type(parsed)}, len={len(parsed) if isinstance(parsed, list) else 'N/A'}")
                if isinstance(parsed, list) and parsed:
                    print(f"  Keys: {list(parsed[0].keys())}")
                    print(f"  Sample: {json.dumps(parsed[0], ensure_ascii=False)[:300]}")
            elif isinstance(dd, list):
                print(f"  d: list of {len(dd)}")
                if dd: print(f"  Keys: {list(dd[0].keys())}")
except Exception as e:
    print(f"Error: {e}")
