# ============================================================
# ASK ORCA - MULTILINGUAL MARINE INTELLIGENCE ASSISTANT
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional

# ============================================================
# TRANSLATION
# ============================================================

from ask_orca.translator import (
    translate_to_english,
    translate_from_english
)


# ============================================================
# ORCA AGENTS
# ============================================================

try:
    from agents.weather_agent import WeatherAgent
except Exception as e:
    WeatherAgent = None
    print("Weather Agent import error:", e)


try:
    from agents.fisheries_agent import fisheries_agent
except Exception as e:
    fisheries_agent = None
    print("Fisheries Agent import error:", e)


try:
    from agents.gis_agent import gis_agent
except Exception as e:
    gis_agent = None
    print("GIS Agent import error:", e)


try:
    from agents.vessel_agent import vessel_agent
except Exception as e:
    vessel_agent = None
    print("Vessel Agent import error:", e)


try:
    from sos_service import get_active_sos
except Exception as e:
    get_active_sos = None
    print("SOS import error:", e)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Ask ORCA",
    description="Multilingual Marine Intelligence Assistant",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SUPPORTED LANGUAGES
# ============================================================

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "gu": "Gujarati",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "or": "Odia",
    "pa": "Punjabi"
}


# ============================================================
# REQUEST MODEL
# ============================================================

class AskOrcaRequest(BaseModel):

    question: str

    language: str = "en"

    latitude: float = 18.52

    longitude: float = 73.85

    user_id: Optional[int] = None


# ============================================================
# RESPONSE MODEL
# ============================================================

class AskOrcaResponse(BaseModel):

    answer: str

    language: str

    agent: str

    risk: Optional[str] = None

    reason: Optional[str] = None

    precautions: list[str] = []

    sources: list[str] = []

    confidence: Optional[float] = None

    timestamp: str


# ============================================================
# WEATHER AGENT INITIALIZATION
# ============================================================

weather_agent = None

if WeatherAgent is not None:

    try:

        weather_agent = WeatherAgent()

        print("Weather Agent: READY")

    except Exception as e:

        print("Weather Agent initialization failed:", e)


# ============================================================
# INTENT DETECTION
# ============================================================

