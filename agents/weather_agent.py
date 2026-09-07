from datetime import datetime, timezone


class WeatherAgent:
    """
    Weather Agent for ORCA.

    Receives weather data from OpenWeather and:
    - analyzes wind
    - analyzes rain
    - analyzes temperature
    - analyzes humidity
    - analyzes pressure
    - calculates weather risk
    - provides a simple 24-hour outlook
    """

    def __init__(self):
        self.agent_name = "weather"
        self.default_source = "OpenWeather"

    # -----------------------------
    # WIND CONDITION
    # -----------------------------
    def determine_wind_condition(self, wind_speed_knots):
        if wind_speed_knots < 4:
            return "Calm"
        elif wind_speed_knots <= 10:
            return "Light Breeze"
        elif wind_speed_knots <= 16:
            return "Moderate Breeze"
        elif wind_speed_knots <= 21:
            return "Fresh Breeze"
        elif wind_speed_knots <= 27:
            return "Strong Breeze - Small Craft Caution"
        elif wind_speed_knots <= 33:
            return "Near Gale - Rough Conditions"
        elif wind_speed_knots <= 47:
            return "Gale - Hazardous Conditions"
        elif wind_speed_knots <= 63:
            return "Storm - Extremely Dangerous"
        else:
            return "Violent Storm"

    # -----------------------------
    # RAIN CONDITION
    # -----------------------------
    def determine_rain_condition(self, rain_rate):
        if rain_rate < 0.1:
            return "No Rain"
        elif rain_rate <= 2.5:
            return "Light Rain"
        elif rain_rate <= 10:
            return "Moderate Rain"
        elif rain_rate <= 35:
            return "Heavy Rain"
        else:
            return "Very Heavy Rain"

    # -----------------------------
    # WEATHER CONDITION
    # -----------------------------
    def determine_weather_condition(
        self,
        wind_condition,
        rain_condition,
        cloud_cover
    ):

        if "Storm" in wind_condition:
            return "Storm / Severe Weather"

        if "Gale" in wind_condition:
            return "Gale / High Winds"

        if "Heavy" in rain_condition:
            return "Heavy Rain / Poor Visibility"

        if rain_condition != "No Rain":
            return "Rainy Weather"

        if cloud_cover > 70:
            return "Overcast"

        if cloud_cover > 30:
            return "Partly Cloudy"

        return "Clear Weather"

    # -----------------------------
    # RISK CALCULATION
    # -----------------------------
    def calculate_risk(
        self,
        wind_speed_knots,
        rain_rate,
        temperature,
        humidity
    ):

        risk_score = 0
        warnings = []

        # Wind
        if wind_speed_knots > 33:
            risk_score += 4
            warnings.append("Very strong wind")
        elif wind_speed_knots > 27:
            risk_score += 3
            warnings.append("Strong wind")
        elif wind_speed_knots > 21:
            risk_score += 2
            warnings.append("Fresh to strong wind")

        # Rain
        if rain_rate > 35:
            risk_score += 3
            warnings.append("Very heavy rainfall")
        elif rain_rate > 10:
            risk_score += 2
            warnings.append("Heavy rainfall")
        elif rain_rate > 2.5:
            risk_score += 1

        # Temperature
        if temperature >= 40:
            risk_score += 3
            warnings.append("Extremely high temperature")
        elif temperature >= 35:
            risk_score += 2
            warnings.append("High temperature")

        # Humidity
        if humidity >= 90:
            risk_score += 2
            warnings.append("Very high humidity")
        elif humidity >= 80:
            risk_score += 1

        # Final risk
        if risk_score >= 7:
            risk = "CRITICAL"
        elif risk_score >= 5:
            risk = "HIGH"
        elif risk_score >= 3:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        return risk, risk_score, warnings

    # -----------------------------
    # 24 HOUR OUTLOOK
    # -----------------------------
    def generate_forecast_outlook(self, forecast_24_hours):

        if not forecast_24_hours:
            return "24-hour forecast data not available."

        temperatures = [
            x["temperature_c"]
            for x in forecast_24_hours
            if x.get("temperature_c") is not None
        ]

        wind_speeds = [
            x["wind_speed_knots"]
            for x in forecast_24_hours
            if x.get("wind_speed_knots") is not None
        ]

        rain_values = [
            x["rain_3h_mm"]
            for x in forecast_24_hours
            if x.get("rain_3h_mm") is not None
        ]

        max_temp = max(temperatures) if temperatures else None
        max_wind = max(wind_speeds) if wind_speeds else None
        total_rain = sum(rain_values) if rain_values else 0

        messages = []

        if max_wind and max_wind > 33:
            messages.append("Very strong winds may occur.")

        elif max_wind and max_wind > 27:
            messages.append("Strong winds may occur.")

        if total_rain > 35:
            messages.append("Heavy rainfall is possible.")

        if max_temp and max_temp >= 35:
            messages.append("High temperature conditions are expected.")

        if not messages:
            messages.append("No major severe weather condition detected.")

        return " ".join(messages)

    # -----------------------------
    # MAIN ANALYSIS
    # -----------------------------
    def analyze(self, observation, forecast_24_hours=None):

        latitude = float(observation.get("latitude", 0))
        longitude = float(observation.get("longitude", 0))

        temperature = float(
            observation.get("air_temperature", 28)
        )

        wind_speed_knots = float(
            observation.get("wind_speed_knots", 0)
        )

        wind_gust_knots = float(
            observation.get(
                "wind_gust_knots",
                wind_speed_knots
            )
        )

        wind_direction = int(
            observation.get("wind_direction_deg", 0)
        )

        rain_rate = float(
            observation.get(
                "precipitation_rate_mmh",
                0
            )
        )

        humidity = float(
            observation.get(
                "relative_humidity_pct",
                75
            )
        )

        pressure = float(
            observation.get(
                "surface_pressure_hpa",
                1010
            )
        )

        cloud_cover = int(
            observation.get(
                "cloud_cover_pct",
                0
            )
        )

        # Convert knots to km/h
        wind_speed_kmh = round(
            wind_speed_knots * 1.852,
            2
        )

        # Analyze weather
        wind_condition = self.determine_wind_condition(
            wind_speed_knots
        )

        rain_condition = self.determine_rain_condition(
            rain_rate
        )

        weather_condition = self.determine_weather_condition(
            wind_condition,
            rain_condition,
            cloud_cover
        )

        # Calculate risk
        risk, risk_score, warnings = self.calculate_risk(
            wind_speed_knots,
            rain_rate,
            temperature,
            humidity
        )

        # 24-hour forecast
        forecast_outlook = self.generate_forecast_outlook(
            forecast_24_hours
        )

        return {
            "agent": self.agent_name,

            "location": {
                "latitude": latitude,
                "longitude": longitude
            },

            "result": {

                "condition": weather_condition,

                "temperature_c": temperature,

                "wind": {
                    "speed_knots": wind_speed_knots,
                    "speed_kmh": wind_speed_kmh,
                    "gust_knots": wind_gust_knots,
                    "direction_deg": wind_direction,
                    "condition": wind_condition
                },

                "rain": {
                    "rate_mmh": rain_rate,
                    "condition": rain_condition
                },

                "humidity_pct": humidity,

                "pressure_hpa": pressure,

                "cloud_cover_pct": cloud_cover,

                "risk_score": risk_score,

                "warnings": warnings,

                "forecast_24h": forecast_outlook
            },

            "risk": risk,

            "confidence": 0.85,

            "source": self.default_source,

            "timestamp": datetime.now(
                timezone.utc
            ).isoformat()
        }