from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from database import get_db_connection

from routes.ocean_routes import ocean_bp

from sos_service import (
    create_sos,
    update_sos_status,
    get_active_sos,
    get_sos,
    update_sos_location
)

from notification_service import (
    send_emergency_notification
)

from services.weather_service import analyze_weather

from agents.fisheries_agent import fisheries_agent
from agents.gis_agent import gis_agent
from agents.vessel_agent import vessel_agent
from ocean_service import get_ocean_data
from marine_safety_service import get_marine_safety

# Ocean Agent
try:
    from agents.ocean_agent import OceanAgent

    ocean_agent = OceanAgent()

    OCEAN_AGENT_AVAILABLE = True

except Exception as e:

    print(
        "Ocean Agent initialization error:",
        e
    )

    ocean_agent = None

    OCEAN_AGENT_AVAILABLE = False


import os
import json
import math

from datetime import datetime, timezone


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

app.register_blueprint(ocean_bp)


# ============================================================
# SECRET KEY
# ============================================================

app.secret_key = "ORCA_SECRET_KEY_CHANGE_THIS_LATER"


# ============================================================
# HELPER - ROLE CHECK
# ============================================================

def is_logged_in():

    return "user_id" in session


def require_role(role):

    if "user_id" not in session:

        return False

    if session.get("role") != role:

        return False

    return True


# ============================================================
# HELPER - GET COORDINATES
# ============================================================

def get_coordinates():

    latitude = request.args.get(
        "lat",
        type=float
    )

    longitude = request.args.get(
        "lon",
        type=float
    )

    if latitude is None or longitude is None:

        raise ValueError(
            "Latitude and longitude are required."
        )

    if not -90 <= latitude <= 90:

        raise ValueError(
            "Invalid latitude."
        )

    if not -180 <= longitude <= 180:

        raise ValueError(
            "Invalid longitude."
        )

    return latitude, longitude


# ============================================================
# LOGIN PAGE
# ============================================================

@app.route("/")
def login():

    if "user_id" in session:

        role = session.get("role")

        if role == "fisherman":

            return redirect(
                url_for("fisherman_dashboard")
            )

        elif role == "rescue":

            return redirect(
                url_for("rescue_dashboard")
            )

        elif role == "admin":

            return redirect(
                url_for("admin_dashboard")
            )

    return render_template("login.html")


# ============================================================
# REGISTER PAGE
# ============================================================

@app.route("/register")
def register():

    return render_template("register.html")


# ============================================================
# REGISTER API
# ============================================================

