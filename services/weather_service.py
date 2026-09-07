from data_sources.openweather_client import get_weather_forecast
from data_sources.weather_normalizer import (
    normalize_weather_forecast,
    get_next_24_hours
)
from agents.weather_agent import WeatherAgent


weather_agent = WeatherAgent()


def analyze_weather(latitude, longitude):

    # Get weather forecast from OpenWeather
    weather_data = get_weather_forecast(
        latitude,
        longitude
    )

    # Convert OpenWeather data into Weather Agent format
    observation = normalize_weather_forecast(
        weather_data
    )

    # Get next 24 hours
    forecast_24_hours = get_next_24_hours(
        weather_data
    )

    # Send current weather + 24 hour forecast to Weather Agent
    agent_result = weather_agent.analyze(
        observation,
        forecast_24_hours
    )

    return {
        "agent_result": agent_result,
        "forecast_24_hours": forecast_24_hours,
        "source": "OpenWeather",
        "location": {
            "latitude": latitude,
            "longitude": longitude
        }
    }