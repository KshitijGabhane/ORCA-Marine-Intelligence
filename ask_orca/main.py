from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ask_orca.translator import (
    translate_to_english,
    translate_from_english,
    detect_language
)

from services.weather_service import analyze_weather
from agents.fisheries_agent import fisheries_agent
from agents.vessel_agent import vessel_agent
from agents.gis_agent import gis_agent
from ocean_service import get_ocean_data


app = FastAPI(title="Ask ORCA")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class AskRequest(BaseModel):
    question: str
    language: str = "en"
    latitude: float = 18.52
    longitude: float = 73.85


def detect_intent(question):

    q = question.lower()

    if any(word in q for word in [
        "weather",
        "rain",
        "wind",
        "temperature",
        "storm"
    ]):
        return "weather"

    if any(word in q for word in [
        "fish",
        "fishing",
        "pfz",
        "catch"
    ]):
        return "fisheries"

    if any(word in q for word in [
        "boat",
        "vessel",
        "ship",
        "ais"
    ]):
        return "vessel"

    if any(word in q for word in [
        "location",
        "area",
        "zone",
        "boundary",
        "gis"
    ]):
        return "gis"

    if any(word in q for word in [
        "wave",
        "ocean",
        "sea",
        "swell"
    ]):
        return "ocean"

    if any(word in q for word in [
        "sos",
        "emergency",
        "help",
        "danger"
    ]):
        return "sos"

    return "general"


@app.post("/api/ask-orca")
def ask_orca(request: AskRequest):

    # 1. Work out which language to answer in.
    #    If the caller explicitly picked a non-English language, honor it.
    #    Otherwise (default "en"), auto-detect the language the question
    #    was actually asked in, so users can type in any supported
    #    Indian language and get the answer back in that same language.
    reply_language = request.language

    if not reply_language or reply_language == "en":
        reply_language = detect_language(request.question)

    # 2. Translate user question to English
    english_question = translate_to_english(
        request.question,
        reply_language
    )

    # 3. Detect which agent is needed
    intent = detect_intent(english_question)

    lat = request.latitude
    lon = request.longitude

    # 4. Call correct agent

    if intent == "weather":

        result = analyze_weather(lat, lon)

        answer = (
            f"Weather condition: "
            f"{result.get('condition', 'Unknown')}. "
            f"Temperature: "
            f"{result.get('temperature_c', 'Unknown')}°C."
        )

    elif intent == "fisheries":

        result = fisheries_agent(lat, lon)

        answer = str(result)

    elif intent == "vessel":

        result = vessel_agent(lat, lon)

        answer = str(result)

    elif intent == "gis":

        result = gis_agent(lat, lon)

        answer = str(result)

    elif intent == "ocean":

        result = get_ocean_data(lat, lon)

        answer = str(result)

    elif intent == "sos":

        answer = (
            "This appears to be an emergency. "
            "Please use the ORCA SOS button immediately "
            "to send your GPS location to the rescue team."
        )

    else:

        answer = (
            "I can help with weather, ocean conditions, "
            "fishing/PFZ, nearby vessels, GIS information "
            "and emergency safety."
        )

    # 5. Translate answer back into the same language the question was asked in
    final_answer = translate_from_english(
        answer,
        reply_language
    )

    return {
        "answer": final_answer,
        "language": reply_language,
        "intent": intent
    }


@app.get("/")
def home():
    return {
        "message": "Ask ORCA is running"
    }


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "ask_orca.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )