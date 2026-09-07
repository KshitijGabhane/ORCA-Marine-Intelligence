from datetime import datetime, timezone


def normalize_weather_forecast(data):

    forecast_list = data.get("list", [])

    if not forecast_list:
        raise Exception("No forecast data received from OpenWeather")

    # First forecast point
    current = forecast_list[0]

    main = current.get("main", {})
    wind = current.get("wind", {})
    clouds = current.get("clouds", {})

    # OpenWeather wind speed is m/s
    # Convert m/s → knots
    wind_speed_knots = wind.get("speed", 0) * 1.94384

    wind_gust_knots = wind.get(
        "gust",
        wind.get("speed", 0)
    ) * 1.94384

    rain = current.get("rain", {})

    precipitation = rain.get(
        "3h",
        0
    )

    # OpenWeather gives rain for 3 hours.
    # Convert approximately to mm/hour.
    precipitation_rate = precipitation / 3

    observation = {
        "latitude": data["city"]["coord"]["lat"],
        "longitude": data["city"]["coord"]["lon"],

        "timestamp": datetime.now(timezone.utc).isoformat(),

        "air_temperature": main.get("temp", 28.0),

        "wind_speed_knots": round(
            wind_speed_knots,
            2
        ),

        "wind_gust_knots": round(
            wind_gust_knots,
            2
        ),

        "wind_direction_deg": wind.get(
            "deg",
            0
        ),

        "precipitation_rate_mmh": round(
            precipitation_rate,
            2
        ),

        "relative_humidity_pct": main.get(
            "humidity",
            75
        ),

        "surface_pressure_hpa": main.get(
            "pressure",
            1010
        ),

        "pressure_tendency_3h": 0.0,

        "cloud_cover_pct": clouds.get(
            "all",
            0
        ),

        # OpenWeather is NOT IMD.
        # Therefore we don't fake an IMD warning.
        "imd_official_warning": "NONE"
    }

    return observation


def get_next_24_hours(data):

    forecast_list = data.get("list", [])

    if not forecast_list:
        return []

    now = datetime.now(timezone.utc)

    next_24_hours = []

    for item in forecast_list:

        timestamp = item.get("dt")

        if timestamp is None:
            continue

        forecast_time = datetime.fromtimestamp(
            timestamp,
            timezone.utc
        )

        difference = (
            forecast_time - now
        ).total_seconds()

        if 0 <= difference <= 24 * 60 * 60:

            main = item.get("main", {})
            wind = item.get("wind", {})
            clouds = item.get("clouds", {})

            rain = item.get("rain", {})

            next_24_hours.append({
                "timestamp": forecast_time.isoformat(),

                "temperature_c": main.get(
                    "temp"
                ),

                "humidity_pct": main.get(
                    "humidity"
                ),

                "pressure_hpa": main.get(
                    "pressure"
                ),

                "wind_speed_knots": round(
                    wind.get("speed", 0) * 1.94384,
                    2
                ),

                "wind_direction_deg": wind.get(
                    "deg",
                    0
                ),

                "cloud_cover_pct": clouds.get(
                    "all",
                    0
                ),

                "rain_3h_mm": rain.get(
                    "3h",
                    0
                )
            })

    return next_24_hours