import requests
import json
import os

# ============================================================
# OFFICIAL WDPA MARINE & COASTAL DATA
# UNEP-WCMC / IUCN Protected Planet
# ============================================================

url = (
    "https://data-gis.unep-wcmc.org/server/rest/services/"
    "ProtectedSites/WDPA_Marine_and_Coastal/MapServer/1/query"
)

params = {
    "where": "iso3 = 'IND'",
    "outFields": "*",
    "returnGeometry": "true",
    "outSR": "4326",
    "f": "geojson"
}

print("Downloading India's marine protected areas...")

response = requests.get(
    url,
    params=params,
    timeout=120
)

if response.status_code != 200:
    print("Download failed.")
    print("HTTP Status:", response.status_code)
    print(response.text)
    exit()

try:
    data = response.json()
except Exception:
    print("Server did not return valid JSON.")
    print(response.text)
    exit()

# Check whether features were returned
features = data.get("features", [])

print("Protected-area features received:", len(features))

if len(features) == 0:
    print("No Indian marine protected areas were returned.")
    print("Server response:")
    print(json.dumps(data, indent=2))
    exit()

# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

output_dir = os.path.join(
    "data",
    "geofences"
)

os.makedirs(
    output_dir,
    exist_ok=True
)

# ============================================================
# SAVE GEOJSON
# ============================================================

output_file = os.path.join(
    output_dir,
    "protected_areas.geojson"
)

with open(
    output_file,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        data,
        file,
        indent=2
    )

print()
print("==============================================")
print("SUCCESS")
print("==============================================")
print("India's marine protected-area data downloaded.")
print()
print("File created:")
print(output_file)
print()
print("Number of protected areas:", len(features))