def detect_intent(question: str):

    q = question.lower().strip()

    # --------------------------------------------------------
    # SOS / EMERGENCY
    # --------------------------------------------------------

    emergency_words = [

        "sos",
        "emergency",
        "help",
        "danger",
        "dangerous",
        "sinking",
        "sink",
        "drowning",
        "man overboard",
        "person overboard",
        "engine failure",
        "engine failed",
        "engine stopped",
        "boat damaged",
        "boat damage",
        "fire",
        "collision",
        "accident",
        "medical emergency",
        "medical problem",
        "injured",
        "injury",
        "unconscious",
        "lost at sea",
        "stranded",
        "stuck at sea",
        "need rescue",
        "rescue me",
        "save me"
    ]

    if any(word in q for word in emergency_words):

        return "sos"


    # --------------------------------------------------------
    # WEATHER
    # --------------------------------------------------------

    weather_words = [

        "weather",
        "rain",
        "raining",
        "temperature",
        "wind",
        "wind speed",
        "wind direction",
        "humidity",
        "pressure",
        "cloud",
        "cloudy",
        "forecast",
        "storm",
        "thunder",
        "lightning",
        "cyclone",
        "heat",
        "hot",
        "cold",
        "visibility",
        "fog",
        "weather condition",
        "weather risk",
        "weather safe",
        "weather today",
        "weather tomorrow"
    ]

    if any(word in q for word in weather_words):

        return "weather"


    # --------------------------------------------------------
    # OCEAN / SEA
    # --------------------------------------------------------

    ocean_words = [

        "ocean",
        "sea",
        "sea condition",
        "sea state",
        "wave",
        "waves",
        "wave height",
        "swell",
        "swell height",
        "tide",
        "tidal",
        "current",
        "ocean current",
        "water",
        "water temperature",
        "sea temperature",
        "sst",
        "salinity",
        "sea level",
        "storm surge",
        "high wave",
        "rough sea",
        "rough water",
        "calm sea"
    ]

    if any(word in q for word in ocean_words):

        return "ocean"


    # --------------------------------------------------------
    # FISHERIES
    # --------------------------------------------------------

    fisheries_words = [

        "fish",
        "fishing",
        "fisheries",
        "pfz",
        "potential fishing zone",
        "fishing zone",
        "fish zone",
        "fishing area",
        "fish location",
        "where to fish",
        "best place to fish",
        "fish productivity",
        "fish availability",
        "fishing advisory",
        "fishing advice",
        "fishing depth",
        "depth for fishing",
        "fish forecast",
        "incois pfz"
    ]

    if any(word in q for word in fisheries_words):

        return "fisheries"


    # --------------------------------------------------------
    # VESSEL / AIS
    # --------------------------------------------------------

    vessel_words = [

        "vessel",
        "vessels",
        "boat",
        "boats",
        "ship",
        "ships",
        "ais",
        "nearby vessel",
        "nearby vessels",
        "nearby boat",
        "nearby boats",
        "marine traffic",
        "ship traffic",
        "boat traffic",
        "closest vessel",
        "nearest vessel",
        "other boat",
        "other vessels",
        "vessel distance",
        "boat distance"
    ]

    if any(word in q for word in vessel_words):

        return "vessel"


    # --------------------------------------------------------
    # GIS / LOCATION / BOUNDARIES
    # --------------------------------------------------------

    gis_words = [

        "gps",
        "coordinate",
        "coordinates",
        "latitude",
        "longitude",
        "where am i",
        "my location",
        "current location",
        "marine area",
        "eez",
        "exclusive economic zone",
        "boundary",
        "maritime boundary",
        "international boundary",
        "protected area",
        "marine protected area",
        "mpa",
        "restricted area",
        "restricted zone",
        "no fishing zone",
        "geofence",
        "geofencing",
        "fishing allowed",
        "fishing not allowed"
    ]

    if any(word in q for word in gis_words):

        return "gis"


    # --------------------------------------------------------
    # SAFETY
    # --------------------------------------------------------

    safety_words = [

        "safe",
        "safety",
        "marine risk",
        "fishing safe",
        "go fishing",
        "should i go",
        "can i go",
        "should we go",
        "return to shore",
        "return shore",
        "life jacket",
        "lifejacket",
        "safety equipment",
        "precaution",
        "precautions"
    ]

    if any(word in q for word in safety_words):

        return "safety"


    # --------------------------------------------------------
    # NAVIGATION
    # --------------------------------------------------------

    navigation_words = [

        "route",
        "routing",
        "navigation",
        "navigate",
        "safe route",
        "best route",
        "shortest route",
        "destination",
        "bearing",
        "route safety",
        "route risk"
    ]

    if any(word in q for word in navigation_words):

        return "navigation"


    # --------------------------------------------------------
    # GENERAL ORCA
    # --------------------------------------------------------

    general_words = [

        "what is orca",
        "about orca",
        "orca",
        "how does orca work",
        "how to use orca",
        "dashboard",
        "agent",
        "agents",
        "language",
        "data source",
        "data sources"
    ]

    if any(word in q for word in general_words):

        return "general"


    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    return "unknown"


# ============================================================
# WEATHER PROCESSING
# ============================================================

