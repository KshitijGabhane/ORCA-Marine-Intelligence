from ocean_service import get_ocean_data


# Arabian Sea test location
LATITUDE = 18.5
LONGITUDE = 72.5


print()
print("==============================")
print("OCEAN DATA TEST")
print("==============================")

try:
    data = get_ocean_data(LATITUDE, LONGITUDE)

    for key, value in data.items():
        print(f"{key}: {value}")

    print("==============================")
    print("TEST COMPLETED")
    print("==============================")

except Exception as e:
    print("==============================")
    print("TEST FAILED")
    print("==============================")
    print("Error:", e)