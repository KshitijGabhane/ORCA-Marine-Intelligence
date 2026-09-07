from datetime import datetime


def create_location_data(
    latitude,
    longitude,
    accuracy
):

    return {
        "latitude": latitude,
        "longitude": longitude,
        "accuracy": accuracy,
        "timestamp": datetime.now()
    }


def get_location_type(
    latitude,
    longitude
):

    if latitude is not None and longitude is not None:
        return "CURRENT"

    return "LAST_KNOWN"