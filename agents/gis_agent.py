import os
import geopandas as gpd


def gis_agent(latitude, longitude):
    """
    GIS Agent for ORCA.

    Takes latitude and longitude and determines:
    - Whether the location is in a mapped marine area
    - Marine area name/details
    - Location type
    """

    try:
        # ---------------------------------------
        # 1. Find project root directory
        # ---------------------------------------
        BASE_DIR = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        # ---------------------------------------
        # 2. GeoJSON file path
        # ---------------------------------------
        geojson_path = os.path.join(
            BASE_DIR,
            "data",
            "raw",
            "gis",
            "marine_areas.geojson"
        )

        # ---------------------------------------
        # 3. Check GeoJSON file
        # ---------------------------------------
        if not os.path.exists(geojson_path):
            return {
                "status": "error",
                "message": "Marine areas GeoJSON file not found.",
                "expected_path": geojson_path
            }

        # ---------------------------------------
        # 4. Validate coordinates
        # ---------------------------------------
        latitude = float(latitude)
        longitude = float(longitude)

        if not (-90 <= latitude <= 90):
            return {
                "status": "error",
                "message": "Invalid latitude."
            }

        if not (-180 <= longitude <= 180):
            return {
                "status": "error",
                "message": "Invalid longitude."
            }

        # ---------------------------------------
        # 5. Load GeoJSON
        # ---------------------------------------
        gdf = gpd.read_file(geojson_path)

        if gdf.empty:
            return {
                "status": "error",
                "message": "Marine areas GeoJSON is empty."
            }

        # ---------------------------------------
        # 6. Make sure CRS is available
        # ---------------------------------------
        if gdf.crs is None:
            gdf = gdf.set_crs("EPSG:4326")

        # Convert dataset to WGS84
        gdf = gdf.to_crs("EPSG:4326")

        # ---------------------------------------
        # 7. Create user location point
        # ---------------------------------------
        user_point = gpd.GeoSeries.from_xy(
            [longitude],
            [latitude],
            crs="EPSG:4326"
        ).iloc[0]

        # ---------------------------------------
        # 8. Find marine area
        # ---------------------------------------
        matching_areas = gdf[
            gdf.geometry.contains(user_point)
            | gdf.geometry.touches(user_point)
        ]

        # ---------------------------------------
        # 9. Location is outside mapped area
        # ---------------------------------------
        if matching_areas.empty:

            return {
                "status": "success",
                "latitude": latitude,
                "longitude": longitude,
                "location_type": "outside_mapped_marine_area",
                "marine_area_found": False,
                "marine_area": None,
                "message": "Location is not inside any mapped marine area."
            }

        # ---------------------------------------
        # 10. Convert marine area information
        # ---------------------------------------
        area_data = matching_areas.drop(
            columns="geometry"
        ).to_dict(orient="records")

        # ---------------------------------------
        # 11. Return ORCA GIS result
        # ---------------------------------------
        return {
            "status": "success",
            "latitude": latitude,
            "longitude": longitude,
            "location_type": "marine",
            "marine_area_found": True,
            "marine_area": area_data,
            "message": "Location is inside a mapped marine area."
        }

    except ValueError:
        return {
            "status": "error",
            "message": "Latitude and longitude must be valid numbers."
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# ---------------------------------------
# Test the GIS Agent directly
# ---------------------------------------
if __name__ == "__main__":

    latitude = 18.638
    longitude = 72.508

    result = gis_agent(latitude, longitude)

    import json

    print(json.dumps(result, indent=2))