def process_weather(latitude, longitude):

    if weather_agent is None:

        return {

            "answer":
                "The Weather Agent is currently unavailable. "
                "Live weather data cannot be confirmed.",

            "risk": None,

            "confidence": 0,

            "sources": []

        }


    # ========================================================
    # IMPORTANT
    #
    # Your WeatherAgent does NOT fetch live weather itself.
    #
    # This observation MUST eventually come from your
    # real weather API/fetcher.
    #
    # These are only safe fallback values for testing.
    # They must NOT be presented as live weather.
    # ========================================================

    observation = {

        "latitude": latitude,

        "longitude": longitude,

        "air_temperature": 28,

        "wind_speed_knots": 0,

        "wind_gust_knots": 0,

        "wind_direction_deg": 0,

        "precipitation_rate_mmh": 0,

        "relative_humidity_pct": 75,

        "surface_pressure_hpa": 1010,

        "cloud_cover_pct": 0
    }


    try:

        result = weather_agent.analyze(

            observation,

            forecast_24_hours=[]

        )

        data = result.get(
            "result",
            {}
        )


        answer = (

            f"Weather information for "
            f"latitude {latitude:.4f}, "
            f"longitude {longitude:.4f}: "

            f"{data.get('condition', 'Unknown condition')}. "

            f"Temperature: "
            f"{data.get('temperature_c', 'N/A')}°C. "

            f"Wind: "
            f"{data.get('wind', {}).get('speed_knots', 'N/A')} knots. "

            f"Rain: "
            f"{data.get('rain', {}).get('condition', 'N/A')}. "

            f"Humidity: "
            f"{data.get('humidity_pct', 'N/A')}%."

        )


        warnings = data.get(
            "warnings",
            []
        )


        if warnings:

            answer += (

                " Warnings: "
                + ", ".join(warnings)
                + "."

            )


        return {

            "answer": answer,

            "risk": result.get("risk"),

            "confidence": result.get(
                "confidence"
            ),

            "sources": [

                result.get(
                    "source",
                    "Weather Agent"
                )

            ]

        }


    except Exception as e:

        print(
            "Weather processing error:",
            e
        )

        return {

            "answer":
                "Weather data could not be processed.",

            "risk": None,

            "confidence": 0,

            "sources": []

        }


# ============================================================
# FISHERIES PROCESSING
# ============================================================

def process_fisheries(latitude, longitude):

    if fisheries_agent is None:

        return {

            "answer":
                "Fisheries Agent is currently unavailable.",

            "risk": None,

            "confidence": 0,

            "sources": []

        }


    try:

        result = fisheries_agent(
            latitude,
            longitude
        )


        if result.get("status") == "error":

            return {

                "answer":
                    "Fisheries data is currently unavailable.",

                "risk": None,

                "confidence": 0,

                "sources": []

            }


        data = result.get(
            "result",
            result
        )


        if data.get("pfz_found"):

            answer = (

                "A Potential Fishing Zone "
                "(PFZ) was found near your location. "

                f"Distance: "
                f"{data.get('distance_km', 'N/A')} km. "

                f"Direction: "
                f"{data.get('direction', 'N/A')}. "

                f"Bearing: "
                f"{data.get('bearing_deg', 'N/A')}°. "

                f"Depth: "
                f"{data.get('depth_m', 'N/A')} m."

            )

        else:

            answer = (

                "No Potential Fishing Zone was found "
                "within the available PFZ search range "
                "near your location."

            )


        return {

            "answer": answer,

            "risk": result.get("risk"),

            "confidence": result.get(
                "confidence"
            ),

            "sources": [

                result.get(
                    "source",
                    "INCOIS PFZ Advisory"
                )

            ]

        }


    except Exception as e:

        print(
            "Fisheries processing error:",
            e
        )

        return {

            "answer":
                "Fisheries data could not be processed.",

            "risk": None,

            "confidence": 0,

            "sources": []

        }


# ============================================================
# GIS PROCESSING
# ============================================================

