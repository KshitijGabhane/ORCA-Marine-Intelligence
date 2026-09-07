import requests
import os

URL = "https://incois.gov.in/thredds/fileServer/osf/ww3/rsmc_combined_ww3_20260905.nc"

OUTPUT = "ocean_data.nc"

print("Downloading INCOIS ocean data...")
print("This file may be large. Please wait...")

response = requests.get(URL, stream=True, timeout=120)

if response.status_code != 200:
    print("Download failed")
    print("Status:", response.status_code)
    exit()

with open(OUTPUT, "wb") as f:
    for chunk in response.iter_content(chunk_size=1024 * 1024):
        if chunk:
            f.write(chunk)

size_mb = os.path.getsize(OUTPUT) / (1024 * 1024)

print()
print("================================")
print("OCEAN DATA DOWNLOADED")
print("================================")
print("File:", OUTPUT)
print(f"Size: {size_mb:.2f} MB")
print("Source: INCOIS RSMC")
print("================================")