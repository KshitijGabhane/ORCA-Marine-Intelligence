import requests
import json
import os
from datetime import datetime

# Put the actual INCOIS REST API URL here
INCOIS_API_URL = os.getenv("INCOIS_PFZ_API_URL")


def fetch_pfz_data():
    if not INCOIS_API_URL:
        raise Exception("INCOIS_PFZ_API_URL is not configured")

    response = requests.get(
        INCOIS_API_URL,
        timeout=20
    )

    response.raise_for_status()

    return response.json()


def save_pfz_data(data):
    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "raw",
        "fisheries",
        "pfz_data.json"
    )

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("Latest PFZ data saved.")


def update_pfz():
    data = fetch_pfz_data()
    save_pfz_data(data)
    return data