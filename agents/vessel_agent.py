import os
import sys
import math
from datetime import datetime, timezone

# ============================================================
# ORCA PROJECT ROOT
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(0, BASE_DIR)

# ============================================================
# IMPORT LIVE AIS CLIENT
# ============================================================

from data_sources.ais_client import get_nearby_vessels


# ============================================================
# HAVERSINE DISTANCE
# ============================================================

def calculate_distance_km(
    lat1,
    lon1,
    lat2,
    lon2
):
    """
    Calculate distance between two GPS coordinates.
    """

    R = 6371.0

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(lat1_rad)
        *
        math.cos(lat2_rad)
        *
        math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return R * c


# ============================================================
# VESSEL AGENT
# ============================================================

def vessel_agent(
    latitude: float,
    longitude: float,
    radius_degree: float = 0.5,
    timeout: int = 10
):
    """
    Get live nearby AIS vessels and analyze
    vessel traffic around the user's location.
    """

    try:

        # ----------------------------------------------------
        # GET LIVE AIS VESSELS
        # ----------------------------------------------------

        vessels = get_nearby_vessels(
            latitude=latitude,
            longitude=longitude,
            radius_degree=radius_degree,
            timeout=timeout
        )

        nearby_vessels = []

        # ----------------------------------------------------
        # CALCULATE DISTANCE FROM USER
        # ----------------------------------------------------

        for vessel in vessels:

            vessel_lat = vessel.get("latitude")
            vessel_lon = vessel.get("longitude")

            if vessel_lat is None or vessel_lon is None:
                continue

            distance = calculate_distance_km(
                latitude,
                longitude,
                vessel_lat,
                vessel_lon
            )

            vessel["distance_km"] = round(
                distance,
                2
            )

            nearby_vessels.append(vessel)

        # ----------------------------------------------------
        # SORT NEAREST FIRST
        # ----------------------------------------------------

        nearby_vessels.sort(
            key=lambda vessel: vessel["distance_km"]
        )

        # ----------------------------------------------------
        # VESSEL COUNT
        # ----------------------------------------------------

        vessel_count = len(
            nearby_vessels
        )

        # ----------------------------------------------------
        # TRAFFIC DENSITY
        # ----------------------------------------------------

        if vessel_count > 5:

            traffic_density = "HIGH"

        elif vessel_count > 0:

            traffic_density = "MODERATE"

        else:

            traffic_density = "LOW"

        # ----------------------------------------------------
        # CLOSEST VESSEL
        # ----------------------------------------------------

        if nearby_vessels:

            closest_distance = nearby_vessels[0][
                "distance_km"
            ]

        else:

            closest_distance = None

        # ----------------------------------------------------
        # RISK LEVEL
        # ----------------------------------------------------

        if closest_distance is None:

            risk_level = "LOW"

        elif closest_distance <= 1:

            risk_level = "HIGH"

        elif closest_distance <= 3:

            risk_level = "MEDIUM"

        else:

            risk_level = "LOW"

        # ----------------------------------------------------
        # FINAL RESULT
        # ----------------------------------------------------

        return {

            "status": "success",

            "agent": "vessel",

            "location": {

                "latitude": latitude,

                "longitude": longitude

            },

            "result": {

                "nearby_vessels_count":
                    vessel_count,

                "traffic_density":
                    traffic_density,

                "closest_vessel_distance_km":
                    closest_distance,

                "nearby_vessels":
                    nearby_vessels

            },

            "risk": risk_level,

            "confidence": 0.92,

            "source":
                "AISStream Real-Time AIS",

            "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat()

        }

    except Exception as e:

        # ----------------------------------------------------
        # ERROR RESPONSE
        # ----------------------------------------------------

        return {

            "status": "error",

            "agent": "vessel",

            "location": {

                "latitude": latitude,

                "longitude": longitude

            },

            "result": {

                "nearby_vessels_count": 0,

                "traffic_density": "UNKNOWN",

                "closest_vessel_distance_km": None,

                "nearby_vessels": []

            },

            "risk": "UNKNOWN",

            "confidence": 0,

            "source":
                "AISStream Real-Time AIS",

            "error": str(e),

            "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat()

        }


# ============================================================
# TEST VESSEL AGENT
# ============================================================

if __name__ == "__main__":

    print("\n======================================")
    print("        ORCA VESSEL AGENT")
    print("======================================\n")

    # --------------------------------------------------------
    # TEST LOCATION
    # --------------------------------------------------------

    try:

        latitude = float(
            input("Enter latitude: ")
        )

        longitude = float(
            input("Enter longitude: ")
        )

    except ValueError:

        print(
            "\nInvalid latitude or longitude."
        )

        sys.exit()

    print(
        "\nRunning Vessel Agent...\n"
    )

    # --------------------------------------------------------
    # RUN AGENT
    # --------------------------------------------------------

    result = vessel_agent(
        latitude=latitude,
        longitude=longitude,
        radius_degree=2,
        timeout=120
    )

    # --------------------------------------------------------
    # PRINT COMPLETE RESULT
    # --------------------------------------------------------

    print(
        "\n======================================"
    )

    print("Status:", result["status"])

    print("Agent:", result["agent"])

    print("Risk:", result["risk"])

    print("Confidence:", result["confidence"])

    print("Source:", result["source"])

    print(
        "======================================\n"
    )

    # --------------------------------------------------------
    # VESSEL INFORMATION
    # --------------------------------------------------------

    if result["status"] == "success":

        data = result["result"]

        print(
            "Nearby vessels:",
            data["nearby_vessels_count"]
        )

        print(
            "Traffic density:",
            data["traffic_density"]
        )

        print(
            "Closest vessel:",
            data["closest_vessel_distance_km"],
            "km"
        )

        print(
            "\n----------- VESSELS -----------"
        )

        vessels = data["nearby_vessels"]

        if not vessels:

            print(
                "No AIS vessels received."
            )

        else:

            for vessel in vessels:

                print(
                    "\n--------------------------------"
                )

                print(
                    "Name:",
                    vessel.get(
                        "name",
                        "Unknown Vessel"
                    )
                )

                print(
                    "MMSI:",
                    vessel.get("mmsi")
                )

                print(
                    "Latitude:",
                    vessel.get("latitude")
                )

                print(
                    "Longitude:",
                    vessel.get("longitude")
                )

                print(
                    "Distance:",
                    vessel.get("distance_km"),
                    "km"
                )

                print(
                    "Speed:",
                    vessel.get("speed_knots"),
                    "knots"
                )

                print(
                    "Course:",
                    vessel.get("course")
                )

                print(
                    "Heading:",
                    vessel.get("heading")
                )

                print(
                    "Navigation Status:",
                    vessel.get(
                        "navigation_status"
                    )
                )

        print(
            "\n======================================"
        )

    else:

        print(
            "\nVessel Agent Error:"
        )

        print(
            result.get(
                "error",
                "Unknown error"
            )
        )