@app.route(
    "/api/register",
    methods=["POST"]
)
def register_api():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "message": "No data received"
            }), 400

        name = data.get(
            "name",
            ""
        ).strip()

        email = data.get(
            "email",
            ""
        ).strip().lower()

        password = data.get(
            "password",
            ""
        ).strip()

        role = data.get(
            "role",
            ""
        ).strip().lower()


        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not name:

            return jsonify({
                "success": False,
                "message": "Name is required"
            }), 400


        if not email:

            return jsonify({
                "success": False,
                "message": "Email is required"
            }), 400


        if not password:

            return jsonify({
                "success": False,
                "message": "Password is required"
            }), 400


        if len(password) < 6:

            return jsonify({
                "success": False,
                "message":
                    "Password must contain at least 6 characters"
            }), 400


        # ----------------------------------------------------
        # ADMIN CANNOT BE CREATED FROM PUBLIC REGISTRATION
        # ----------------------------------------------------

        if role not in [
            "fisherman",
            "rescue"
        ]:

            return jsonify({
                "success": False,
                "message": "Invalid user role"
            }), 400


        # ----------------------------------------------------
        # DATABASE
        # ----------------------------------------------------

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        # Check existing email

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email = %s
            """,
            (email,)
        )


        existing_user = cursor.fetchone()


        if existing_user:

            cursor.close()
            connection.close()

            return jsonify({
                "success": False,
                "message":
                    "An account with this email already exists"
            }), 409


        # ----------------------------------------------------
        # HASH PASSWORD
        # ----------------------------------------------------

        password_hash = generate_password_hash(
            password
        )


        # ----------------------------------------------------
        # INSERT USER
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO users
            (
                name,
                email,
                password_hash,
                role
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                name,
                email,
                password_hash,
                role
            )
        )


        connection.commit()


        cursor.close()
        connection.close()


        return jsonify({

            "success": True,

            "message":
                "Registration successful"

        }), 201


    except Exception as e:

        print(
            "REGISTRATION ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                "Registration failed"

        }), 500


# ============================================================
# LOGIN API
# ============================================================

@app.route(
    "/api/login",
    methods=["POST"]
)
def login_api():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "message": "No data received"
            }), 400


        email = data.get(
            "email",
            ""
        ).strip().lower()


        password = data.get(
            "password",
            ""
        )


        if not email or not password:

            return jsonify({

                "success": False,

                "message":
                    "Email and password are required"

            }), 400


        # ----------------------------------------------------
        # DATABASE
        # ----------------------------------------------------

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        cursor.execute(
            """
            SELECT
                id,
                name,
                email,
                password_hash,
                role
            FROM users
            WHERE email = %s
            """,
            (email,)
        )


        user = cursor.fetchone()


        cursor.close()
        connection.close()


        # ----------------------------------------------------
        # USER NOT FOUND
        # ----------------------------------------------------

        if not user:

            return jsonify({

                "success": False,

                "message":
                    "Invalid email or password"

            }), 401


        # ----------------------------------------------------
        # PASSWORD CHECK
        # ----------------------------------------------------

        if not check_password_hash(
            user["password_hash"],
            password
        ):

            return jsonify({

                "success": False,

                "message":
                    "Invalid email or password"

            }), 401


        # ----------------------------------------------------
        # CREATE SESSION
        # ----------------------------------------------------

        session.clear()


        session["user_id"] = user["id"]

        session["name"] = user["name"]

        session["email"] = user["email"]

        session["role"] = user["role"]


        # ----------------------------------------------------
        # DASHBOARD URL
        # ----------------------------------------------------

        if user["role"] == "fisherman":

            dashboard = "/fisherman-dashboard"


        elif user["role"] == "rescue":

            dashboard = "/rescue-dashboard"


        elif user["role"] == "admin":

            dashboard = "/admin-dashboard"


        else:

            return jsonify({

                "success": False,

                "message":
                    "Invalid account role"

            }), 403


        return jsonify({

            "success": True,

            "message":
                "Login successful",

            "user": {

                "id":
                    user["id"],

                "name":
                    user["name"],

                "email":
                    user["email"],

                "role":
                    user["role"]

            },

            "redirect":
                dashboard

        })


    except Exception as e:

        print(
            "LOGIN ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                "Login failed"

        }), 500


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ============================================================
# CURRENT USER
# ============================================================

@app.route(
    "/api/current-user",
    methods=["GET"]
)
def current_user():

    if "user_id" not in session:

        return jsonify({

            "success": False,

            "message":
                "Not logged in"

        }), 401


    return jsonify({

        "success": True,

        "user": {

            "id":
                session["user_id"],

            "name":
                session["name"],

            "email":
                session["email"],

            "role":
                session["role"]

        }

    })


# ============================================================
# FISHERMAN DASHBOARD
# ============================================================

@app.route("/fisherman-dashboard")
def fisherman_dashboard():

    if not require_role("fisherman"):

        return redirect(
            url_for("login")
        )

    return render_template(
        "fisherman_dashboard.html"
    )


# ============================================================
# RESCUE DASHBOARD
# ============================================================

@app.route("/rescue-dashboard")
def rescue_dashboard():

    if not require_role("rescue"):

        return redirect(
            url_for("login")
        )

    return render_template(
        "rescue_dashboard.html"
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin-dashboard")
def admin_dashboard():

    if not require_role("admin"):

        return redirect(
            url_for("login")
        )

    return render_template(
        "admin_dashboard.html"
    )


# ============================================================
# OLD /dashboard ROUTE
# ============================================================

@app.route("/dashboard")
def old_dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    role = session.get("role")


    if role == "fisherman":

        return redirect(
            url_for("fisherman_dashboard")
        )


    if role == "rescue":

        return redirect(
            url_for("rescue_dashboard")
        )


    if role == "admin":

        return redirect(
            url_for("admin_dashboard")
        )


    return redirect(
        url_for("login")
    )


# ============================================================
# SOS CREATE
# ============================================================

@app.route(
    "/api/sos/create",
    methods=["POST"]
)
def create_sos_api():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "message":
                    "No JSON data received"
            }), 400


        # Use logged-in user

        user_id = session.get(
            "user_id",
            data.get(
                "user_id",
                "USER001"
            )
        )


        latitude = data.get(
            "latitude"
        )

        longitude = data.get(
            "longitude"
        )

        accuracy = data.get(
            "accuracy"
        )

        emergency_type = data.get(
            "emergency_type",
            "Other"
        )


        if latitude is None or longitude is None:

            return jsonify({

                "success": False,

                "message":
                    "GPS location required"

            }), 400


        sos_id = create_sos(

            user_id,
            latitude,
            longitude,
            accuracy,
            emergency_type

        )


        notification_sent = \
            send_emergency_notification(

                sos_id,

                latitude,

                longitude,

                emergency_type

            )


        return jsonify({

            "success": True,

            "sos_id":
                sos_id,

            "status":
                "SOS_ACTIVE",

            "alert_status":
                "SENT"
                if notification_sent
                else
                "FAILED"

        })


    except Exception as e:

        print(
            "SOS ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500


# ============================================================
# ACTIVE SOS
# ============================================================

@app.route(
    "/api/sos/active",
    methods=["GET"]
)
def active_sos():

    try:

        alerts = get_active_sos()

        return jsonify({

            "success": True,

            "alerts": alerts

        })


    except Exception as e:

        print(
            "ACTIVE SOS ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500


# ============================================================
# SINGLE SOS
# ============================================================

@app.route(
    "/api/sos/<sos_id>",
    methods=["GET"]
)
def single_sos(sos_id):

    try:

        sos = get_sos(sos_id)

        if not sos:

            return jsonify({

                "success": False,

                "message":
                    "SOS not found"

            }), 404


        return jsonify({

            "success": True,

            "sos":
                sos

        })


    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500


# ============================================================
# UPDATE SOS STATUS
# ============================================================

@app.route(
    "/api/sos/<sos_id>/status",
    methods=["POST"]
)
def update_status(sos_id):

    try:

        data = request.get_json()

        new_status = data.get(
            "status"
        )


        allowed_statuses = [

            "SOS_ACTIVE",

            "LOCATION_ACQUIRED",

            "ALERT_SENT",

            "ALERT_FAILED",

            "RESCUE_ACKNOWLEDGED",

            "RESCUE_IN_PROGRESS",

            "EMERGENCY_RESOLVED",

            "SOS_CANCELLED"

        ]


        if new_status not in allowed_statuses:

            return jsonify({

                "success": False,

                "message":
                    "Invalid SOS status"

            }), 400


        updated = update_sos_status(

            sos_id,

            new_status

        )


        if not updated:

            return jsonify({

                "success": False,

                "message":
                    "SOS not found"

            }), 404


        return jsonify({

            "success": True,

            "sos_id":
                sos_id,

            "status":
                new_status

        })


    except Exception as e:

        print(
            "STATUS ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500


# ============================================================
# UPDATE SOS LOCATION
# ============================================================

@app.route(
    "/api/sos/<sos_id>/location",
    methods=["POST"]
)
def update_location(sos_id):

    try:

        data = request.get_json()

        latitude = data.get(
            "latitude"
        )

        longitude = data.get(
            "longitude"
        )

        accuracy = data.get(
            "accuracy"
        )


        if latitude is None or longitude is None:

            return jsonify({

                "success": False,

                "message":
                    "Location required"

            }), 400


        updated = update_sos_location(

            sos_id,

            latitude,

            longitude,

            accuracy

        )


        if not updated:

            return jsonify({

                "success": False,

                "message":
                    "SOS not found"

            }), 404


        return jsonify({

            "success": True,

            "message":
                "Location updated"

        })


    except Exception as e:

        print(
            "LOCATION ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500


# ============================================================
# WEATHER API
#
# Dashboard sends:
#
# /api/weather?lat=18.638&lon=72.508
#
# Weather Agent/service handles the actual weather data.
# ============================================================

@app.route(
    "/api/weather",
    methods=["GET"]
)
def weather_api():

    try:

        latitude, longitude = get_coordinates()


        result = analyze_weather(

            latitude,

            longitude

        )


        return jsonify({

            "status": "success",

            "latitude": latitude,

            "longitude": longitude,

            "data": result,

            "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat()

        })


    except ValueError as e:

        return jsonify({

            "status": "error",

            "message":
                str(e)

        }), 400


    except Exception as e:

        print(
            "WEATHER API ERROR:",
            e
        )

        return jsonify({

            "status": "error",

            "message":
                str(e)

        }), 500


# ============================================================
# MARINE SAFETY API
#
# Dashboard sends:
#
# /api/marine-safety?lat=18.52&lon=73.85
#
# Optional:
#
# /api/marine-safety?lat=18.52&lon=73.85
# &wave_height=2.5
# &wind_speed=30
#
# This calls the Marine Safety Service.
# ============================================================

@app.route("/api/marine-safety", methods=["GET"])
def marine_safety():
    try:
        lat = request.args.get("lat", type=float)
        lon = request.args.get("lon", type=float)

        if lat is None or lon is None:
            return jsonify({
                "success": False,
                "message": "Latitude and longitude are required"
            }), 400

        # -----------------------------
        # 1. OCEAN DATA
        # -----------------------------
        ocean_data = get_ocean_data(lat, lon)

        wind_speed_kmh = None

        if ocean_data.get("wind_speed_ms") is not None:
            wind_speed_kmh = ocean_data["wind_speed_ms"] * 3.6

        # -----------------------------
        # 2. WEATHER DATA
        # -----------------------------
        weather_data = analyze_weather(lat, lon)

        # -----------------------------
        # 3. MARINE SAFETY
        # -----------------------------
        result = get_marine_safety(
            lat,
            lon,
            wave_height=ocean_data.get("significant_wave_height"),
            wind_speed=wind_speed_kmh
        )

        # -----------------------------
        # 4. ADD OCEAN + WEATHER
        # -----------------------------
        result["ocean_data"] = ocean_data
        result["weather"] = weather_data

        return jsonify(result)

    except Exception as e:
        print("Marine safety error:", e)

        return jsonify({
            "success": False,
            "message": "Marine safety calculation failed",
            "error": str(e)
        }), 500

        # ----------------------------------------------------
        # WEATHER AGENT
        # ----------------------------------------------------

        weather_result = None

        try:

            weather_observation = {
                "latitude": lat,
                "longitude": lon
            }

            weather_result = analyze_weather(
                lat,
                lon
            )

        except Exception as e:

            print(
                "Weather Agent error:",
                e
            )

        # ----------------------------------------------------
        # EXTRACT WIND
        # ----------------------------------------------------

        wind_speed = None

        if weather_result:

            try:

                wind_speed = (
                    weather_result
                    .get("result", {})
                    .get("wind", {})
                    .get("speed_kmh")
                )

            except Exception:

                wind_speed = None

        # ----------------------------------------------------
        # OCEAN AGENT
        # ----------------------------------------------------

        ocean_result = None

        try:

            if OCEAN_AGENT_AVAILABLE:

                ocean_observation = {
                    "latitude": lat,
                    "longitude": lon
                }

                # Use your existing Ocean Agent
                ocean_result = ocean_agent.analyze(
                    lat,
                    lon,
                    ocean_observation
                )

        except Exception as e:

            print(
                "Ocean Agent error:",
                e
            )

        # ----------------------------------------------------
        # EXTRACT WAVE HEIGHT
        # ----------------------------------------------------

        wave_height = None

        if ocean_result:

            try:

                wave_height = (
                    ocean_result
                    .get("ocean", {})
                    .get("significant_wave_height")
                )

            except Exception:

                wave_height = None

        # ----------------------------------------------------
        # MARINE SAFETY ENGINE
        # ----------------------------------------------------

        result = get_marine_safety(

            lat,
            lon,

            wave_height=wave_height,

            wind_speed=wind_speed
        )

        # ----------------------------------------------------
        # ADD AGENT DATA FOR TRANSPARENCY
        # ----------------------------------------------------

        result["agents"] = {

            "weather": weather_result,

            "ocean": ocean_result

        }

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify(result)

    except Exception as e:

        print(
            "Marine safety error:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                "Marine safety calculation failed",

            "error": str(e)

        }), 500

# ============================================================
# OCEAN API
#
# Dashboard sends:
#
# /api/ocean?lat=18.638&lon=72.508
#
# Ocean Agent receives the selected location.
# ============================================================

@app.route(
    "/api/ocean",
    methods=["GET"]
)
def ocean_api():

    try:

        latitude, longitude = get_coordinates()


        if not OCEAN_AGENT_AVAILABLE:

            return jsonify({

                "status": "error",

                "message":
                    "Ocean Agent is not available."

            }), 503


        observation = {

            "latitude":
                latitude,

            "longitude":
                longitude,

            "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat()

        }


        result = ocean_agent.analyze(

            observation

        )


        return jsonify({

            "status": "success",

            "latitude":
                latitude,

            "longitude":
                longitude,

            "data":
                result,

            "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat()

        })


    except ValueError as e:

        return jsonify({

            "status": "error",

            "message":
                str(e)

        }), 400


    except Exception as e:

        print(
            "OCEAN API ERROR:",
            e
        )

        return jsonify({

            "status": "error",

            "message":
                str(e)

        }), 500


# ============================================================
# VESSEL API
# ============================================================

@app.route(
    "/api/vessel",
    methods=["GET"]
)
def api_vessel():

    try:

        latitude, longitude = get_coordinates()


        result = vessel_agent(

            latitude=latitude,

            longitude=longitude,

            radius_degree=0.5,

            timeout=10

        )


        return jsonify(result)


    except ValueError as e:

        return jsonify({

            "status": "error",

            "message":
                str(e)

        }), 400


    except Exception as e:

        print(
            "VESSEL API ERROR:",
            e
        )

        return jsonify({

            "status": "error",

            "message":
                str(e)

        }), 500


# ============================================================
# GIS API
# ============================================================

@app.route(
    "/api/gis",
    methods=["GET"]
)
def gis_api():

    try:

        latitude, longitude = get_coordinates()


        result = gis_agent(

            latitude,

            longitude

        )


        return jsonify(result)


    except ValueError as e:

        return jsonify({

            "status": "error",

            "message":
                str(e)

        }), 400


    except Exception as e:

        print(
            "GIS API ERROR:",
            e
        )

        return jsonify({

            "status": "error",

            "message":
                str(e)

        }), 500


# ============================================================
# FISHERIES PAGE
# ============================================================

@app.route("/fisheries")
def fisheries():

    return render_template(
        "fisheries.html"
    )


# ============================================================
# FISHERIES API
#
# Finds the nearest PFZ to the current fisherman location.
# ============================================================

@app.route(
    "/api/fisheries",
    methods=["GET"]
)
def fisheries_api():

    try:

        latitude, longitude = get_coordinates()


        result = fisheries_agent(

            latitude,

            longitude

        )


        return jsonify(result)


    except ValueError as e:

        return jsonify({

            "status": "error",

            "message":
                str(e)

        }), 400


    except Exception as e:

        print(
            "FISHERIES API ERROR:",
            e
        )

        return jsonify({

            "status": "error",

            "message":
                str(e)

        }), 500


# ============================================================
# ALL PFZ / FISHING REGIONS
#
# This API loads your complete PFZ dataset.
#
# File:
#
# data/raw/fisheries/pfz_data.json
#
# The dashboard can use this to permanently display
# all available fishing regions on the map.
# ============================================================

PFZ_FILE = os.path.join(

    os.path.dirname(__file__),

    "data",

    "raw",

    "fisheries",

    "pfz_data.json"

)


def load_all_pfz():

    if not os.path.exists(PFZ_FILE):

        raise FileNotFoundError(

            "PFZ data file not found: "
            + PFZ_FILE

        )


    with open(

        PFZ_FILE,

        "r",

        encoding="utf-8"

    ) as file:

        return json.load(file)


@app.route(
    "/api/fisheries/regions",
    methods=["GET"]
)
def fisheries_regions_api():

    try:

        regions = load_all_pfz()


        return jsonify({

            "status":
                "success",

            "count":
                len(regions),

            "regions":
                regions,

            "source":
                "INCOIS PFZ Advisory"

        })


    except Exception as e:

        print(
            "PFZ REGIONS API ERROR:",
            e
        )

        return jsonify({

            "status":
                "error",

            "message":
                str(e)

        }), 500


# ============================================================
# HAVERSINE DISTANCE
#
# Calculates distance between fisherman and PFZ.
# ============================================================

def haversine_distance(

    lat1,
    lon1,
    lat2,
    lon2

):

    earth_radius_km = 6371.0


    lat1_rad = math.radians(
        lat1
    )


    lat2_rad = math.radians(
        lat2
    )


    delta_lat = math.radians(
        lat2 - lat1
    )


    delta_lon = math.radians(
        lon2 - lon1
    )


    a = (

        math.sin(
            delta_lat / 2
        ) ** 2

        +

        math.cos(
            lat1_rad
        )

        *

        math.cos(
            lat2_rad
        )

        *

        math.sin(
            delta_lon / 2
        ) ** 2

    )


    c = 2 * math.atan2(

        math.sqrt(a),

        math.sqrt(
            1 - a
        )

    )


    return earth_radius_km * c


# ============================================================
# BEARING CALCULATION
# ============================================================

def calculate_bearing(

    lat1,
    lon1,
    lat2,
    lon2

):

    lat1_rad = math.radians(
        lat1
    )


    lat2_rad = math.radians(
        lat2
    )


    delta_lon = math.radians(
        lon2 - lon1
    )


    x = (

        math.sin(
            delta_lon
        )

        *

        math.cos(
            lat2_rad
        )

    )


    y = (

        math.cos(
            lat1_rad
        )

        *

        math.sin(
            lat2_rad
        )

        -

        math.sin(
            lat1_rad
        )

        *

        math.cos(
            lat2_rad
        )

        *

        math.cos(
            delta_lon
        )

    )


    bearing = math.degrees(

        math.atan2(
            x,
            y
        )

    )


    return (
        bearing + 360
    ) % 360


# ============================================================
# BEARING → DIRECTION
# ============================================================

def bearing_direction(
    bearing
):

    directions = [

        "N",
        "NE",
        "E",
        "SE",
        "S",
        "SW",
        "W",
        "NW"

    ]


    index = round(
        bearing / 45
    ) % 8


    return directions[index]


# ============================================================
# FISHING REGION ROUTE API
#
# Example:
#
# /api/fisheries/route
# ?current_lat=18.638
# &current_lon=72.508
# &target_lat=19.011
# &target_lon=72.258
#
# Returns:
# distance
# bearing
# direction
# start
# destination
# ============================================================

@app.route(
    "/api/fisheries/route",
    methods=["GET"]
)
def fisheries_route_api():

    try:

        current_lat = request.args.get(
            "current_lat",
            type=float
        )


        current_lon = request.args.get(
            "current_lon",
            type=float
        )


        target_lat = request.args.get(
            "target_lat",
            type=float
        )


        target_lon = request.args.get(
            "target_lon",
            type=float
        )


        if None in [

            current_lat,
            current_lon,
            target_lat,
            target_lon

        ]:

            return jsonify({

                "status":
                    "error",

                "message":
                    "Current and target coordinates are required."

            }), 400


        # ----------------------------------------------------
        # VALIDATE COORDINATES
        # ----------------------------------------------------

        if not -90 <= current_lat <= 90:

            return jsonify({

                "status":
                    "error",

                "message":
                    "Invalid current latitude."

            }), 400


        if not -180 <= current_lon <= 180:

            return jsonify({

                "status":
                    "error",

                "message":
                    "Invalid current longitude."

            }), 400


        if not -90 <= target_lat <= 90:

            return jsonify({

                "status":
                    "error",

                "message":
                    "Invalid target latitude."

            }), 400


        if not -180 <= target_lon <= 180:

            return jsonify({

                "status":
                    "error",

                "message":
                    "Invalid target longitude."

            }), 400


        # ----------------------------------------------------
        # DISTANCE
        # ----------------------------------------------------

        distance = haversine_distance(

            current_lat,

            current_lon,

            target_lat,

            target_lon

        )


        # ----------------------------------------------------
        # BEARING
        # ----------------------------------------------------

        bearing = calculate_bearing(

            current_lat,

            current_lon,

            target_lat,

            target_lon

        )


        # ----------------------------------------------------
        # DIRECTION
        # ----------------------------------------------------

        direction = bearing_direction(
            bearing
        )


        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "status":
                "success",

            "distance_km":
                round(
                    distance,
                    2
                ),

            "bearing_deg":
                round(
                    bearing,
                    1
                ),

            "direction":
                direction,

            "route": {

                "start": {

                    "latitude":
                        current_lat,

                    "longitude":
                        current_lon

                },

                "destination": {

                    "latitude":
                        target_lat,

                    "longitude":
                        target_lon

                }

            },

            "message":
                "Direct marine route calculated."

        })


    except Exception as e:

        print(
            "FISHERIES ROUTE ERROR:",
            e
        )

        return jsonify({

            "status":
                "error",

            "message":
                str(e)

        }), 500


# ============================================================
# HEALTH CHECK
#
# Useful for checking whether Flask is running.
# ============================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health_check():

    return jsonify({

        "status":
            "success",

        "message":
            "ORCA backend is running",

        "agents": {

            "weather":
                True,

            "ocean":
                OCEAN_AGENT_AVAILABLE,

            "fisheries":
                True,

            "gis":
                True,

            "vessel":
                True,

            "biodiversity":
                False

        },

        "timestamp":
            datetime.now(
                timezone.utc
            ).isoformat()

    })

@app.route("/api/offline-safety", methods=["GET"])
def offline_safety():
    try:
        lat = request.args.get("lat", type=float)
        lon = request.args.get("lon", type=float)

        if lat is None or lon is None:
            return jsonify({
                "success": False,
                "message": "Latitude and longitude are required"
            }), 400

        # Get current marine safety information
        safety = get_marine_safety(
            lat,
            lon
        )

        # Get ocean data
        ocean_data = get_ocean_data(lat, lon)

        # Get weather data
        weather_data = analyze_weather(lat, lon)

        return jsonify({
            "success": True,
            "cached_at": datetime.now(timezone.utc).isoformat(),

            "location": {
                "latitude": lat,
                "longitude": lon
            },

            "weather": weather_data,

            "ocean": ocean_data,

            "marine_safety": safety
        })

    except Exception as e:
        print("Offline safety error:", e)

        return jsonify({
            "success": False,
            "message": "Unable to prepare offline safety data",
            "error": str(e)
        }), 500

# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(

        debug=True,

        host="127.0.0.1",

        port=5000

    )