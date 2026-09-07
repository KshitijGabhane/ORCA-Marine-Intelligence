from flask import Blueprint, request, jsonify

from services.ocean_service import get_ocean_data
from agents.ocean_agent import ocean_agent


ocean_bp = Blueprint("ocean", __name__)


@ocean_bp.route("/api/ocean", methods=["GET"])
def ocean_api():

    try:
        latitude = request.args.get("lat")
        longitude = request.args.get("lon")

        if latitude is None or longitude is None:
            return jsonify({
                "status": "error",
                "message": "Latitude and longitude are required"
            }), 400

        latitude = float(latitude)
        longitude = float(longitude)

        # Get ocean data
        ocean_data = get_ocean_data(
            latitude,
            longitude
        )

        if ocean_data.get("status") != "success":
            return jsonify({
                "status": "error",
                "message": ocean_data.get(
                    "message",
                    "Unable to get ocean data"
                )
            }), 500

        # IMPORTANT:
        # OceanAgent requires:
        # latitude, longitude, ocean_data

        result = ocean_agent.analyze(
            latitude,
            longitude,
            ocean_data
        )

        return jsonify({
            "status": "success",
            "data": result
        })

    except ValueError:
        return jsonify({
            "status": "error",
            "message": "Invalid latitude or longitude"
        }), 400

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500