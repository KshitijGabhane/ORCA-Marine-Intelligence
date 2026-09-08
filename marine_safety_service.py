# marine_safety_service.py

import math
import json
import os
import requests
from datetime import datetime, timezone


# ============================================================
# FILE PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

GEOFENCE_DIR = os.path.join(
    BASE_DIR,
    "data",
    "geofences"
)

MARITIME_BOUNDARY_FILE = os.path.join(
    GEOFENCE_DIR,
    "maritime_boundary.geojson"
)

PROTECTED_AREAS_FILE = os.path.join(
    GEOFENCE_DIR,
    "protected_areas.geojson"
)

RESTRICTED_AREAS_FILE = os.path.join(
    GEOFENCE_DIR,
    "restricted_areas.geojson"
)


# ============================================================
# OFFICIAL IMD API
# ============================================================

IMD_BASE_URL = "https://api.imd.gov.in/api/v1"

IMD_CYCLONE_TRACK_URL = (
    f"{IMD_BASE_URL}/cyclone_track"
)

IMD_CYCLONE_WIND_URL = (
    f"{IMD_BASE_URL}/cyclone_wind"
)

IMD_CYCLONE_COI_URL = (
    f"{IMD_BASE_URL}/cyclone_cou"
)


# ============================================================
# BASIC DISTANCE CALCULATION
# ============================================================

