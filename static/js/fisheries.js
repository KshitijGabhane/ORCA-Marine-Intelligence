// ============================================================
// ORCA FISHERIES INTELLIGENCE
// LIVE FISHERIES AGENT
// ============================================================


// ============================================================
// MAP
// ============================================================

const map = L.map("fisheriesMap").setView(
    [20.5, 78.9],
    5
);


L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        attribution:
            "&copy; OpenStreetMap contributors"
    }
).addTo(map);


// ============================================================
// MARKERS
// ============================================================

let userMarker = null;
let pfzMarker = null;


// ============================================================
// HELPER
// ============================================================

function setText(id, value) {

    const element =
        document.getElementById(id);

    if (element) {

        element.textContent = value;

    }

}


// ============================================================
// GET GPS
// ============================================================

function startGPS() {

    if (!navigator.geolocation) {

        setText(
            "status",
            "❌ GPS is not supported."
        );

        return;

    }


    setText(
        "status",
        "📍 Getting your live location..."
    );


    navigator.geolocation.getCurrentPosition(

        handleLocation,

        handleGPSError,

        {

            enableHighAccuracy: true,

            timeout: 15000,

            maximumAge: 5000

        }

    );

}


// ============================================================
// GPS SUCCESS
// ============================================================

async function handleLocation(position) {

    const latitude =
        position.coords.latitude;

    const longitude =
        position.coords.longitude;


    setText(
        "latitude",
        latitude.toFixed(6) + "°"
    );


    setText(
        "longitude",
        longitude.toFixed(6) + "°"
    );


    setText(
        "status",
        "🟢 Location found. Fetching Fisheries data..."
    );


    // ========================================================
    // USER MARKER
    // ========================================================

    userMarker =
        L.marker([
            latitude,
            longitude
        ])
        .addTo(map)
        .bindPopup(
            "📍 Your Current Location"
        );


    map.setView(
        [latitude, longitude],
        9
    );


    // ========================================================
    // CALL FISHERIES AGENT
    // ========================================================

    await fetchFisheries(
        latitude,
        longitude
    );

}


// ============================================================
// FISHERIES API
// ============================================================

async function fetchFisheries(
    latitude,
    longitude
) {

    try {

        const response =
            await fetch(
                `/api/fisheries?lat=${latitude}&lon=${longitude}`
            );


        if (!response.ok) {

            throw new Error(
                "HTTP " + response.status
            );

        }


        const data =
            await response.json();


        console.log(
            "Fisheries Agent:",
            data
        );


        if (data.status !== "success") {

            throw new Error(
                data.message ||
                "Fisheries Agent failed"
            );

        }


        const fisheries =
            data.result;


        // ====================================================
        // DISPLAY DATA
        // ====================================================

        if (fisheries.pfz_found) {

            setText(
                "pfzZone",
                fisheries.zone_id
            );


            setText(
                "pfzCoast",
                fisheries.coast
            );


            setText(
                "pfzDistance",
                fisheries.distance_from_user_km +
                " km"
            );


            setText(
                "pfzDirection",
                fisheries.direction
            );


            setText(
                "pfzBearing",
                fisheries.bearing_deg +
                "°"
            );


            setText(
                "pfzDepth",
                fisheries.depth_m +
                " m"
            );

        }

        else {

            setText(
                "pfzZone",
                "No PFZ"
            );


            setText(
                "pfzCoast",
                "Unavailable"
            );


            setText(
                "pfzDistance",
                "Unavailable"
            );


            setText(
                "pfzDirection",
                "Unavailable"
            );


            setText(
                "pfzBearing",
                "Unavailable"
            );


            setText(
                "pfzDepth",
                "Unavailable"
            );

        }


        // ====================================================
        // RISK
        // ====================================================

        setText(
            "pfzRisk",
            data.risk || "UNKNOWN"
        );


        // ====================================================
        // SOURCE
        // ====================================================

        setText(
            "pfzSource",
            data.source ||
            "INCOIS PFZ Advisory"
        );


        // ====================================================
        // PFZ MARKER
        // ====================================================

        if (fisheries.pfz_found) {

            const pfzLatitude =
                fisheries.latitude;

            const pfzLongitude =
                fisheries.longitude;


            if (pfzMarker) {

                pfzMarker.setLatLng([
                    pfzLatitude,
                    pfzLongitude
                ]);

            }

            else {

                pfzMarker =
                    L.marker([
                        pfzLatitude,
                        pfzLongitude
                    ])
                    .addTo(map);

            }


            pfzMarker.bindPopup(`

                <strong>
                    🎣 Potential Fishing Zone
                </strong>

                <br><br>

                Zone:
                ${fisheries.zone_id}

                <br>

                Coast:
                ${fisheries.coast}

                <br>

                Direction:
                ${fisheries.direction}

                <br>

                Bearing:
                ${fisheries.bearing_deg}°

                <br>

                Depth:
                ${fisheries.depth_m} m

            `);


            // Show user + PFZ together

            const bounds =
                L.latLngBounds([

                    [
                        latitude,
                        longitude
                    ],

                    [
                        pfzLatitude,
                        pfzLongitude
                    ]

                ]);


            map.fitBounds(
                bounds,
                {
                    padding: [50, 50]
                }
            );

        }


        setText(
            "status",
            fisheries.pfz_found
                ? "🟢 PFZ found near your location."
                : "🟡 No PFZ found within the current search range."
        );


    }

    catch (error) {

        console.error(
            "Fisheries API error:",
            error
        );


        setText(
            "status",
            "❌ Unable to load Fisheries Agent data."
        );


        setText(
            "pfzZone",
            "Unavailable"
        );


        setText(
            "pfzCoast",
            "Unavailable"
        );


        setText(
            "pfzDistance",
            "Unavailable"
        );


        setText(
            "pfzDirection",
            "Unavailable"
        );


        setText(
            "pfzBearing",
            "Unavailable"
        );


        setText(
            "pfzDepth",
            "Unavailable"
        );


        setText(
            "pfzRisk",
            "ERROR"
        );


        setText(
            "pfzSource",
            "Unavailable"
        );

    }

}


// ============================================================
// GPS ERROR
// ============================================================

function handleGPSError(error) {

    console.error(
        "GPS Error:",
        error
    );


    setText(
        "status",
        "❌ Unable to get your location."
    );

}


// ============================================================
// START
// ============================================================

startGPS();