import os
import json
import time
import websocket
from dotenv import load_dotenv

# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

AISSTREAM_API_KEY = os.getenv("AISSTREAM_API_KEY")

AISSTREAM_URL = "wss://stream.aisstream.io/v0/stream"


# ============================================================
# GET NEARBY LIVE VESSELS
# ============================================================

def get_nearby_vessels(
    latitude: float,
    longitude: float,
    radius_degree: float = 0.5,
    timeout: int = 30
) -> list:

    # --------------------------------------------------------
    # Check API key
    # --------------------------------------------------------

    if not AISSTREAM_API_KEY:

        raise Exception(
            "AISSTREAM_API_KEY is missing in .env"
        )

    # --------------------------------------------------------
    # Create bounding box
    # --------------------------------------------------------

    lat_min = latitude - radius_degree
    lat_max = latitude + radius_degree

    lon_min = longitude - radius_degree
    lon_max = longitude + radius_degree

    print(
        f"Searching AIS vessels around "
        f"{latitude}, {longitude}"
    )

    print(
        f"Bounding box:"
        f"\n  Latitude : {lat_min} to {lat_max}"
        f"\n  Longitude: {lon_min} to {lon_max}"
    )

    # --------------------------------------------------------
    # AISStream subscription
    # --------------------------------------------------------

    subscribe_message = {

        "APIKey": AISSTREAM_API_KEY,

        "BoundingBoxes": [
            [
                [lat_min, lon_min],
                [lat_max, lon_max]
            ]
        ],

        "FilterMessageTypes": [
            "PositionReport"
        ]
    }

    vessels = {}

    ws = None

    start_time = time.monotonic()

    try:

        # ----------------------------------------------------
        # CONNECT
        # ----------------------------------------------------

        print("\nConnecting to AISStream...")

        ws = websocket.create_connection(
            AISSTREAM_URL,
            timeout=2
        )

        print("Connected to AISStream")

        # ----------------------------------------------------
        # SEND SUBSCRIPTION
        # ----------------------------------------------------

        ws.send(
            json.dumps(subscribe_message)
        )

        print("Subscription sent")
        print("Waiting for live AIS data...\n")

        # ----------------------------------------------------
        # RECEIVE AIS DATA
        # ----------------------------------------------------

        while True:

            # -----------------------------------------------
            # Overall timeout
            # -----------------------------------------------

            elapsed = time.monotonic() - start_time

            if elapsed >= timeout:

                print(
                    f"\nAIS listening finished "
                    f"after {timeout} seconds."
                )

                break

            try:

                message = ws.recv()

                # -------------------------------------------
                # Empty message
                # -------------------------------------------

                if not message:

                    print(
                        "AISStream closed the connection."
                    )

                    break

                # -------------------------------------------
                # Convert JSON
                # -------------------------------------------

                try:

                    data = json.loads(message)

                except json.JSONDecodeError:

                    print(
                        "Invalid AIS message received."
                    )

                    continue

                # -------------------------------------------
                # Get message type
                # -------------------------------------------

                message_type = data.get(
                    "MessageType"
                )

                print(
                    "Received:",
                    message_type
                )

                # -------------------------------------------
                # Subscription confirmation
                # -------------------------------------------

                if message_type == "SubscriptionConfirmation":

                    print(
                        "AIS subscription confirmed."
                    )

                    continue

                # -------------------------------------------
                # Position Report
                # -------------------------------------------

                if message_type == "PositionReport":

                    position = data.get(
                        "Message",
                        {}
                    ).get(
                        "PositionReport",
                        {}
                    )

                    mmsi = position.get(
                        "UserID"
                    )

                    # Skip if MMSI unavailable
                    if not mmsi:
                        continue

                    # ---------------------------------------
                    # Create / update vessel
                    # ---------------------------------------

                    vessel = vessels.get(
                        mmsi,
                        {
                            "mmsi": mmsi
                        }
                    )

                    vessel["latitude"] = position.get(
                        "Latitude"
                    )

                    vessel["longitude"] = position.get(
                        "Longitude"
                    )

                    vessel["speed_knots"] = position.get(
                        "Sog"
                    )

                    vessel["course"] = position.get(
                        "Cog"
                    )

                    vessel["heading"] = position.get(
                        "TrueHeading"
                    )

                    vessel["navigation_status"] = position.get(
                        "NavigationalStatus"
                    )

                    vessels[mmsi] = vessel

                    print(
                        f"✓ Vessel received: {mmsi}"
                    )

            # ------------------------------------------------
            # WebSocket timeout
            # ------------------------------------------------

            except websocket.WebSocketTimeoutException:

                # recv() waited 2 seconds without receiving
                # anything. Check overall timeout and continue.

                elapsed = time.monotonic() - start_time

                if elapsed >= timeout:

                    print(
                        f"\nAIS listening finished "
                        f"after {timeout} seconds."
                    )

                    break

                print(
                    "No AIS message yet..."
                )

                continue

            # ------------------------------------------------
            # Other WebSocket errors
            # ------------------------------------------------

            except websocket.WebSocketConnectionClosedException:

                print(
                    "AISStream connection closed."
                )

                break

            except Exception as e:

                error_text = str(e).lower()

                # Some websocket versions report timeout
                # as a normal Exception.

                if (
                    "timeout" in error_text
                    or "timed out" in error_text
                ):

                    elapsed = (
                        time.monotonic()
                        - start_time
                    )

                    if elapsed >= timeout:

                        print(
                            f"\nAIS listening finished "
                            f"after {timeout} seconds."
                        )

                        break

                    print(
                        "No AIS message yet..."
                    )

                    continue

                print(
                    "AIS receive error:",
                    e
                )

                break

    except Exception as e:

        print(
            "\nAISStream connection error:"
        )

        print(e)

        raise

    finally:

        # ----------------------------------------------------
        # CLOSE CONNECTION
        # ----------------------------------------------------

        if ws:

            try:
                ws.close()

            except Exception:
                pass

            print(
                "AIS connection closed."
            )

    # --------------------------------------------------------
    # RETURN VESSELS
    # --------------------------------------------------------

    return list(
        vessels.values()
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("\n======================================")
    print("       ORCA AIS CLIENT TEST")
    print("======================================\n")

    # --------------------------------------------------------
    # Get coordinates
    # --------------------------------------------------------

    try:

        latitude = float(
            input("Enter latitude: ")
        )

        longitude = float(
            input("Enter longitude: ")
        )

    except ValueError:

        print(
            "Invalid latitude or longitude."
        )

        exit()

    print(
        "\nStarting live AIS search..."
    )

    try:

        vessels = get_nearby_vessels(

            latitude=latitude,

            longitude=longitude,

            # 2 degrees around location
            radius_degree=2,

            # Stop after 120 seconds
            timeout=120
        )

        # ----------------------------------------------------
        # RESULTS
        # ----------------------------------------------------

        print(
            "\n======================================"
        )

        print(
            f"Total vessels received: {len(vessels)}"
        )

        print(
            "======================================\n"
        )

        if not vessels:

            print(
                "No AIS vessels received "
                "during this test."
            )

        else:

            for vessel in vessels:

                print(
                    "--------------------------------------"
                )

                print(
                    "MMSI:",
                    vessel.get("mmsi")
                )

                print(
                    "Latitude:",
                    vessel.get("latitude")
                )

                print(
                    "Longitude:",
                    vessel.get("longitude")
                )

                print(
                    "Speed:",
                    vessel.get(
                        "speed_knots"
                    ),
                    "knots"
                )

                print(
                    "Course:",
                    vessel.get(
                        "course"
                    )
                )

                print(
                    "Heading:",
                    vessel.get(
                        "heading"
                    )
                )

                print(
                    "Navigation Status:",
                    vessel.get(
                        "navigation_status"
                    )
                )

        print(
            "\n======================================"
        )
        print("AIS TEST FINISHED")
        print(
            "======================================\n"
        )

    except Exception as e:

        print(
            "\n======================================"
        )

        print(
            "AISStream Error:"
        )

        print(e)

        print(
            "======================================\n"
        )