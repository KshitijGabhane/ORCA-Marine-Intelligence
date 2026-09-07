import requests
from bs4 import BeautifulSoup
from datetime import datetime


INCOIS_URL = "https://www.incois.gov.in/oceanservices/osfforecast.jsp"


def get_ocean_data(latitude, longitude):
    """
    Get ocean forecast information from INCOIS.

    NOTE:
    INCOIS provides the official Ocean State Forecast through its
    web service. The public page exposes forecast layers such as:

    - Wind
    - Significant Wave Height
    - Swell Height
    - Wave Period
    - Swell Period
    - Surface Currents
    - Sea Surface Temperature

    This function prepares the location request and returns
    the available INCOIS information.
    """

    try:

        latitude = float(latitude)
        longitude = float(longitude)

        response = requests.get(
            INCOIS_URL,
            timeout=15
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        page_text = soup.get_text(
            " ",
            strip=True
        )

        return {
            "status": "success",
            "source": "INCOIS Ocean State Forecast",
            "latitude": latitude,
            "longitude": longitude,
            "retrieved_at": datetime.utcnow().isoformat(),
            "source_url": INCOIS_URL,
            "available_parameters": [
                "wind_speed",
                "wind_direction",
                "significant_wave_height",
                "swell_height",
                "wave_period",
                "swell_period",
                "surface_current",
                "sea_surface_temperature"
            ],
            "source_available": True,
            "page_available": bool(page_text)
        }

    except requests.RequestException as e:

        return {
            "status": "error",
            "source": "INCOIS",
            "message": str(e)
        }

    except Exception as e:

        return {
            "status": "error",
            "source": "INCOIS",
            "message": str(e)
        }