def process_gis(latitude, longitude):

    if gis_agent is None:

        return {

            "answer":
                "GIS Agent is currently unavailable.",

            "risk": None,

            "confidence": 0,

            "sources": []

        }


    try:

        result = gis_agent(
            latitude,
            longitude
        )


        if result.get("status") == "error":

            return {

                "answer":
                    "GIS information is currently unavailable.",

                "risk": None,

                "confidence": 0,

                "sources": []

            }


        location_type = result.get(
            "location_type",
            "Unknown"
        )


        area_found = result.get(
            "marine_area_found",
            False
        )


        if area_found:

            answer = (

                f"Your current coordinates are "
                f"{latitude:.5f}, "
                f"{longitude:.5f}. "

                f"The GIS system identifies this "
                f"location as {location_type}."

            )

        else:

            answer = (

                f"Your current coordinates are "
                f"{latitude:.5f}, "
                f"{longitude:.5f}. "

                "No marine area was identified "
                "in the current GIS dataset."

            )


        return {

            "answer": answer,

            "risk": None,

            "confidence": 0.90,

            "sources": [
                "ORCA GIS Dataset"
            ]

        }


    except Exception as e:

        print(
            "GIS processing error:",
            e
        )

        return {

            "answer":
                "GIS information could not be processed.",

            "risk": None,

            "confidence": 0,

            "sources": []

        }


# ============================================================
# VESSEL PROCESSING
# ============================================================

def process_vessel(latitude, longitude):

    if vessel_agent is None:

        return {

            "answer":
                "Vessel Agent is currently unavailable.",

            "risk": None,

            "confidence": 0,

            "sources": []

        }


    try:

        result = vessel_agent(
            latitude,
            longitude
        )


        if result.get("status") == "error":

            return {

                "answer":
                    "Live AIS vessel data is currently unavailable.",

                "risk": None,

                "confidence": 0,

                "sources": []

            }


        data = result.get(
            "result",
            {}
        )


        count = data.get(
            "count",
            data.get(
                "vessel_count",
                0
            )
        )


        density = data.get(
            "traffic_density",
            "Unknown"
        )


        closest = data.get(
            "closest_vessel"
        )


        answer = (

            f"There are {count} nearby AIS vessels. "

            f"Traffic density is {density}."

        )


        if closest:

            distance = closest.get(
                "distance_km",
                "N/A"
            )

            answer += (

                f" The closest detected vessel "
                f"is {distance} km away."

            )


        return {

            "answer": answer,

            "risk": result.get("risk"),

            "confidence": result.get(
                "confidence"
            ),

            "sources": [

                result.get(
                    "source",
                    "AISStream Real-Time AIS"
                )

            ]

        }


    except Exception as e:

        print(
            "Vessel processing error:",
            e
        )

        return {

            "answer":
                "Live vessel data could not be processed.",

            "risk": None,

            "confidence": 0,

            "sources": []

        }


# ============================================================
# SOS PROCESSING
# ============================================================

def process_sos(user_id):

    answer = (

        "This appears to be an emergency. "

        "If you are in immediate danger, "
        "activate the ORCA SOS button on the "
        "fisherman dashboard and share your GPS "
        "location. "

        "Do not wait for normal marine analysis."

    )


    # --------------------------------------------------------
    # NEVER CLAIM THAT SOS WAS ACTIVATED AUTOMATICALLY
    # --------------------------------------------------------

    if (
        get_active_sos is not None
        and user_id is not None
    ):

        try:

            active = get_active_sos(
                user_id
            )


            if active:

                answer = (

                    "An active SOS record was found "
                    "for your account. "

                    "Please remain in a safe position, "
                    "keep GPS enabled and follow the "
                    "emergency instructions on the "
                    "ORCA dashboard."

                )


        except Exception as e:

            print(
                "SOS status check error:",
                e
            )


    return {

        "answer": answer,

        "risk": "CRITICAL",

        "confidence": 0.99,

        "sources": [
            "ORCA SOS System"
        ]

    }


# ============================================================
# OCEAN PROCESSING
# ============================================================

def process_ocean():

    return {

        "answer": (

            "The Ocean Agent is not currently connected "
            "to a live ocean-data service. "

            "I cannot safely provide current wave, "
            "swell, tide, current or sea-state values."

        ),

        "risk": None,

        "confidence": 0,

        "sources": []

    }