def distance_km(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two GPS coordinates.
    """

    R = 6371.0

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

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return round(R * c, 2)


# ============================================================
# LOAD GEOJSON
# ============================================================

def load_geojson(file_path):
    """
    Load a GeoJSON file.

    Returns:
        GeoJSON dictionary if available.
        None if file does not exist or cannot be read.
    """

    if not os.path.exists(file_path):
        print(f"GeoJSON file not found: {file_path}")
        return None

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as e:

        print(
            f"Error loading GeoJSON "
            f"{file_path}: {e}"
        )

        return None


# ============================================================
# GEOJSON GEOMETRY HELPERS
# ============================================================

def point_on_segment(px, py, x1, y1, x2, y2):
    """
    Check whether a point is approximately on a line segment.
    """

    cross = (
        (py - y1) * (x2 - x1)
        - (px - x1) * (y2 - y1)
    )

    if abs(cross) > 1e-9:
        return False

    if (
        min(x1, x2) - 1e-9 <= px <= max(x1, x2) + 1e-9
        and
        min(y1, y2) - 1e-9 <= py <= max(y1, y2) + 1e-9
    ):

        return True

    return False


def point_in_polygon(lat, lon, polygon):
    """
    Point-in-polygon test.

    GeoJSON coordinates are:

        [longitude, latitude]

    The function accepts:

        lat = latitude
        lon = longitude
    """

    if not polygon:
        return False

    inside = False

    for ring in polygon:

        if not ring:
            continue

        j = len(ring) - 1

        for i in range(len(ring)):

            lon_i = ring[i][0]
            lat_i = ring[i][1]

            lon_j = ring[j][0]
            lat_j = ring[j][1]

            # Point exactly on boundary
            if point_on_segment(
                lon,
                lat,
                lon_i,
                lat_i,
                lon_j,
                lat_j
            ):
                return True

            intersects = (
                ((lat_i > lat) != (lat_j > lat))
                and
                (
                    lon
                    <
                    (
                        (lon_j - lon_i)
                        * (lat - lat_i)
                        /
                        (lat_j - lat_i)
                        + lon_i
                    )
                )
            )

            if intersects:
                inside = not inside

            j = i

    return inside


def geometry_contains_point(lat, lon, geometry):
    """
    Check whether a point is inside a GeoJSON geometry.
    """

    if not geometry:
        return False

    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")

    if geometry_type == "Polygon":

        return point_in_polygon(
            lat,
            lon,
            coordinates
        )

    elif geometry_type == "MultiPolygon":

        for polygon in coordinates:

            if point_in_polygon(
                lat,
                lon,
                polygon
            ):
                return True

    return False


# ============================================================
# GEOJSON DISTANCE
# ============================================================

def coordinate_distance_km(
    lat,
    lon,
    coordinate
):
    """
    Distance between GPS point and a GeoJSON coordinate.

    GeoJSON coordinate format:

        [longitude, latitude]
    """

    if not coordinate or len(coordinate) < 2:
        return None

    coordinate_lon = coordinate[0]
    coordinate_lat = coordinate[1]

    return distance_km(
        lat,
        lon,
        coordinate_lat,
        coordinate_lon
    )


def geometry_min_distance(
    lat,
    lon,
    geometry
):
    """
    Approximate minimum distance from a GPS point
    to a GeoJSON geometry.

    For large polygons this checks polygon vertices.
    """

    if not geometry:
        return None

    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")

    distances = []

    def collect_ring(ring):

        if not ring:
            return

        for coordinate in ring:

            d = coordinate_distance_km(
                lat,
                lon,
                coordinate
            )

            if d is not None:
                distances.append(d)

    if geometry_type == "Polygon":

        for ring in coordinates:
            collect_ring(ring)

    elif geometry_type == "MultiPolygon":

        for polygon in coordinates:

            for ring in polygon:
                collect_ring(ring)

    if not distances:
        return None

    return round(
        min(distances),
        2
    )


# ============================================================
# GEOJSON FEATURE CHECK
# ============================================================

def check_geojson_zone(
    lat,
    lon,
    file_path,
    zone_name
):
    """
    Check a location against a GeoJSON zone.

    Returns:
        status
        distance_km
        message
    """

    data = load_geojson(file_path)

    if not data:

        return {
            "status": "UNKNOWN",
            "distance_km": None,
            "message": f"{zone_name} data unavailable"
        }

    features = data.get(
        "features",
        []
    )

    if not features:

        return {
            "status": "UNKNOWN",
            "distance_km": None,
            "message": f"{zone_name} dataset is empty"
        }

    nearest_distance = None
    inside_zone = False

    for feature in features:

        geometry = feature.get(
            "geometry"
        )

        if not geometry:
            continue

        # Check if vessel is inside zone
        if geometry_contains_point(
            lat,
            lon,
            geometry
        ):

            inside_zone = True

        # Calculate approximate distance
        current_distance = geometry_min_distance(
            lat,
            lon,
            geometry
        )

        if current_distance is not None:

            if nearest_distance is None:

                nearest_distance = current_distance

            elif current_distance < nearest_distance:

                nearest_distance = current_distance

    # --------------------------------------------------------
    # INSIDE ZONE
    # --------------------------------------------------------

    if inside_zone:

        return {
            "status": "WARNING",
            "distance_km": 0.0,
            "message": f"Vessel is inside {zone_name}"
        }

    # --------------------------------------------------------
    # DATA AVAILABLE BUT DISTANCE UNKNOWN
    # --------------------------------------------------------

    if nearest_distance is None:

        return {
            "status": "UNKNOWN",
            "distance_km": None,
            "message": f"Unable to calculate distance to {zone_name}"
        }

    # --------------------------------------------------------
    # APPLICATION WARNING THRESHOLD
    #
    # NOTE:
    # This is an ORCA application threshold,
    # NOT an official government safety limit.
    # --------------------------------------------------------

    WARNING_DISTANCE_KM = 5.0

    if nearest_distance <= WARNING_DISTANCE_KM:

        return {
            "status": "WARNING",
            "distance_km": nearest_distance,
            "message": (
                f"Vessel is approaching {zone_name}"
            )
        }

    return {
        "status": "SAFE",
        "distance_km": nearest_distance,
        "message": f"No {zone_name} warning"
    }


# ============================================================
# HTTP HELPER FOR IMD
# ============================================================

def fetch_imd_json(url):
    """
    Fetch JSON from official IMD API.

    This function is only used for the newly added
    official-warning layer.
    """

    try:

        response = requests.get(
            url,
            timeout=8
        )

        response.raise_for_status()

        return response.json()

    except Exception as e:

        print(
            f"IMD API error: {url} -> {e}"
        )

        return None


# ============================================================
# OFFICIAL IMD CYCLONE WARNING
# ============================================================

def get_official_imd_warning(
    lat,
    lon
):
    """
    Check the user's exact GPS location against
    official IMD cyclone warning geometry.

    Existing ORCA outputs are NOT changed.

    This function only adds a new official-warning
    section to the final response.
    """

    official_warnings = []

    # --------------------------------------------------------
    # 1. OFFICIAL IMD CYCLONE WIND WARNING
    # --------------------------------------------------------

    cyclone_wind_data = fetch_imd_json(
        IMD_CYCLONE_WIND_URL
    )

    if cyclone_wind_data:

        wind_data = cyclone_wind_data.get(
            "data",
            {}
        )

        if isinstance(wind_data, dict):

            for wind_level, geometry in wind_data.items():

                if not isinstance(geometry, dict):
                    continue

                if geometry_contains_point(
                    lat,
                    lon,
                    geometry
                ):

                    official_warnings.append({

                        "type":
                            "CYCLONE_WIND_WARNING",

                        "severity":
                            "OFFICIAL",

                        "warning_level":
                            wind_level,

                        "message":
                            (
                                "Your current GPS location "
                                "is inside an official IMD "
                                "cyclone wind warning area."
                            ),

                        "source":
                            "India Meteorological Department",

                        "source_url":
                            IMD_CYCLONE_WIND_URL

                    })

    # --------------------------------------------------------
    # 2. OFFICIAL IMD CYCLONE CONE
    # --------------------------------------------------------

    cyclone_cone_data = fetch_imd_json(
        IMD_CYCLONE_COI_URL
    )

    if cyclone_cone_data:

        cone_geometry = cyclone_cone_data.get(
            "data"
        )

        if isinstance(
            cone_geometry,
            dict
        ):

            if geometry_contains_point(
                lat,
                lon,
                cone_geometry
            ):

                official_warnings.append({

                    "type":
                        "CYCLONE_CONE_OF_UNCERTAINTY",

                    "severity":
                        "OFFICIAL",

                    "message":
                        (
                            "Your current GPS location "
                            "is inside the official IMD "
                            "cyclone cone of uncertainty."
                        ),

                    "source":
                        "India Meteorological Department",

                    "source_url":
                        IMD_CYCLONE_COI_URL

                })

    # --------------------------------------------------------
    # 3. OFFICIAL IMD CYCLONE TRACK
    # --------------------------------------------------------

    cyclone_track_data = fetch_imd_json(
        IMD_CYCLONE_TRACK_URL
    )

    closest_cyclone = None
    closest_distance = None

    if cyclone_track_data:

        track_data = cyclone_track_data.get(
            "data",
            {}
        )

        if isinstance(
            track_data,
            dict
        ):

            all_points = []

            all_points.extend(
                track_data.get(
                    "observed",
                    []
                )
            )

            all_points.extend(
                track_data.get(
                    "forecast",
                    []
                )
            )

            for point in all_points:

                try:

                    cyclone_lat = float(
                        point.get("lat")
                    )

                    cyclone_lon = float(
                        point.get("lon")
                    )

                    current_distance = distance_km(
                        lat,
                        lon,
                        cyclone_lat,
                        cyclone_lon
                    )

                    if (
                        closest_distance is None
                        or
                        current_distance
                        <
                        closest_distance
                    ):

                        closest_distance = (
                            current_distance
                        )

                        closest_cyclone = point

                except (
                    TypeError,
                    ValueError
                ):

                    continue

    # --------------------------------------------------------
    # Add track warning only when reasonably close.
    #
    # This is a location-proximity indication to the
    # official IMD track, NOT an IMD-defined safety radius.
    # --------------------------------------------------------

    if (
        closest_cyclone is not None
        and
        closest_distance is not None
        and
        closest_distance <= 300
    ):

        official_warnings.append({

            "type":
                "CYCLONE_TRACK_PROXIMITY",

            "severity":
                "OFFICIAL_TRACK",

            "distance_km":
                closest_distance,

            "cyclone_name":
                closest_cyclone.get(
                    "CYCLONE_NAME"
                ),

            "category":
                closest_cyclone.get(
                    "Category"
                ),

            "message":
                (
                    "Your current GPS location "
                    "is within 300 km of an official "
                    "IMD cyclone track point."
                ),

            "source":
                "India Meteorological Department",

            "source_url":
                IMD_CYCLONE_TRACK_URL

        })

    # --------------------------------------------------------
    # FINAL OFFICIAL WARNING RESULT
    # --------------------------------------------------------

    if official_warnings:

        return {

            "status":
                "WARNING",

            "source":
                "India Meteorological Department",

            "official":
                True,

            "location": {

                "latitude":
                    lat,

                "longitude":
                    lon

            },

            "warnings":
                official_warnings,

            "checked_at":
                datetime.now(
                    timezone.utc
                ).isoformat()

        }

    return {

        "status":
            "NO_WARNING",

        "source":
            "India Meteorological Department",

        "official":
            True,

        "location": {

            "latitude":
                lat,

            "longitude":
                lon

        },

        "warnings":
            [],

        "message":
            (
                "No official IMD cyclone warning "
                "was detected at the current GPS location."
            ),

        "checked_at":
            datetime.now(
                timezone.utc
            ).isoformat()

    }


# ============================================================
# CYCLONE
# ============================================================

def check_cyclone(lat, lon):

    """
    Existing ORCA cyclone output.

    Kept unchanged.
    """

    return {
        "status": "LOW",
        "severity": "NONE",
        "message": "No cyclone warning available",
        "source": "Marine Safety Engine"
    }


# ============================================================
# LIGHTNING
# ============================================================

def check_lightning(lat, lon):

    """
    Existing ORCA lightning output.

    Kept unchanged.
    """

    return {
        "status": "LOW",
        "severity": "NONE",
        "message": "No lightning warning available",
        "source": "Marine Safety Engine"
    }


# ============================================================
# WAVE
# ============================================================

def check_wave(wave_height=None):

    if wave_height is None:

        return {
            "status": "UNKNOWN",
            "height_m": None,
            "message": "Wave data unavailable"
        }

    try:

        wave_height = float(
            wave_height
        )

    except (TypeError, ValueError):

        return {
            "status": "UNKNOWN",
            "height_m": None,
            "message": "Invalid wave data"
        }

    if wave_height >= 2.5:

        return {
            "status": "HIGH",
            "height_m": wave_height,
            "message": "High wave conditions"
        }

    elif wave_height >= 1.5:

        return {
            "status": "MODERATE",
            "height_m": wave_height,
            "message": "Moderate wave conditions"
        }

    else:

        return {
            "status": "LOW",
            "height_m": wave_height,
            "message": "Wave conditions are relatively low"
        }


# ============================================================
# WIND
# ============================================================

def check_wind(wind_speed=None):

    if wind_speed is None:

        return {
            "status": "UNKNOWN",
            "speed": None,
            "message": "Wind data unavailable"
        }

    try:

        wind_speed = float(
            wind_speed
        )

    except (TypeError, ValueError):

        return {
            "status": "UNKNOWN",
            "speed": None,
            "message": "Invalid wind data"
        }

    if wind_speed >= 40:

        status = "HIGH"

    elif wind_speed >= 25:

        status = "MODERATE"

    else:

        status = "LOW"

    return {
        "status": status,
        "speed": wind_speed,
        "message": (
            f"Wind speed: "
            f"{wind_speed} km/h"
        )
    }


# ============================================================
# GEOFENCE
# ============================================================

def check_geofence(lat, lon):

    """
    Check the vessel location against
    the three GeoJSON datasets.
    """

    # --------------------------------------------------------
    # MARITIME BOUNDARY
    # --------------------------------------------------------

    international_boundary = check_geojson_zone(
        lat,
        lon,
        MARITIME_BOUNDARY_FILE,
        "maritime boundary"
    )

    # --------------------------------------------------------
    # PROTECTED AREA
    # --------------------------------------------------------

    protected_area = check_geojson_zone(
        lat,
        lon,
        PROTECTED_AREAS_FILE,
        "protected area"
    )

    # --------------------------------------------------------
    # RESTRICTED AREA
    # --------------------------------------------------------

    restricted_area = check_geojson_zone(
        lat,
        lon,
        RESTRICTED_AREAS_FILE,
        "restricted area"
    )

    return {
        "international_boundary": international_boundary,
        "protected_area": protected_area,
        "restricted_area": restricted_area
    }


# ============================================================
# RISK CALCULATION
# ============================================================

def calculate_overall_risk(
    cyclone,
    lightning,
    wave,
    wind,
    geofence
):

    statuses = [
        cyclone.get("status"),
        lightning.get("status"),
        wave.get("status"),
        wind.get("status")
    ]

    geofence_statuses = [
        geofence[
            "international_boundary"
        ].get("status"),

        geofence[
            "protected_area"
        ].get("status"),

        geofence[
            "restricted_area"
        ].get("status")
    ]

    all_statuses = (
        statuses
        +
        geofence_statuses
    )

    if "HIGH" in all_statuses:

        return "HIGH"

    if (
        "WARNING" in all_statuses
        or
        "MODERATE" in all_statuses
    ):

        return "MODERATE"

    if "UNKNOWN" in all_statuses:

        return "UNKNOWN"

    return "LOW"


# ============================================================
# RECOMMENDATION
# ============================================================

def generate_recommendation(
    risk,
    cyclone,
    lightning,
    wave,
    wind,
    geofence
):

    reasons = []

    if cyclone.get("status") == "HIGH":

        reasons.append(
            "cyclone risk is high"
        )

    if lightning.get("status") == "HIGH":

        reasons.append(
            "lightning activity is high"
        )

    if lightning.get("status") == "WARNING":

        reasons.append(
            "lightning warning is active"
        )

    if wave.get("status") == "HIGH":

        reasons.append(
            "wave conditions are high"
        )

    if wind.get("status") == "HIGH":

        reasons.append(
            "wind conditions are high"
        )

    if (
        geofence[
            "international_boundary"
        ].get("status")
        == "WARNING"
    ):

        reasons.append(
            "vessel is approaching "
            "the maritime boundary"
        )

    if (
        geofence[
            "protected_area"
        ].get("status")
        == "WARNING"
    ):

        reasons.append(
            "vessel is approaching "
            "a protected area"
        )

    if (
        geofence[
            "restricted_area"
        ].get("status")
        == "WARNING"
    ):

        reasons.append(
            "vessel is approaching "
            "a restricted area"
        )

    if risk == "HIGH":

        if reasons:

            return (
                "🚨 HIGH RISK: "
                "Avoid offshore travel because "
                +
                ", ".join(reasons)
                +
                "."
            )

        return (
            "🚨 HIGH RISK: "
            "Offshore travel is not recommended."
        )

    if risk == "MODERATE":

        if reasons:

            return (
                "⚠️ MODERATE RISK: "
                "Proceed with caution because "
                +
                ", ".join(reasons)
                +
                "."
            )

        return (
            "⚠️ MODERATE RISK: "
            "Monitor marine conditions."
        )

    if risk == "UNKNOWN":

        return (
            "⚠️ Risk cannot be fully determined "
            "because some marine data is unavailable."
        )

    return (
        "🟢 LOW RISK: "
        "No major marine hazard detected."
    )


# ============================================================
# MAIN SAFETY FUNCTION
# ============================================================

def get_marine_safety(
    lat,
    lon,
    wave_height=None,
    wind_speed=None
):

    # ========================================================
    # EXISTING OUTPUTS
    # ========================================================

    cyclone = check_cyclone(
        lat,
        lon
    )

    lightning = check_lightning(
        lat,
        lon
    )

    wave = check_wave(
        wave_height
    )

    wind = check_wind(
        wind_speed
    )

    geofence = check_geofence(
        lat,
        lon
    )

    risk = calculate_overall_risk(
        cyclone,
        lightning,
        wave,
        wind,
        geofence
    )

    recommendation = generate_recommendation(
        risk,
        cyclone,
        lightning,
        wave,
        wind,
        geofence
    )

    # ========================================================
    # NEW:
    # OFFICIAL IMD WARNING BASED ON USER GPS LOCATION
    # ========================================================

    official_warning = get_official_imd_warning(
        lat,
        lon
    )

    # ========================================================
    # EXISTING RESPONSE + ONLY ONE NEW FIELD
    # ========================================================

    return {

        "success": True,

        "location": {
            "latitude": lat,
            "longitude": lon
        },

        "risk": risk,

        "hazards": {

            "cyclone": cyclone,

            "lightning": lightning,

            "wave": wave,

            "wind": wind

        },

        "geofence": geofence,

        "recommendation": recommendation,

        # ====================================================
        # NEW OFFICIAL WARNING
        # ====================================================

        "official_warning": official_warning

    }