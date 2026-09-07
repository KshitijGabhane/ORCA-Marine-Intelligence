import requests

url = "https://geo.vliz.be/geoserver/MarineRegions/wfs"

params = {
    "service": "WFS",
    "version": "1.0.0",
    "request": "GetFeature",
    "typeName": "eez",
    "cql_filter": "mrgid=8480",
    "outputFormat": "application/json"
}

response = requests.get(url, params=params, timeout=60)

if response.status_code != 200:
    print("Download failed")
    print(response.status_code)
    print(response.text)
    exit()

data = response.json()

with open(
    "data/geofences/maritime_boundary.geojson",
    "w",
    encoding="utf-8"
) as file:
    import json
    json.dump(data, file, indent=2)

print("India EEZ GeoJSON downloaded successfully.")
print("File: data/geofences/maritime_boundary.geojson")
