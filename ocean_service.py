import os
import xarray as xr


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OCEAN_DATA_FILE = os.path.join(
    BASE_DIR,
    "ocean_data.nc"
)


def get_ocean_data(latitude, longitude):

    ds = xr.open_dataset(
        OCEAN_DATA_FILE,
        engine="netcdf4"
    )

    try:

        # Find nearest grid point
        point = ds.sel(
            IOYAXIS=latitude,
            IOXAXIS=longitude,
            method="nearest"
        )

        # Use first/latest available time
        data = point.isel(TIME=0)

        wave_height = float(
            data["HS"].values
        )

        peak_period = float(
            data["PWP"].values
        )

        wind_u = float(
            data["UWND"].values
        )

        wind_v = float(
            data["VWND"].values
        )

        # Calculate wind speed from U/V components
        wind_speed_ms = (
            wind_u ** 2 +
            wind_v ** 2
        ) ** 0.5

        return {

            "significant_wave_height":
                wave_height,

            "swell_height":
                None,

            "swell_period":
                peak_period,

            "current_speed":
                None,

            "wind_u":
                wind_u,

            "wind_v":
                wind_v,

            "wind_speed_ms":
                round(wind_speed_ms, 2),

            "latitude":
                float(point["IOYAXIS"].values),

            "longitude":
                float(point["IOXAXIS"].values)

        }

    finally:

        ds.close()