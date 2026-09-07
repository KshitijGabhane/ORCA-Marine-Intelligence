import os
import json
import math
from datetime import datetime, timezone


# Project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "fisheries",
    "pfz_data.json"
)


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate approximate distance between two coordinates in km.
    """

    R = 6371  # Earth radius in km

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    dlat = lat2 - lat1
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def fisheries_agent(latitude: float, longitude: float) -> dict:

    # Check dataset
    if not os.path.exists(DATA_PATH):

        return {
            "agent": "fisheries",
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "result": {},
            "risk": "UNKNOWN",
            "confidence": 0.0,
            "source": "INCOIS PFZ Advisory",
            "status": "error",
            "message": "PFZ dataset not found"
        }

    # Read PFZ dataset
    try:

        with open(DATA_PATH, "r", encoding="utf-8") as f:
            pfz_list = json.load(f)

    except Exception as e:

        return {
            "agent": "fisheries",
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "result": {},
            "risk": "UNKNOWN",
            "confidence": 0.0,
            "source": "INCOIS PFZ Advisory",
            "status": "error",
            "message": f"Unable to read PFZ dataset: {str(e)}"
        }

    # Empty dataset
    if not pfz_list:

        return {
            "agent": "fisheries",
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "result": {},
            "risk": "UNKNOWN",
            "confidence": 0.0,
            "source": "INCOIS PFZ Advisory",
            "status": "error",
            "message": "PFZ dataset is empty"
        }

    # Find nearest PFZ
    nearest_pfz = None
    nearest_distance = float("inf")

    for zone in pfz_list:

        pfz_lat = zone.get("latitude")
        pfz_lon = zone.get("longitude")

        if pfz_lat is None or pfz_lon is None:
            continue

        distance = calculate_distance(
            latitude,
            longitude,
            pfz_lat,
            pfz_lon
        )

        if distance < nearest_distance:

            nearest_distance = distance
            nearest_pfz = zone

    # No valid PFZ
    if nearest_pfz is None:

        return {
            "agent": "fisheries",
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "result": {},
            "risk": "UNKNOWN",
            "confidence": 0.0,
            "source": "INCOIS PFZ Advisory",
            "status": "error",
            "message": "No valid PFZ coordinates found"
        }

    # Maximum distance for considering PFZ relevant
    MAX_DISTANCE = 100

    if nearest_distance <= MAX_DISTANCE:

        result_payload = {
            "pfz_found": True,
            "zone_id": nearest_pfz.get("zone_id"),
            "coast": nearest_pfz.get("coast"),
            "latitude": nearest_pfz.get("latitude"),
            "longitude": nearest_pfz.get("longitude"),
            "direction": nearest_pfz.get("direction"),
            "bearing_deg": nearest_pfz.get("bearing_deg"),
            "distance_km": nearest_pfz.get("distance_km"),
            "distance_from_user_km": round(nearest_distance, 2),
            "depth_m": nearest_pfz.get("depth_m"),
            "source": nearest_pfz.get(
                "source",
                "INCOIS PFZ Advisory"
            ),

            # Not provided by the INCOIS table
            "target_species": [],
            "sst_celsius": None,
            "chlorophyll_mg_m3": None
        }

        risk = "LOW"
        confidence = 0.90

    else:

        result_payload = {
            "pfz_found": False,
            "message": "No PFZ found within 100 km",
            "nearest_pfz": nearest_pfz.get("coast"),
            "distance_from_user_km": round(nearest_distance, 2),
            "target_species": [],
            "sst_celsius": None,
            "chlorophyll_mg_m3": None
        }

        risk = "MEDIUM"
        confidence = 0.75

    return {
        "agent": "fisheries",
        "location": {
            "latitude": latitude,
            "longitude": longitude
        },
        "result": result_payload,
        "risk": risk,
        "confidence": confidence,
        "source": "INCOIS PFZ Advisory",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "success"
    }


if __name__ == "__main__":

    # Test location
    latitude = 18.638
    longitude = 72.508

    result = fisheries_agent(
        latitude,
        longitude
    )

    print(json.dumps(result, indent=2))