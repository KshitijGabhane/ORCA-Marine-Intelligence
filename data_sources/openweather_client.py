import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"


def get_weather_forecast(latitude, longitude):

    if not OPENWEATHER_API_KEY:
        raise Exception("OPENWEATHER_API_KEY is not configured")

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    return response.json()