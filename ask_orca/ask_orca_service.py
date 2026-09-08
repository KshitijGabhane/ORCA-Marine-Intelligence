"""
ask_orca_service.py

"Ask ORCA" - an LLM-driven Q&A layer over ORCA's external marine data sources
(weather, vessel/AIS traffic, PFZ fishing zones).

How it works
------------
1. The user asks a natural-language question, optionally with their current
   GPS coordinates (lat/lon).
2. We send the question to an LLM (Anthropic Claude) along with a set of
   "tools" -- one per external data source ORCA already integrates with.
3. Claude decides which tool(s) it needs, we run them for real, feed the
   results back, and Claude writes a final natural-language answer.
4. If Claude asks for a tool we don't recognize, or a tool call fails, we
   surface that gracefully instead of guessing.

Wire-up required from you
--------------------------
The three functions below (`fetch_weather`, `fetch_vessels`, `fetch_pfz`)
are stubs. Replace the body of each with your actual API calls (same ones
your dashboard.js / weather agent / vessel agent / PFZ agent already use).
Everything else (tool schema, orchestration loop, Flask route) works as-is
once those are filled in.

Environment variables expected
-------------------------------
ANTHROPIC_API_KEY   - your Anthropic API key
WEATHER_API_KEY     - OpenWeatherMap API key (https://openweathermap.org/api)
VESSEL_API_KEY      - AISstream.io API key (https://aisstream.io)
PFZ_API_URL         - base URL for your INCOIS/PFZ data source (not yet
                      wired up -- see README, no public PFZ API is known)

Set these in your shell or a local .env file -- never hardcode real key
values into this file or commit them to version control.
"""

import os
import json
import logging
from typing import Any

import requests
from anthropic import Anthropic

logger = logging.getLogger("ask_orca")

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are ORCA, a marine intelligence assistant for fishermen.
You answer questions about weather, ocean conditions, nearby vessels, and
INCOIS Potential Fishing Zones (PFZ) using the live tools available to you.

Rules:
- Always call a tool to get live data before answering questions about
  current conditions, vessels, or fishing zones. Never guess numbers.
- If the question doesn't need live data (e.g. "what does PFZ mean?"),
  answer directly without calling a tool.
- Keep answers short, plain-language, and actionable for someone at sea.
  Lead with the safety-relevant fact first if there is one.
- If a tool fails or returns no data, say so plainly rather than making
  something up.
- If the user hasn't shared their location and the question needs it,
  ask for it instead of assuming a location.
"""

# ---------------------------------------------------------------------------
# 1. Data source functions -- REPLACE THE BODIES with your real API calls.
# ---------------------------------------------------------------------------

def fetch_weather(lat: float, lon: float) -> dict:
    """Fetch current weather + marine wave conditions for a coordinate.

    Combines two calls:
    - OpenWeatherMap: temperature, wind, general conditions (needs WEATHER_API_KEY)
    - Open-Meteo Marine API: wave height/period (free, no key needed) --
      this is what actually matters for "is it safe to go out" questions.
    """
    api_key = os.environ.get("WEATHER_API_KEY")
    result: dict = {}

    if not api_key:
        result["weather_error"] = (
            "WEATHER_API_KEY not set -- get one free at "
            "https://openweathermap.org/api"
        )
    else:
        try:
            resp = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": api_key,
                    "units": "metric",
                },
                timeout=8,
            )
            resp.raise_for_status()
            data = resp.json()
            result.update(
                {
                    "temperature_c": data.get("main", {}).get("temp"),
                    "condition": (data.get("weather") or [{}])[0].get("description"),
                    "wind_speed_ms": data.get("wind", {}).get("speed"),
                    "wind_deg": data.get("wind", {}).get("deg"),
                }
            )
        except requests.RequestException as e:
            logger.exception("OpenWeatherMap fetch failed")
            result["weather_error"] = str(e)

    # Marine/wave data -- free, no key needed.
    try:
        marine_resp = requests.get(
            "https://marine-api.open-meteo.com/v1/marine",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "wave_height,wave_period,wave_direction",
            },
            timeout=8,
        )
        marine_resp.raise_for_status()
        marine_data = marine_resp.json().get("current", {})
        result.update(
            {
                "wave_height_m": marine_data.get("wave_height"),
                "wave_period_s": marine_data.get("wave_period"),
                "wave_direction_deg": marine_data.get("wave_direction"),
            }
        )
    except requests.RequestException as e:
        logger.exception("marine data fetch failed")
        result["marine_error"] = str(e)

    return result


def _km_to_deg_lat(km: float) -> float:
    return km / 111.0


def _km_to_deg_lon(km: float, lat: float) -> float:
    return km / (111.0 * max(0.1, abs(__import__("math").cos(__import__("math").radians(lat)))))


async def _fetch_vessels_async(lat: float, lon: float, radius_km: float) -> dict:
    """Open a short-lived AISstream websocket, collect nearby ship reports
    for a few seconds, and summarize them. AISstream is a live push feed,
    not a request/response API, so we listen briefly rather than "GET"ing.
    """
    import asyncio
    import json as _json
    import websockets

    api_key = os.environ.get("VESSEL_API_KEY")
    if not api_key:
        return {
            "error": "VESSEL_API_KEY not set -- get a free key at "
                     "https://aisstream.io"
        }

    dlat = _km_to_deg_lat(radius_km)
    dlon = _km_to_deg_lon(radius_km, lat)
    bounding_box = [[lat - dlat, lon - dlon], [lat + dlat, lon + dlon]]

    vessels: dict[str, dict] = {}

    try:
        async with websockets.connect(
            "wss://stream.aisstream.io/v0/stream", open_timeout=8
        ) as ws:
            await ws.send(
                _json.dumps(
                    {
                        "APIKey": api_key,
                        "BoundingBoxes": [bounding_box],
                        "FilterMessageTypes": ["PositionReport"],
                    }
                )
            )

            # Listen for a short window -- AIS is a live stream, not a
            # single request/response, so we sample a few seconds of traffic.
            try:
                async with asyncio.timeout(6):
                    async for raw in ws:
                        msg = _json.loads(raw)
                        report = msg.get("Message", {}).get("PositionReport")
                        meta = msg.get("MetaData", {})
                        if report:
                            mmsi = str(meta.get("MMSI") or report.get("UserID"))
                            vessels[mmsi] = {
                                "lat": report.get("Latitude"),
                                "lon": report.get("Longitude"),
                                "speed_knots": report.get("Sog"),
                                "name": meta.get("ShipName", "").strip(),
                            }
            except TimeoutError:
                pass
    except Exception as e:
        logger.exception("AISstream fetch failed")
        return {"error": str(e)}

    if not vessels:
        return {"vessel_count": 0, "note": "No AIS reports received in the sample window."}

    def _dist_km(v):
        import math
        dy = (v["lat"] - lat) * 111.0
        dx = (v["lon"] - lon) * 111.0 * math.cos(math.radians(lat))
        return math.hypot(dx, dy)

    closest = min(vessels.values(), key=_dist_km)

    return {
        "vessel_count": len(vessels),
        "radius_km": radius_km,
        "closest_vessel": {
            "name": closest.get("name") or "Unknown",
            "distance_km": round(_dist_km(closest), 1),
            "speed_knots": closest.get("speed_knots"),
        },
    }


def fetch_vessels(lat: float, lon: float, radius_km: float = 20) -> dict:
    """Fetch nearby AIS vessels for a coordinate via AISstream.io.

    AISstream pushes a live websocket feed rather than answering a single
    request, so this opens a short connection, samples traffic for a few
    seconds, and summarizes it.
    """
    import asyncio

    try:
        return asyncio.run(_fetch_vessels_async(lat, lon, radius_km))
    except RuntimeError:
        # Already inside an event loop (e.g. some WSGI/ASGI setups) --
        # fall back to a new loop in a thread.
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(
                lambda: asyncio.run(_fetch_vessels_async(lat, lon, radius_km))
            ).result()


def fetch_pfz(lat: float, lon: float) -> dict:
    """Fetch nearest INCOIS Potential Fishing Zone (PFZ) info for a coordinate.

    TODO: replace with your real PFZ agent's call to INCOIS (or your own
    scraped/cached PFZ dataset) -- whatever populates #selectedPFZ,
    #pfzDistance, #pfzDirection, #pfzDepth in the dashboard.
    """
    pfz_url = os.environ.get("PFZ_API_URL")
    if not pfz_url:
        return {
            "error": "PFZ data source not yet connected. "
                     "Set PFZ_API_URL and wire this up in fetch_pfz()."
        }
    try:
        resp = requests.get(pfz_url, params={"lat": lat, "lon": lon}, timeout=8)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.exception("PFZ fetch failed")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# 2. Tool schema Claude sees. Keep names in sync with DATA_SOURCES below.
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "get_weather",
        "description": (
            "Get current weather and wind conditions at a coordinate. "
            "Use for questions about wind, storms, temperature, rain, or "
            "general weather safety."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"},
            },
            "required": ["lat", "lon"],
        },
    },
    {
        "name": "get_vessels",
        "description": (
            "Get nearby AIS vessel traffic at a coordinate. Use for "
            "questions about other boats, traffic density, or collision risk."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"},
                "radius_km": {
                    "type": "number",
                    "description": "Search radius in km (default 20)",
                },
            },
            "required": ["lat", "lon"],
        },
    },
    {
        "name": "get_pfz",
        "description": (
            "Get the nearest INCOIS Potential Fishing Zone (PFZ) to a "
            "coordinate -- distance, direction, and depth. Use for "
            "questions about where to fish."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"},
            },
            "required": ["lat", "lon"],
        },
    },
]

DATA_SOURCES = {
    "get_weather": lambda i: fetch_weather(i["lat"], i["lon"]),
    "get_vessels": lambda i: fetch_vessels(i["lat"], i["lon"], i.get("radius_km", 20)),
    "get_pfz": lambda i: fetch_pfz(i["lat"], i["lon"]),
}


# ---------------------------------------------------------------------------
# 3. Orchestration loop
# ---------------------------------------------------------------------------

def ask_orca(question: str, lat: float | None = None, lon: float | None = None) -> dict:
    """Answer a natural-language question, calling live data tools as needed.

    Returns {"answer": str, "tool_calls": [...]} so the frontend can show
    what data backed the answer if it wants to.
    """
    location_note = (
        f"The user's current GPS location is lat={lat}, lon={lon}."
        if lat is not None and lon is not None
        else "The user has not shared their GPS location."
    )

    messages: list[dict[str, Any]] = [
        {"role": "user", "content": f"{location_note}\n\nQuestion: {question}"}
    ]

    tool_calls_made = []

    # Cap the loop so a misbehaving tool-call cycle can't run forever.
    for _ in range(4):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            final_text = "".join(
                block.text for block in response.content if block.type == "text"
            )
            return {"answer": final_text, "tool_calls": tool_calls_made}

        # Handle tool use: run every requested tool, then loop back.
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []

        for block in response.content:
            if block.type != "tool_use":
                continue

            tool_name = block.name
            tool_input = block.input
            handler = DATA_SOURCES.get(tool_name)

            if handler is None:
                result: dict = {"error": f"Unknown tool '{tool_name}'"}
            else:
                result = handler(tool_input)

            tool_calls_made.append({"tool": tool_name, "input": tool_input, "result": result})
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                }
            )

        messages.append({"role": "user", "content": tool_results})

    return {
        "answer": "I wasn't able to pull together a confident answer -- please try rephrasing.",
        "tool_calls": tool_calls_made,
    }