# ============================================================
# SAFETY PROCESSING
# ============================================================

def process_safety(latitude, longitude):

    weather = process_weather(
        latitude,
        longitude
    )


    risk = weather.get(
        "risk"
    )


    if risk in [
        "CRITICAL",
        "HIGH"
    ]:

        answer = (

            "Marine conditions may be unsafe. "

            "Check the latest weather, wave and "
            "hazard information before going fishing. "

            "If conditions deteriorate, return to shore "
            "and follow official marine advisories."

        )

    else:

        answer = (

            "Before going to sea, check the latest "
            "weather, wave and hazard information. "

            "Carry required safety equipment and "
            "keep communication and GPS systems available."

        )


    return {

        "answer": answer,

        "risk": risk,

        "confidence": weather.get(
            "confidence"
        ),

        "sources": weather.get(
            "sources",
            []
        )

    }


# ============================================================
# NAVIGATION
# ============================================================

def process_navigation():

    return {

        "answer": (

            "Safe route calculation requires live "
            "vessel position, destination, sea state, "
            "weather hazards and verified marine boundaries. "

            "The complete Safe Route Agent is not currently "
            "connected, so I will not invent a route."

        ),

        "risk": None,

        "confidence": 0,

        "sources": []

    }


# ============================================================
# GENERAL ORCA
# ============================================================

def process_general():

    return {

        "answer": (

            "I am Ask ORCA, the conversational interface "
            "for the ORCA Marine Intelligence and Safety System. "

            "I can help with weather, ocean conditions, "
            "fisheries, vessels, GIS information, "
            "marine safety and SOS."

        ),

        "risk": None,

        "confidence": 0.95,

        "sources": [
            "ORCA"
        ]

    }


# ============================================================
# UNKNOWN QUESTION
# ============================================================

def process_unknown():

    return {

        "answer": (

            "I could not confidently identify the ORCA "
            "service needed for this question. "

            "Please ask about weather, sea or ocean "
            "conditions, fishing or PFZ, vessels or AIS, "
            "GPS or GIS, marine safety, navigation or SOS."

        ),

        "risk": None,

        "confidence": 0,

        "sources": []

    }


# ============================================================
# ASK ORCA API
# ============================================================

