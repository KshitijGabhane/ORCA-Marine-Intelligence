import json
import os

# ============================================================
# ORCA - Restricted Areas GeoJSON
# ============================================================
# This file creates the restricted-area GeoJSON structure
# expected by marine_safety_service.py.
#
# IMPORTANT:
# Do NOT add random/fake restricted-area coordinates here.
# Real restricted zones should be added from official
# maritime/navigation sources.
# ============================================================

output_dir = os.path.join("data", "geofences")
os.makedirs(output_dir, exist_ok=True)

output_file = os.path.join(
    output_dir,
    "restricted_areas.geojson"
)

geojson_data = {
    "type": "FeatureCollection",
    "features": []
}

with open(
    output_file,
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        geojson_data,
        file,
        indent=2
    )

print()
print("==============================================")
print("ORCA RESTRICTED AREAS")
print("==============================================")
print()
print("File created successfully:")
print(output_file)
print()
print("Current restricted-area features: 0")
print()
print("No fake coordinates were added.")
print("Add verified official restricted-zone polygons")
print("when their coordinates are available.")
print()