@app.post(
    "/api/ask-orca",
    response_model=AskOrcaResponse
)
def ask_orca(
    request: AskOrcaRequest
):

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()


    # --------------------------------------------------------
    # QUESTION VALIDATION
    # --------------------------------------------------------

    original_question = (
        request.question
        .strip()
    )


    if not original_question:

        return AskOrcaResponse(

            answer="Please enter a question.",

            language=request.language,

            agent="general",

            risk=None,

            reason=None,

            precautions=[],

            sources=[],

            confidence=0,

            timestamp=timestamp

        )


    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    language = (
        request.language
        .lower()
        .strip()
    )


    if language not in SUPPORTED_LANGUAGES:

        language = "en"


    # --------------------------------------------------------
    # TRANSLATE USER QUESTION
    # --------------------------------------------------------

    english_question = translate_to_english(

        original_question,

        language

    )


    print("\n" + "=" * 70)

    print(
        "ORIGINAL QUESTION:",
        original_question
    )

    print(
        "LANGUAGE:",
        language
    )

    print(
        "TRANSLATED QUESTION:",
        english_question
    )


    # --------------------------------------------------------
    # DETECT INTENT
    # --------------------------------------------------------

    intent = detect_intent(
        english_question
    )


    print(
        "DETECTED AGENT:",
        intent
    )

    print("=" * 70)


    # --------------------------------------------------------
    # ROUTE TO AGENT
    # --------------------------------------------------------

    if intent == "weather":

        result = process_weather(

            request.latitude,

            request.longitude

        )


    elif intent == "ocean":

        result = process_ocean()


    elif intent == "fisheries":

        result = process_fisheries(

            request.latitude,

            request.longitude

        )


    elif intent == "vessel":

        result = process_vessel(

            request.latitude,

            request.longitude

        )


    elif intent == "gis":

        result = process_gis(

            request.latitude,

            request.longitude

        )


    elif intent == "sos":

        result = process_sos(

            request.user_id

        )


    elif intent == "safety":

        result = process_safety(

            request.latitude,

            request.longitude

        )


    elif intent == "navigation":

        result = process_navigation()


    elif intent == "general":

        result = process_general()


    else:

        result = process_unknown()


    # --------------------------------------------------------
    # ENGLISH ANSWER
    # --------------------------------------------------------

    english_answer = result.get(

        "answer",

        "No answer available."

    )


    # --------------------------------------------------------
    # TRANSLATE ANSWER TO USER LANGUAGE
    # --------------------------------------------------------

    final_answer = translate_from_english(

        english_answer,

        language

    )


    print(
        "FINAL ANSWER:",
        final_answer
    )


    # --------------------------------------------------------
    # RETURN RESPONSE
    # --------------------------------------------------------

    return AskOrcaResponse(

        answer=final_answer,

        language=language,

        agent=intent,

        risk=result.get(
            "risk"
        ),

        reason=english_answer,

        precautions=[],

        sources=result.get(
            "sources",
            []
        ),

        confidence=result.get(
            "confidence"
        ),

        timestamp=timestamp

    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {

        "status": "online",

        "service": "Ask ORCA",

        "multilingual": True,

        "languages": list(
            SUPPORTED_LANGUAGES.keys()
        ),

        "agents": [

            "Weather",
            "Ocean",
            "Fisheries",
            "GIS",
            "Vessel",
            "SOS"

        ],

        "timestamp":
            datetime.now(
                timezone.utc
            ).isoformat()

    }


# ============================================================
# ASK ORCA WEB PAGE
# ============================================================

@app.get("/")
def home():

    return """
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Ask ORCA</title>

<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    font-family:
        Arial,
        sans-serif;

    background:
        linear-gradient(
            135deg,
            #061826,
            #0a3048
        );

    color: white;

    min-height: 100vh;
}

.container {

    max-width: 850px;

    margin:
        50px auto;

    padding:
        30px;
}

.header {

    text-align: center;

    margin-bottom: 35px;
}

.whale {

    font-size: 55px;
}

h1 {

    margin:
        5px 0;

    color:
        #35c5ff;

    font-size:
        38px;
}

.subtitle {

    color:
        #b8c9d6;

    font-size:
        17px;
}

.card {

    background:
        rgba(
            12,
            37,
            53,
            0.95
        );

    padding:
        25px;

    border-radius:
        18px;

    box-shadow:
        0 10px 30px
        rgba(0,0,0,0.3);
}

label {

    display:
        block;

    margin-top:
        15px;

    margin-bottom:
        6px;

    font-weight:
        bold;
}

select,
textarea,
button {

    width:
        100%;

    border:
        none;

    border-radius:
        10px;

    padding:
        14px;

    font-size:
        16px;
}

select,
textarea {

    background:
        #102b3d;

    color:
        white;
}

textarea {

    min-height:
        130px;

    resize:
        vertical;

    outline:
        none;
}

textarea:focus,
select:focus {

    outline:
        2px solid
        #35c5ff;
}

button {

    margin-top:
        18px;

    background:
        #0b8dcc;

    color:
        white;

    font-weight:
        bold;

    cursor:
        pointer;

    transition:
        0.2s;
}

button:hover {

    background:
        #0875a9;

    transform:
        translateY(-1px);
}

button:disabled {

    opacity:
        0.6;

    cursor:
        not-allowed;
}

#result {

    margin-top:
        25px;

    background:
        #081f30;

    border-radius:
        14px;

    padding:
        20px;

    display:
        none;
}

.answer {

    font-size:
        18px;

    line-height:
        1.7;

    margin-bottom:
        20px;
}

.meta {

    color:
        #9fc3d7;

    margin-top:
        8px;

    font-size:
        14px;
}

.meta span {

    color:
        white;

    font-weight:
        bold;
}

.error {

    color:
        #ff8a8a;
}

</style>

</head>

<body>

<div class="container">

<div class="header">

<div class="whale">
🐋
</div>

<h1>ASK ORCA</h1>

<div class="subtitle">

Multilingual Marine Intelligence Assistant

</div>

</div>

<div class="card">

<label>
Language
</label>

<select id="language">

<option value="en">
English
</option>

<option value="hi">
हिन्दी
</option>

<option value="mr">
मराठी
</option>

<option value="gu">
ગુજરાતી
</option>

<option value="bn">
বাংলা
</option>

<option value="ta">
தமிழ்
</option>

<option value="te">
తెలుగు
</option>

<option value="kn">
ಕನ್ನಡ
</option>

<option value="ml">
മലയാളം
</option>

<option value="or">
ଓଡ଼ିଆ
</option>

<option value="pa">
ਪੰਜਾਬੀ
</option>

</select>


<label>
Ask ORCA
</label>

<textarea
id="question"
placeholder="Ask about weather, ocean, fishing, vessels, GIS, safety or SOS..."
></textarea>


<button
id="askButton"
onclick="askOrca()"
>

ASK ORCA

</button>


<div id="result">

<div
class="answer"
id="answer">
</div>


<div class="meta">

Agent:
<span id="agent">
</span>

</div>


<div class="meta">

Risk:
<span id="risk">
</span>

</div>


<div class="meta">

Confidence:
<span id="confidence">
</span>

</div>


<div class="meta">

Sources:
<span id="sources">
</span>

</div>

</div>

</div>

</div>


<script>

async function askOrca() {

    const question =
        document
        .getElementById(
            "question"
        )
        .value
        .trim();


    const language =
        document
        .getElementById(
            "language"
        )
        .value;


    const resultBox =
        document
        .getElementById(
            "result"
        );


    const answer =
        document
        .getElementById(
            "answer"
        );


    const button =
        document
        .getElementById(
            "askButton"
        );


    if (!question) {

        alert(
            "Please enter a question."
        );

        return;
    }


    resultBox.style.display =
        "block";


    answer.innerText =
        "ORCA is thinking...";


    button.disabled =
        true;


    try {

        const response =
            await fetch(
                "/api/ask-orca",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

                            question:
                                question,

                            language:
                                language,

                            latitude:
                                18.52,

                            longitude:
                                73.85

                        })

                }
            );


        if (!response.ok) {

            throw new Error(
                "API request failed"
            );

        }


        const data =
            await response.json();


        answer.innerText =
            data.answer;


        document
        .getElementById(
            "agent"
        )
        .innerText =
            data.agent;


        document
        .getElementById(
            "risk"
        )
        .innerText =
            data.risk ||
            "N/A";


        document
        .getElementById(
            "confidence"
        )
        .innerText =
            data.confidence !== null &&
            data.confidence !== undefined
                ? data.confidence
                : "N/A";


        document
        .getElementById(
            "sources"
        )
        .innerText =
            data.sources &&
            data.sources.length
                ? data.sources.join(", ")
                : "N/A";

    }


    catch (error) {

        console.error(
            error
        );


        answer.innerText =
            "Unable to connect to Ask ORCA.";


        answer.classList.add(
            "error"
        );

    }


    finally {

        button.disabled =
            false;

    }

}

</script>

</body>

</html>
"""


# ============================================================
# START SERVER
# ============================================================

@app.get("/")
def home():

    return """
    
    <!DOCTYPE html>
    
    <html>
       ...
    </html>
    
    """

# OUTSIDE the HTML string
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "ask_orca.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )