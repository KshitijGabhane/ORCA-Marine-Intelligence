/* ============================================================
   ORCA FISHERMAN DASHBOARD
   ============================================================

   LIVE AGENTS

   Weather Agent
   Ocean Agent
   Fisheries Agent
   Vessel Agent
   GIS Agent

   FEATURES

   ✓ Live weather
   ✓ Live wind
   ✓ Live ocean conditions
   ✓ Live vessel data
   ✓ GIS location
   ✓ Permanent PFZ fishing regions
   ✓ Distance from fisherman to PFZ
   ✓ Bearing / direction
   ✓ Marine route
   ✓ Normal map
   ✓ Satellite map
   ✓ GPS location
   ✓ Selected location
   ✓ Clear selected location
   ✓ Vessel refresh
   ✓ Mobile responsive support
   ✓ Integrated SOS
   ✓ Live SOS GPS tracking

   NO:
   ✗ Hardcoded weather
   ✗ Hardcoded ocean values
   ✗ Hardcoded PFZ regions
   ✗ Biodiversity Agent
   ✗ Red danger polygon
============================================================ */


/* ============================================================
   GLOBAL VARIABLES
============================================================ */

let map = null;

let currentMarker = null;

let selectedMarker = null;

let currentLatitude = null;

let currentLongitude = null;

let selectedLatitude = null;

let selectedLongitude = null;


/* ============================================================
   MAP LAYERS
============================================================ */

let satelliteLayer = null;

let normalLayer = null;

let pfzLayer = null;

let vesselLayer = null;

let routeLayer = null;


/* ============================================================
   RISK VALUES
============================================================ */

let currentWeatherRisk = null;

let currentOceanRisk = null;

let currentVesselRisk = null;


/* ============================================================
   GPS WATCH ID
============================================================ */

let gpsWatchId = null;


/* ============================================================
   SOS GLOBAL STATE
============================================================ */

let activeSosId = null;

let sosLocationWatchId = null;

let currentGPSAccuracy = null;


/* ============================================================
   HELPER - SET TEXT
============================================================ */

function setText(id, value) {

    const element =
        document.getElementById(id);

    if (!element) {
        return;
    }

    element.textContent =
        value ?? "--";
}


/* ============================================================
   HELPER - SET HTML
============================================================ */

function setHTML(id, value) {

    const element =
        document.getElementById(id);

    if (!element) {
        return;
    }

    element.innerHTML =
        value ?? "";
}


/* ============================================================
   API HELPER
============================================================ */

async function fetchJSON(url, options = {}) {

    const response =
        await fetch(url, options);

    let data = null;

    try {

        data =
            await response.json();

    }
    catch (error) {

        throw new Error(
            `Invalid server response. HTTP ${response.status}`
        );

    }


    if (!response.ok) {

        throw new Error(
            data?.message ||
            `HTTP ${response.status}`
        );

    }


    return data;

}


/* ============================================================
   INITIALIZE MAP
============================================================ */

function initializeMap() {

    const mapElement =
        document.getElementById("map");


    if (!mapElement) {

        console.error(
            "ORCA: #map element not found."
        );

        return;

    }


    /* ========================================================
       NORMAL MAP
    ======================================================== */

    normalLayer =
        L.tileLayer(

            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",

            {

                maxZoom: 19,

                attribution:
                    "&copy; OpenStreetMap contributors"

            }

        );


    /* ========================================================
       SATELLITE MAP
    ======================================================== */

    satelliteLayer =
        L.tileLayer(

            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",

            {

                maxZoom: 19,

                attribution:
                    "&copy; Esri"

            }

        );


    /* ========================================================
       CREATE MAP
    ======================================================== */

    map =
        L.map(

            "map",

            {

                center: [
                    15,
                    78
                ],

                zoom: 5,

                layers: [
                    normalLayer
                ],

                zoomControl: true

            }

        );


    /* ========================================================
       PFZ LAYER
    ======================================================== */

    pfzLayer =
        L.layerGroup()
            .addTo(map);


    /* ========================================================
       VESSEL LAYER
    ======================================================== */

    vesselLayer =
        L.layerGroup()
            .addTo(map);


    /* ========================================================
       ROUTE LAYER
    ======================================================== */

    routeLayer =
        L.layerGroup()
            .addTo(map);


    /* ========================================================
       LAYER CONTROL
    ======================================================== */

    L.control.layers(

        {

            "🗺 Normal":
                normalLayer,

            "🛰 Satellite":
                satelliteLayer

        },

        {

            "🎣 Fishing Regions":
                pfzLayer,

            "🚢 Vessels":
                vesselLayer,

            "🧭 Route":
                routeLayer

        },

        {

            collapsed: true,

            position: "topright"

        }

    ).addTo(map);


    /* ========================================================
       MAP CLICK
    ======================================================== */

    map.on(
        "click",
        handleMapClick
    );


    /* ========================================================
       LOAD PFZ REGIONS
    ======================================================== */

    loadAllFishingRegions();

}


/* ============================================================
   MAP CLICK
============================================================ */

async function handleMapClick(event) {

    const latitude =
        Number(event.latlng.lat);

    const longitude =
        Number(event.latlng.lng);


    if (
        !Number.isFinite(latitude) ||
        !Number.isFinite(longitude)
    ) {

        return;

    }


    selectedLatitude =
        latitude;

    selectedLongitude =
        longitude;


    if (selectedMarker) {

        map.removeLayer(
            selectedMarker
        );

        selectedMarker = null;

    }


    selectedMarker =
        L.marker(

            [
                latitude,
                longitude
            ]

        )
        .addTo(map);


    selectedMarker.bindPopup(

        `
        <div>
            <b>📍 Selected Marine Location</b>
            <br><br>
            Latitude:
            ${latitude.toFixed(5)}°
            <br>
            Longitude:
            ${longitude.toFixed(5)}°
        </div>
        `

    ).openPopup();


    setText(
        "selectedLatitude",
        latitude.toFixed(5) + "°"
    );


    setText(
        "selectedLongitude",
        longitude.toFixed(5) + "°"
    );


    setText(
        "selectedLocation",
        `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`
    );


    setText(
        "selectedMarineArea",
        "Loading..."
    );


    showSelectedLocationSection();


    await loadLocationAgents(
        latitude,
        longitude
    );

}


/* ============================================================
   SHOW SELECTED LOCATION SECTION
============================================================ */

function showSelectedLocationSection() {

    const possibleIds = [

        "selectedLocationSection",

        "selectedLocationCard",

        "locationSection",

        "selectedLocationContainer"

    ];


    possibleIds.forEach(
        id => {

            const element =
                document.getElementById(id);

            if (element) {

                element.style.display =
                    "";

            }

        }
    );

}


/* ============================================================
   CLEAR SELECTED LOCATION
============================================================ */

function clearSelectedLocation() {

    console.log(
        "🧹 Clearing selected marine location..."
    );


    selectedLatitude =
        null;

    selectedLongitude =
        null;


    if (selectedMarker) {

        try {

            map.removeLayer(
                selectedMarker
            );

        }
        catch (error) {

            console.warn(
                "Unable to remove selected marker:",
                error
            );

        }

        selectedMarker = null;

    }


    if (routeLayer) {

        routeLayer.clearLayers();

    }


    currentWeatherRisk =
        null;

    currentOceanRisk =
        null;


    setText(
        "selectedLatitude",
        "--"
    );

    setText(
        "selectedLongitude",
        "--"
    );

    setText(
        "selectedLocation",
        "--"
    );

    setText(
        "selectedMarineArea",
        "--"
    );

    setText(
        "gisInformation",
        "--"
    );


    setText(
        "temperature",
        "--"
    );

    setText(
        "wind",
        "--"
    );

    setText(
        "weatherCondition",
        "--"
    );

    setText(
        "weatherRisk",
        "--"
    );

    setText(
        "temperatureStatus",
        "--"
    );

    setText(
        "windStatus",
        "--"
    );

    setText(
        "weatherSource",
        "--"
    );


    setText(
        "waveHeight",
        "--"
    );

    setText(
        "seaState",
        "--"
    );

    setText(
        "swell",
        "--"
    );

    setText(
        "oceanRisk",
        "--"
    );

    setText(
        "oceanSource",
        "--"
    );


    setText(
        "selectedPFZ",
        "--"
    );

    setText(
        "pfzDepth",
        "--"
    );

    setText(
        "pfzDistance",
        "--"
    );

    setText(
        "pfzDirection",
        "--"
    );

    setHTML(
        "pfzDetails",
        "No fishing region selected."
    );


    setText(
        "safetyMessage",
        "Select a marine location to view live conditions."
    );


    const possibleIds = [

        "selectedLocationSection",

        "selectedLocationCard",

        "locationSection",

        "selectedLocationContainer"

    ];


    possibleIds.forEach(
        id => {

            const element =
                document.getElementById(id);

            if (element) {

                element.style.display =
                    "none";

            }

        }
    );


    console.log(
        "✅ Selected location cleared."
    );

}


/* ============================================================
   CONNECT CROSS / CLEAR BUTTON
============================================================ */

function connectClearButtons() {

    const buttonIds = [

        "clearSelectedLocation",

        "selectedLocationClose",

        "closeSelectedLocation",

        "clearLocationButton",

        "selectedLocationCloseButton",

        "closeLocationButton"

    ];


    buttonIds.forEach(
        id => {

            const button =
                document.getElementById(id);

            if (!button) {
                return;
            }


            button.addEventListener(
                "click",
                clearSelectedLocation
            );

        }
    );

}


/* ============================================================
   LOAD ALL AGENTS
============================================================ */

async function loadLocationAgents(
    latitude,
    longitude
) {

    currentWeatherRisk =
        null;

    currentOceanRisk =
        null;


    setText(
        "temperature",
        "Loading..."
    );

    setText(
        "wind",
        "Loading..."
    );

    setText(
        "weatherCondition",
        "Loading..."
    );

    setText(
        "waveHeight",
        "Loading..."
    );

    setText(
        "seaState",
        "Loading..."
    );

    setText(
        "swell",
        "Loading..."
    );

    setText(
        "selectedMarineArea",
        "Loading..."
    );


    await Promise.allSettled([

        loadWeather(
            latitude,
            longitude
        ),

        loadOcean(
            latitude,
            longitude
        ),

        loadGIS(
            latitude,
            longitude
        )

    ]);


    updateSafetyMessage();

}


/* ============================================================
   WEATHER AGENT
============================================================ */

async function loadWeather(
    latitude,
    longitude
) {

    try {

        console.log(
            "🌤 Weather Agent request:",
            latitude,
            longitude
        );


        const data =
            await fetchJSON(

                `/api/weather?lat=${encodeURIComponent(latitude)}&lon=${encodeURIComponent(longitude)}`

            );


        console.log(
            "🌤 Weather Agent response:",
            data
        );


        if (
            data.status &&
            data.status !== "success"
        ) {

            throw new Error(
                data.message ||
                "Weather Agent failed"
            );

        }


        const agent =
            data.data?.agent_result ||
            data.agent_result ||
            data.data ||
            data;


        if (!agent) {

            throw new Error(
                "Weather Agent result missing"
            );

        }


        const result =
            agent.result ||
            agent;


        const temperature =
            Number(
                result.temperature_c ??
                result.temperature ??
                result.temp_c
            );


        if (
            Number.isFinite(
                temperature
            )
        ) {

            setText(
                "temperature",
                temperature.toFixed(1) +
                " °C"
            );

        }
        else {

            setText(
                "temperature",
                "Unavailable"
            );

        }


        const wind =
            result.wind ||
            {};


        const speedKmh =
            Number(
                wind.speed_kmh ??
                result.wind_speed_kmh
            );


        const speedKnots =
            Number(
                wind.speed_knots ??
                result.wind_speed_knots
            );


        let displayWind =
            null;


        if (
            Number.isFinite(
                speedKmh
            )
        ) {

            displayWind =
                speedKmh;

        }
        else if (
            Number.isFinite(
                speedKnots
            )
        ) {

            displayWind =
                speedKnots * 1.852;

        }


        if (
            Number.isFinite(
                displayWind
            )
        ) {

            setText(
                "wind",
                displayWind.toFixed(1) +
                " km/h"
            );

        }
        else {

            setText(
                "wind",
                "Unavailable"
            );

        }


        setText(

            "weatherCondition",

            result.condition ||

            result.weather_condition ||

            result.description ||

            "--"

        );


        const windDirection =
            wind.direction ||
            wind.direction_text ||
            result.wind_direction ||
            "";


        const currentWindText =
            Number.isFinite(displayWind)

                ?

                `${displayWind.toFixed(1)} km/h${windDirection ? " " + windDirection : ""}`

                :

                "Unavailable";


        setText(
            "windDetails",
            currentWindText
        );


        currentWeatherRisk =
            agent.risk ||
            result.risk ||
            "LOW";


        setText(
            "weatherRisk",
            currentWeatherRisk
        );


        setText(
            "temperatureStatus",
            getTemperatureStatus(
                temperature
            )
        );


        let statusKnots =
            speedKnots;


        if (
            !Number.isFinite(
                statusKnots
            ) &&
            Number.isFinite(
                speedKmh
            )
        ) {

            statusKnots =
                speedKmh / 1.852;

        }


        setText(
            "windStatus",
            getWindStatus(
                statusKnots
            )
        );


        setText(
            "weatherSource",
            agent.source ||
            result.source ||
            "Weather Agent"
        );


    }

    catch(error) {

        console.error(
            "❌ Weather Agent error:",
            error
        );


        setText(
            "temperature",
            "Unavailable"
        );

        setText(
            "wind",
            "Unavailable"
        );

        setText(
            "weatherCondition",
            "Unavailable"
        );

        setText(
            "weatherRisk",
            "--"
        );

        setText(
            "temperatureStatus",
            "--"
        );

        setText(
            "windStatus",
            "--"
        );

        setText(
            "weatherSource",
            "Weather Agent unavailable"
        );

    }

}


/* ============================================================
   TEMPERATURE STATUS
============================================================ */

function getTemperatureStatus(
    temperature
) {

    if (
        !Number.isFinite(
            temperature
        )
    ) {

        return "--";

    }


    if (
        temperature >= 40
    ) {

        return "🔴 Extreme";

    }


    if (
        temperature >= 35
    ) {

        return "🟠 High";

    }


    return "🟢 Normal";

}


/* ============================================================
   WIND STATUS
============================================================ */

function getWindStatus(
    knots
) {

    if (
        !Number.isFinite(
            knots
        )
    ) {

        return "--";

    }


    if (
        knots > 33
    ) {

        return "🔴 Very High";

    }


    if (
        knots > 27
    ) {

        return "🟠 High";

    }


    if (
        knots > 21
    ) {

        return "🟡 Moderate";

    }


    return "🟢 Good";

}


/* ============================================================
   OCEAN AGENT
============================================================ */

async function loadOcean(
    latitude,
    longitude
) {

    try {

        console.log(
            "🌊 Ocean Agent request:",
            latitude,
            longitude
        );


        const data =
            await fetchJSON(

                `/api/ocean?lat=${encodeURIComponent(latitude)}&lon=${encodeURIComponent(longitude)}`

            );


        console.log(
            "🌊 Ocean Agent response:",
            data
        );


        if (
            data.status &&
            data.status !== "success"
        ) {

            throw new Error(
                data.message ||
                "Ocean Agent failed"
            );

        }


        const agent =
            data.data?.agent_result ||
            data.agent_result ||
            data.data ||
            data;


        if (!agent) {

            throw new Error(
                "Ocean Agent result missing"
            );

        }


        const result =
            agent.result ||
            agent;


        const waveHeight =
            Number(
                result.wave_height_m ??
                result.wave_height ??
                result.waveHeight
            );


        if (
            Number.isFinite(
                waveHeight
            )
        ) {

            setText(
                "waveHeight",
                waveHeight.toFixed(2) +
                " m"
            );

        }
        else {

            setText(
                "waveHeight",
                "Unavailable"
            );

        }


        setText(
            "seaState",
            result.sea_state ||
            result.seaState ||
            result.ocean_condition ||
            "--"
        );


        const swellHeight =
            Number(
                result.swell_height_m ??
                result.swell_height
            );


        const swellPeriod =
            Number(
                result.swell_period_s ??
                result.swell_period
            );


        if (
            Number.isFinite(
                swellHeight
            )
        ) {

            let swellText =
                swellHeight.toFixed(2) +
                " m";


            if (
                Number.isFinite(
                    swellPeriod
                )
            ) {

                swellText +=
                    " / " +
                    swellPeriod.toFixed(1) +
                    " s";

            }


            setText(
                "swell",
                swellText
            );

        }
        else {

            setText(
                "swell",
                "Unavailable"
            );

        }


        currentOceanRisk =
            agent.risk ||
            result.risk ||
            "LOW";


        setText(
            "oceanRisk",
            currentOceanRisk
        );


        setText(
            "oceanSource",
            agent.source ||
            result.source ||
            "Ocean Agent"
        );


    }

    catch(error) {

        console.error(
            "❌ Ocean Agent error:",
            error
        );


        setText(
            "waveHeight",
            "Unavailable"
        );

        setText(
            "seaState",
            "Unavailable"
        );

        setText(
            "swell",
            "Unavailable"
        );

        setText(
            "oceanRisk",
            "--"
        );

        setText(
            "oceanSource",
            "Ocean Agent unavailable"
        );

    }

}


/* ============================================================
   GIS AGENT
============================================================ */

async function loadGIS(
    latitude,
    longitude
) {

    try {

        console.log(
            "📍 GIS Agent request:",
            latitude,
            longitude
        );


        const data =
            await fetchJSON(

                `/api/gis?lat=${encodeURIComponent(latitude)}&lon=${encodeURIComponent(longitude)}`

            );


        console.log(
            "📍 GIS Agent response:",
            data
        );


        const areas =
            Array.isArray(
                data.marine_area
            )

                ?

                data.marine_area

                :

                [];


        if (
            areas.length > 0
        ) {

            setText(

                "selectedMarineArea",

                areas
                    .map(
                        area =>
                            area.name
                    )
                    .join(" / ")

            );


            setText(

                "gisInformation",

                areas
                    .map(

                        area =>

                            `${area.name} - ${area.description || ""}`

                    )
                    .join("\n")

            );

        }
        else {

            setText(
                "selectedMarineArea",
                "Not mapped"
            );


            setText(

                "gisInformation",

                data.message ||
                "No mapped marine area."

            );

        }

    }

    catch(error) {

        console.error(
            "❌ GIS Agent error:",
            error
        );


        setText(
            "selectedMarineArea",
            "Unavailable"
        );

        setText(
            "gisInformation",
            "GIS Agent unavailable"
        );

    }

}


/* ============================================================
   LOAD ALL PFZ FISHING REGIONS
============================================================ */

async function loadAllFishingRegions() {

    if (!pfzLayer) {
        return;
    }


    try {

        console.log(
            "🎣 Loading PFZ fishing regions..."
        );


        const data =
            await fetchJSON(
                "/api/fisheries/regions"
            );


        if (
            data.status &&
            data.status !== "success"
        ) {

            throw new Error(
                data.message ||
                "PFZ API failed"
            );

        }


        const regions =
            Array.isArray(
                data.regions
            )

                ?

                data.regions

                :

                [];


        console.log(
            `🎣 ${regions.length} PFZ regions received.`
        );


        setText(
            "pfzCount",
            regions.length +
            " Regions"
        );


        pfzLayer.clearLayers();


        regions.forEach(
            region => {

                const latitude =
                    Number(
                        region.latitude
                    );


                const longitude =
                    Number(
                        region.longitude
                    );


                if (
                    !Number.isFinite(
                        latitude
                    ) ||
                    !Number.isFinite(
                        longitude
                    )
                ) {

                    return;

                }


                const zoneId =
                    region.zone_id ||
                    region.id ||
                    "PFZ";


                const coast =
                    region.coast ||
                    "--";


                const depth =
                    region.depth_m ||
                    "--";


                const direction =
                    region.direction ||
                    "--";


                const marker =
                    L.circleMarker(

                        [
                            latitude,
                            longitude
                        ],

                        {

                            radius: 6,

                            weight: 1,

                            fillOpacity: 0.85

                        }

                    );


                marker.bindPopup(

                    `
                    <div style="min-width:180px;">

                        <b>🎣 ${escapeHTML(zoneId)}</b>

                        <br><br>

                        <b>Coast:</b>
                        ${escapeHTML(coast)}

                        <br>

                        <b>Depth:</b>
                        ${escapeHTML(depth)} m

                        <br>

                        <b>Direction:</b>
                        ${escapeHTML(direction)}

                        <br><br>

                        <button
                            type="button"
                            onclick="
                                selectFishingRegion(
                                    ${latitude},
                                    ${longitude},
                                    '${escapePopup(zoneId)}',
                                    '${escapePopup(coast)}',
                                    '${escapePopup(depth)}'
                                )
                            "
                            style="
                                padding:7px 10px;
                                cursor:pointer;
                                border:none;
                                border-radius:5px;
                            "
                        >
                            🧭 Calculate Route
                        </button>

                    </div>
                    `

                );


                marker.on(
                    "click",
                    () => {

                        selectFishingRegion(

                            latitude,

                            longitude,

                            zoneId,

                            coast,

                            depth

                        );

                    }
                );


                marker.addTo(
                    pfzLayer
                );

            }
        );


    }

    catch(error) {

        console.error(
            "❌ PFZ loading error:",
            error
        );


        setText(
            "pfzCount",
            "Unavailable"
        );

    }

}


/* ============================================================
   ESCAPE HTML
============================================================ */

function escapeHTML(value) {

    return String(value)
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );

}


/* ============================================================
   ESCAPE POPUP STRING
============================================================ */

function escapePopup(value) {

    return String(value)
        .replace(
            /\\/g,
            "\\\\"
        )
        .replace(
            /'/g,
            "\\'"
        );

}


/* ============================================================
   SELECT FISHING REGION
============================================================ */

async function selectFishingRegion(
    latitude,
    longitude,
    zoneId,
    coast,
    depth
) {

    if (
        currentLatitude === null ||
        currentLongitude === null
    ) {

        alert(
            "Waiting for your current GPS location."
        );

        return;

    }


    setText(
        "selectedPFZ",
        zoneId
    );

    setText(
        "pfzDepth",
        depth + " m"
    );

    setText(
        "pfzDistance",
        "Calculating..."
    );

    setText(
        "pfzDirection",
        "Calculating..."
    );

    setHTML(
        "pfzDetails",
        "Calculating distance and route..."
    );


    try {

        const url =

            `/api/fisheries/route` +

            `?current_lat=${encodeURIComponent(currentLatitude)}` +

            `&current_lon=${encodeURIComponent(currentLongitude)}` +

            `&target_lat=${encodeURIComponent(latitude)}` +

            `&target_lon=${encodeURIComponent(longitude)}`;


        console.log(
            "🧭 Fisheries route request:",
            url
        );


        const data =
            await fetchJSON(
                url
            );


        console.log(
            "🧭 Fisheries route response:",
            data
        );


        if (
            data.status &&
            data.status !== "success"
        ) {

            throw new Error(
                data.message ||
                "Route calculation failed"
            );

        }


        const distance =
            Number(
                data.distance_km
            );


        const bearing =
            Number(
                data.bearing_deg
            );


        if (
            !Number.isFinite(
                distance
            )
        ) {

            throw new Error(
                "Distance missing from route response"
            );

        }


        setText(
            "pfzDistance",
            distance.toFixed(2) +
            " km"
        );


        setText(

            "pfzDirection",

            `${data.direction || "--"}${
                Number.isFinite(bearing)
                    ? ` (${bearing.toFixed(0)}°)`
                    : ""
            }`

        );


        drawMarineRoute(

            currentLatitude,

            currentLongitude,

            latitude,

            longitude

        );


        const bounds =
            L.latLngBounds(

                [

                    [
                        currentLatitude,
                        currentLongitude
                    ],

                    [
                        latitude,
                        longitude
                    ]

                ]

            );


        map.fitBounds(

            bounds,

            {

                padding:
                    [
                        50,
                        50
                    ]

            }

        );


        setHTML(

            "pfzDetails",

            `
            <b>🎣 ${escapeHTML(zoneId)}</b>

            <br><br>

            <b>Coast:</b>
            ${escapeHTML(coast)}

            <br>

            <b>Depth:</b>
            ${escapeHTML(depth)} m

            <br>

            <b>Distance from current location:</b>
            ${distance.toFixed(2)} km

            <br>

            <b>Direction:</b>
            ${escapeHTML(data.direction || "--")}

            <br>

            <b>Bearing:</b>
            ${
                Number.isFinite(bearing)
                    ? bearing.toFixed(0) + "°"
                    : "--"
            }

            <br><br>

            🧭 Route displayed on map.
            `

        );


    }

    catch(error) {

        console.error(
            "❌ PFZ route error:",
            error
        );


        const distance =
            calculateDistanceKm(

                currentLatitude,

                currentLongitude,

                latitude,

                longitude

            );


        const bearing =
            calculateBearing(

                currentLatitude,

                currentLongitude,

                latitude,

                longitude

            );


        setText(

            "pfzDistance",

            distance.toFixed(2) +
            " km"

        );


        setText(

            "pfzDirection",

            `${getDirectionFromBearing(bearing)} (${bearing.toFixed(0)}°)`

        );


        drawMarineRoute(

            currentLatitude,

            currentLongitude,

            latitude,

            longitude

        );


        setHTML(

            "pfzDetails",

            `
            <b>🎣 ${escapeHTML(zoneId)}</b>

            <br><br>

            Coast:
            ${escapeHTML(coast)}

            <br>

            Depth:
            ${escapeHTML(depth)} m

            <br>

            Distance:
            ${distance.toFixed(2)} km

            <br>

            Direction:
            ${getDirectionFromBearing(bearing)}

            <br>

            Bearing:
            ${bearing.toFixed(0)}°

            <br><br>

            🧭 Direct marine line displayed.

            <br><br>

            ⚠️ Advanced route API unavailable.
            `

        );

    }

}


/* ============================================================
   DRAW MARINE ROUTE
============================================================ */

function drawMarineRoute(
    startLat,
    startLon,
    endLat,
    endLon
) {

    if (!routeLayer) {
        return;
    }


    routeLayer.clearLayers();


    const line =
        L.polyline(

            [

                [
                    startLat,
                    startLon
                ],

                [
                    endLat,
                    endLon
                ]

            ],

            {

                weight: 4,

                dashArray:
                    "10,8"

            }

        );


    line.bindPopup(
        "🧭 Direct marine route"
    );


    line.addTo(
        routeLayer
    );


    L.marker(

        [
            endLat,
            endLon
        ]

    )

    .bindPopup(
        "🎣 Selected Fishing Region"
    )

    .addTo(
        routeLayer
    );

}


/* ============================================================
   GPS
============================================================ */

function startGPS() {

    if (
        !navigator.geolocation
    ) {

        setText(
            "gpsStatus",
            "● GPS not supported"
        );

        return;

    }


    gpsWatchId =
        navigator.geolocation.watchPosition(

            position => {

                const latitude =
                    Number(
                        position.coords.latitude
                    );


                const longitude =
                    Number(
                        position.coords.longitude
                    );


                const accuracy =
                    Number(
                        position.coords.accuracy
                    );


                if (
                    !Number.isFinite(
                        latitude
                    ) ||
                    !Number.isFinite(
                        longitude
                    )
                ) {

                    return;

                }


                currentLatitude =
                    latitude;

                currentLongitude =
                    longitude;


                currentGPSAccuracy =
                    Number.isFinite(accuracy)
                        ? accuracy
                        : null;


                updateCurrentLocation(

                    latitude,

                    longitude

                );

            },


            error => {

                console.error(
                    "GPS error:",
                    error
                );


                setText(
                    "gpsStatus",
                    "● GPS Unavailable"
                );


                setText(
                    "locationStatus",
                    "GPS unavailable"
                );

            },


            {

                enableHighAccuracy:
                    true,

                maximumAge:
                    10000,

                timeout:
                    15000

            }

        );

}


/* ============================================================
   CURRENT LOCATION
============================================================ */

function updateCurrentLocation(
    latitude,
    longitude
) {

    setText(

        "sidebarCoordinates",

        `${latitude.toFixed(4)}° N, ${longitude.toFixed(4)}° E`

    );


    setText(

        "topCoordinates",

        `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`

    );


    setText(
        "gpsStatus",
        "● GPS Active"
    );


    setText(
        "locationStatus",
        "GPS Active"
    );


    if (!currentMarker) {

        currentMarker =
            L.marker(

                [
                    latitude,
                    longitude
                ]

            )
            .addTo(map);


        currentMarker.bindPopup(
            "📍 Your Current Location"
        );

    }
    else {

        currentMarker.setLatLng(

            [
                latitude,
                longitude
            ]

        );

    }


    if (
        !map._orcaGpsCentered
    ) {

        map.setView(

            [
                latitude,
                longitude
            ],

            9

        );


        map._orcaGpsCentered =
            true;


        loadLocationAgents(

            latitude,

            longitude

        );


        loadVessels(

            latitude,

            longitude

        );

    }

}


/* ============================================================
   MY LOCATION BUTTON
============================================================ */

function connectLocationButton() {

    const button =
        document.getElementById(
            "locateButton"
        );


    if (!button) {
        return;
    }


    button.addEventListener(

        "click",

        () => {

            if (
                currentLatitude === null ||
                currentLongitude === null
            ) {

                alert(
                    "Waiting for GPS..."
                );

                return;

            }


            map.setView(

                [
                    currentLatitude,
                    currentLongitude
                ],

                10

            );


            if (currentMarker) {

                currentMarker.openPopup();

            }


            loadLocationAgents(

                currentLatitude,

                currentLongitude

            );


            loadVessels(

                currentLatitude,

                currentLongitude

            );

        }

    );

}


/* ============================================================
   FULLSCREEN
============================================================ */

function connectFullscreenButton() {

    const button =
        document.getElementById(
            "fullscreenButton"
        );


    if (!button) {
        return;
    }


    button.addEventListener(

        "click",

        () => {

            const mapElement =
                document.getElementById(
                    "map"
                );


            if (!mapElement) {
                return;
            }


            if (
                document.fullscreenElement
            ) {

                document.exitFullscreen();

            }
            else if (
                mapElement.requestFullscreen
            ) {

                mapElement.requestFullscreen();

            }

        }

    );

}


/* ============================================================
   REFRESH VESSELS BUTTON
============================================================ */

function connectVesselRefreshButton() {

    const button =
        document.getElementById(
            "refreshVessels"
        );


    if (!button) {

        console.warn(
            "ORCA: #refreshVessels button not found."
        );

        return;

    }


    button.addEventListener(

        "click",

        async () => {

            if (
                currentLatitude === null ||
                currentLongitude === null
            ) {

                alert(
                    "Waiting for GPS..."
                );

                return;

            }


            const originalText =
                button.textContent;


            button.disabled =
                true;


            button.textContent =
                "🔄 Loading...";


            try {

                await loadVessels(

                    currentLatitude,

                    currentLongitude

                );

            }

           finally {

    if (sendButton) {

        if (activeSosId) {

            sendButton.disabled = true;
            sendButton.textContent = "🚨 SOS ACTIVE";

        }
        else {

            sendButton.disabled = false;
            sendButton.textContent = "🚨 SEND SOS";

        }

    }

}

        }

    );

}


/* ============================================================
   VESSEL AGENT
============================================================ */

async function loadVessels(
    latitude,
    longitude
) {

    try {

        console.log(
            "🚢 Vessel Agent request:",
            latitude,
            longitude
        );


        setText(
            "vesselCount",
            "Loading..."
        );


        const data =
            await fetchJSON(

                `/api/vessel?lat=${encodeURIComponent(latitude)}&lon=${encodeURIComponent(longitude)}`

            );


        console.log(
            "🚢 Vessel Agent response:",
            data
        );


        if (
            data.status &&
            data.status !== "success"
        ) {

            throw new Error(
                data.message ||
                "Vessel Agent failed"
            );

        }


        const agent =
            data.data?.agent_result ||
            data.agent_result ||
            data.data ||
            data;


        const result =
            agent.result ||
            agent;


        const vessels =
            result.vessels ||

            result.nearby_vessels ||

            result.vessel_list ||

            [];


        setText(

            "vesselCount",

            result.nearby_vessels_count ??

            result.vessel_count ??

            result.count ??

            vessels.length

        );


        setText(

            "trafficDensity",

            result.traffic_density ||

            result.density ||

            "--"

        );


        const closestDistance =
            Number(

                result.closest_vessel_distance_km ??

                result.closest_distance_km

            );


        if (
            Number.isFinite(
                closestDistance
            )
        ) {

            setText(

                "closestVessel",

                closestDistance.toFixed(2) +
                " km"

            );

        }
        else {

            setText(
                "closestVessel",
                "--"
            );

        }


        currentVesselRisk =

            agent.risk ||

            result.risk ||

            "LOW";


        setText(
            "vesselRisk",
            currentVesselRisk
        );


        if (vesselLayer) {

            vesselLayer.clearLayers();

        }


        vessels.forEach(

            vessel => {

                const lat =
                    Number(

                        vessel.latitude ??

                        vessel.lat ??

                        vessel.position?.latitude

                    );


                const lon =
                    Number(

                        vessel.longitude ??

                        vessel.lon ??

                        vessel.position?.longitude

                    );


                if (
                    !Number.isFinite(lat) ||
                    !Number.isFinite(lon)
                ) {

                    return;

                }


                const vesselName =

                    vessel.name ||

                    vessel.vessel_name ||

                    vessel.mmsi ||

                    "Vessel";


                const marker =
                    L.circleMarker(

                        [
                            lat,
                            lon
                        ],

                        {

                            radius: 6,

                            weight: 1,

                            fillOpacity: 0.9

                        }

                    );


                marker.bindPopup(

                    `
                    <div>

                        <b>🚢 ${escapeHTML(vesselName)}</b>

                        <br><br>

                        Latitude:
                        ${lat.toFixed(5)}

                        <br>

                        Longitude:
                        ${lon.toFixed(5)}

                        ${
                            vessel.speed_knots != null

                                ?

                                `<br>Speed: ${escapeHTML(vessel.speed_knots)} knots`

                                :

                                ""
                        }

                        ${
                            vessel.course_deg != null

                                ?

                                `<br>Course: ${escapeHTML(vessel.course_deg)}°`

                                :

                                ""
                        }

                    </div>
                    `

                );


                marker.addTo(
                    vesselLayer
                );

            }

        );


        updateSafetyMessage();


        console.log(
            `🚢 Vessel Agent updated: ${vessels.length} vessels`
        );


    }

    catch(error) {

        console.error(
            "❌ Vessel Agent error:",
            error
        );


        setText(
            "vesselCount",
            "Unavailable"
        );

        setText(
            "trafficDensity",
            "--"
        );

        setText(
            "closestVessel",
            "--"
        );

        setText(
            "vesselRisk",
            "--"
        );

    }

}


/* ============================================================
   SAFETY MESSAGE
============================================================ */

function updateSafetyMessage() {

    const risks = [

        currentWeatherRisk,

        currentOceanRisk,

        currentVesselRisk

    ]

    .filter(
        Boolean
    )

    .map(

        risk =>

            String(
                risk
            ).toUpperCase()

    );


    if (
        !risks.length
    ) {

        setText(

            "safetyMessage",

            "Select a marine location to view live conditions."

        );

        return;

    }


    if (
        risks.includes(
            "CRITICAL"
        )
    ) {

        setText(

            "safetyMessage",

            "🔴 CRITICAL marine risk detected. Check live agent warnings before sailing."

        );

        return;

    }


    if (
        risks.includes(
            "HIGH"
        )
    ) {

        setText(

            "safetyMessage",

            "🟠 HIGH marine risk detected. Exercise extreme caution."

        );

        return;

    }


    if (

        risks.includes(
            "MEDIUM"
        )

        ||

        risks.includes(
            "MODERATE"
        )

    ) {

        setText(

            "safetyMessage",

            "🟡 Moderate marine risk. Check current conditions before sailing."

        );

        return;

    }


    setText(

        "safetyMessage",

        "🟢 Current agent results indicate low risk."

    );

}


/* ============================================================
   HAVERSINE DISTANCE
============================================================ */

function calculateDistanceKm(
    lat1,
    lon1,
    lat2,
    lon2
) {

    const earthRadius =
        6371;


    const dLat =
        toRadians(
            lat2 - lat1
        );


    const dLon =
        toRadians(
            lon2 - lon1
        );


    const a =

        Math.sin(
            dLat / 2
        ) ** 2

        +

        Math.cos(
            toRadians(lat1)
        )

        *

        Math.cos(
            toRadians(lat2)
        )

        *

        Math.sin(
            dLon / 2
        ) ** 2;


    const c =

        2 *

        Math.atan2(

            Math.sqrt(a),

            Math.sqrt(
                1 - a
            )

        );


    return earthRadius * c;

}


/* ============================================================
   BEARING
============================================================ */

function calculateBearing(
    lat1,
    lon1,
    lat2,
    lon2
) {

    const startLat =
        toRadians(lat1);


    const endLat =
        toRadians(lat2);


    const dLon =
        toRadians(
            lon2 - lon1
        );


    const y =
        Math.sin(
            dLon
        ) *

        Math.cos(
            endLat
        );


    const x =

        Math.cos(
            startLat
        )

        *

        Math.sin(
            endLat
        )

        -

        Math.sin(
            startLat
        )

        *

        Math.cos(
            endLat
        )

        *

        Math.cos(
            dLon
        );


    let bearing =

        Math.atan2(
            y,
            x
        );


    bearing =
        toDegrees(
            bearing
        );


    return (
        bearing + 360
    ) % 360;

}


/* ============================================================
   DIRECTION FROM BEARING
============================================================ */

function getDirectionFromBearing(
    bearing
) {

    const directions = [

        "N",
        "NE",
        "E",
        "SE",
        "S",
        "SW",
        "W",
        "NW"

    ];


    const index =
        Math.round(
            bearing / 45
        ) % 8;


    return directions[index];

}


/* ============================================================
   DEGREE CONVERSION
============================================================ */

function toRadians(
    degrees
) {

    return degrees *
        Math.PI /
        180;

}


function toDegrees(
    radians
) {

    return radians *
        180 /
        Math.PI;

}


/* ============================================================
   NAVIGATION
============================================================ */

function initializeNavigation() {

    document
        .querySelectorAll(
            ".nav-item[data-section]"
        )
        .forEach(

            button => {

                button.addEventListener(

                    "click",

                    () => {

                        const sectionId =
                            button.dataset.section;


                        const section =
                            document.getElementById(
                                sectionId
                            );


                        if (section) {

                            section.scrollIntoView(

                                {

                                    behavior:
                                        "smooth",

                                    block:
                                        "start"

                                }

                            );

                        }


                        document
                            .querySelectorAll(
                                ".nav-item"
                            )
                            .forEach(

                                item =>

                                    item.classList.remove(
                                        "active"
                                    )

                            );


                        button.classList.add(
                            "active"
                        );


                        closeMobileMenu();

                    }

                );

            }

        );

}


/* ============================================================
   MOBILE MENU
============================================================ */

function initializeMobileMenu() {

    const menuButton =
        document.getElementById(
            "menuButton"
        );


    const sidebar =
        document.getElementById(
            "sidebar"
        );


    const backdrop =
        document.getElementById(
            "mobileBackdrop"
        );


    if (
        menuButton &&
        sidebar &&
        backdrop
    ) {

        menuButton.addEventListener(

            "click",

            () => {

                sidebar.classList.toggle(
                    "open"
                );


                backdrop.classList.toggle(
                    "show"
                );

            }

        );


        backdrop.addEventListener(

            "click",

            closeMobileMenu

        );

    }

}


/* ============================================================
   CLOSE MOBILE MENU
============================================================ */

function closeMobileMenu() {

    const sidebar =
        document.getElementById(
            "sidebar"
        );


    const backdrop =
        document.getElementById(
            "mobileBackdrop"
        );


    if (sidebar) {

        sidebar.classList.remove(
            "open"
        );

    }


    if (backdrop) {

        backdrop.classList.remove(
            "show"
        );

    }

}


/* ============================================================
   SOS SYSTEM
============================================================ */


/* ============================================================
   INITIALIZE SOS
============================================================ */

function initializeSOS() {

    const button =
        document.getElementById(
            "sosButton"
        );


    const sendButton =
        document.getElementById(
            "sendSosButton"
        );


    const cancelButton =
        document.getElementById(
            "cancelSosButton"
        );


    /*
       Sidebar SOS button.

       IMPORTANT:
       It does NOT redirect to /sos.

       It opens the SOS section already
       present on the fisherman dashboard.
    */

    if (button) {

        button.addEventListener(

            "click",

            function() {

                const panel =
                    document.getElementById(
                        "sosPanel"
                    );


                if (panel) {

                    panel.scrollIntoView({

                        behavior:
                            "smooth",

                        block:
                            "center"

                    });

                }
                else {

                    /*
                       If there is no SOS panel,
                       directly start SOS.
                    */

                    sendSOS();

                }

            }

        );

    }


    /*
       SEND SOS button
    */

    if (sendButton) {

        sendButton.addEventListener(

            "click",

            sendSOS

        );

    }


    /*
       CANCEL SOS button
    */

    if (cancelButton) {

        cancelButton.addEventListener(

            "click",

            cancelSOS

        );

    }


    /*
       Restore active SOS after page refresh
       if an SOS ID was saved.
    */

    const savedSosId =
        localStorage.getItem(
            "orca_active_sos_id"
        );


    if (savedSosId) {

        activeSosId =
            savedSosId;


        updateSOSUI(

            activeSosId,

            "SOS_ACTIVE",

            "🚨 SOS is still active."

        );


        startSOSLocationTracking();

    }

}


/* ============================================================
   SEND SOS
============================================================ */

async function sendSOS() {

    if (activeSosId) {

        alert(
            "An SOS is already active."
        );

        return;

    }


    /*
       Check GPS
    */

    if (
        currentLatitude === null ||
        currentLongitude === null
    ) {

        alert(
            "Waiting for GPS location. Please enable GPS and try again."
        );

        return;

    }


    /*
       Confirmation
    */

    const confirmed =
        confirm(

            "🚨 SEND EMERGENCY SOS?\n\n" +

            "Your current GPS location will be sent to the Rescue Team."

        );


    if (!confirmed) {

        return;

    }


    /*
       Emergency type
    */

    const emergencyTypeElement =
        document.getElementById(
            "emergencyType"
        );


    const emergencyType =
        emergencyTypeElement
            ? emergencyTypeElement.value
            : "Other";


    /*
       Send button
    */

    const sendButton =
        document.getElementById(
            "sendSosButton"
        );


    if (sendButton) {

        sendButton.disabled =
            true;

        sendButton.textContent =
            "📡 Sending SOS...";

    }


    try {

        /*
           Make sure we have the latest GPS
           position before creating SOS.
        */

        let latitude =
            currentLatitude;

        let longitude =
            currentLongitude;

        let accuracy =
            currentGPSAccuracy;


        if (
            navigator.geolocation
        ) {

            try {

                const position =
                    await new Promise(

                        function(resolve, reject) {

                            navigator.geolocation.getCurrentPosition(

                                resolve,

                                reject,

                                {

                                    enableHighAccuracy:
                                        true,

                                    maximumAge:
                                        5000,

                                    timeout:
                                        10000

                                }

                            );

                        }

                    );


                latitude =
                    position.coords.latitude;

                longitude =
                    position.coords.longitude;

                accuracy =
                    position.coords.accuracy;


                /*
                   Update global GPS values
                */

                currentLatitude =
                    latitude;

                currentLongitude =
                    longitude;

                currentGPSAccuracy =
                    accuracy;


                /*
                   Update dashboard marker
                */

                updateCurrentLocation(

                    latitude,

                    longitude

                );

            }

            catch (gpsError) {

                console.warn(
                    "Latest GPS unavailable. Using existing GPS position.",
                    gpsError
                );

            }

        }


        /*
           Final GPS validation
        */

        if (
            !Number.isFinite(
                Number(latitude)
            ) ||
            !Number.isFinite(
                Number(longitude)
            )
        ) {

            throw new Error(
                "Valid GPS location is not available."
            );

        }


        /*
           Create SOS
        */

        const response =
            await fetch(

                "/api/sos/create",

                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    credentials:
                        "same-origin",

                    body:
                        JSON.stringify({

                            latitude:
                                Number(latitude),

                            longitude:
                                Number(longitude),

                            accuracy:
                                Number.isFinite(
                                    Number(accuracy)
                                )
                                    ? Number(accuracy)
                                    : null,

                            emergency_type:
                                emergencyType

                        })

                }

            );


        let data = null;


        try {

            data =
                await response.json();

        }

        catch (jsonError) {

            throw new Error(
                `Invalid SOS server response. HTTP ${response.status}`
            );

        }


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(

                data.message ||
                data.error ||
                "Unable to create SOS"

            );

        }


        /*
           Get SOS ID
        */

        const newSosId =

            data.sos_id ||

            data.id ||

            data.sos?.sos_id;


        if (!newSosId) {

            throw new Error(
                "SOS was created but no SOS ID was returned."
            );

        }


        /*
           Store active SOS
        */

        activeSosId =
            String(newSosId);


        /*
           Save so it survives refresh
        */

        localStorage.setItem(

            "orca_active_sos_id",

            activeSosId

        );


        /*
           Update SOS UI
        */

        updateSOSUI(

            activeSosId,

            data.status ||
                "SOS_ACTIVE",

            "🚨 SOS ACTIVE. Rescue Team has been notified."

        );


        /*
           Start continuous GPS tracking
        */

        startSOSLocationTracking();


        /*
           Also send the latest location immediately
        */

        await updateSOSLocation(

            latitude,

            longitude,

            accuracy

        );


        console.log(
            "🚨 SOS CREATED:",
            activeSosId
        );


    }

    catch (error) {

        console.error(
            "SOS creation error:",
            error
        );


        updateSOSMessage(

            "❌ SOS failed: " +
            error.message

        );

    }

    finally {

        if (sendButton) {

            sendButton.disabled =
                false;


            if (!activeSosId) {

                sendButton.textContent =
                    "🚨 SEND SOS";

            }

        }

    }

}


/* ============================================================
   START SOS LOCATION TRACKING
============================================================ */

function startSOSLocationTracking() {

    /*
       Stop old watcher
    */

    if (
        sosLocationWatchId !== null
    ) {

        navigator.geolocation.clearWatch(

            sosLocationWatchId

        );

        sosLocationWatchId =
            null;

    }


    if (
        !navigator.geolocation ||
        !activeSosId
    ) {

        return;

    }


    sosLocationWatchId =

        navigator.geolocation.watchPosition(

            function(position) {

                if (!activeSosId) {

                    return;

                }


                const latitude =
                    Number(
                        position.coords.latitude
                    );


                const longitude =
                    Number(
                        position.coords.longitude
                    );


                const accuracy =
                    Number(
                        position.coords.accuracy
                    );


                if (
                    !Number.isFinite(latitude) ||
                    !Number.isFinite(longitude)
                ) {

                    return;

                }


                /*
                   Update normal dashboard GPS
                */

                currentLatitude =
                    latitude;

                currentLongitude =
                    longitude;

                currentGPSAccuracy =
                    accuracy;


                /*
                   Send SOS location to backend
                */

                updateSOSLocation(

                    latitude,

                    longitude,

                    accuracy

                );

            },


            function(error) {

                console.error(

                    "SOS GPS tracking error:",

                    error

                );

            },


            {

                enableHighAccuracy:
                    true,

                maximumAge:
                    5000,

                timeout:
                    15000

            }

        );

}


/* ============================================================
   UPDATE SOS LOCATION
============================================================ */

async function updateSOSLocation(

    latitude,

    longitude,

    accuracy

) {

    if (!activeSosId) {

        return;

    }


    try {

        const response =
            await fetch(

                `/api/sos/${encodeURIComponent(activeSosId)}/location`,

                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    credentials:
                        "same-origin",

                    body:
                        JSON.stringify({

                            latitude:
                                Number(latitude),

                            longitude:
                                Number(longitude),

                            accuracy:
                                Number(accuracy)

                        })

                }

            );


        if (!response.ok) {

            console.warn(

                "SOS location update failed:",
                response.status

            );

            return;

        }


        /*
           Update SOS location UI
        */

        setText(

            "sosLatitude",

            Number(latitude).toFixed(6)

        );


        setText(

            "sosLongitude",

            Number(longitude).toFixed(6)

        );


        console.log(

            "📍 SOS location updated:",

            activeSosId,

            latitude,

            longitude

        );

    }

    catch (error) {

        console.error(

            "SOS location update error:",

            error

        );

    }

}


/* ============================================================
   CANCEL SOS
============================================================ */

async function cancelSOS() {

    if (!activeSosId) {

        return;

    }


    const confirmed =
        confirm(

            "Cancel the active SOS?"

        );


    if (!confirmed) {

        return;

    }


    const sosIdToCancel =
        activeSosId;


    try {

        const response =
            await fetch(

                `/api/sos/${encodeURIComponent(sosIdToCancel)}/status`,

                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    credentials:
                        "same-origin",

                    body:
                        JSON.stringify({

                            status:
                                "SOS_CANCELLED"

                        })

                }

            );


        let data = null;


        try {

            data =
                await response.json();

        }

        catch (jsonError) {

            data = {};

        }


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(

                data.message ||
                data.error ||
                "Unable to cancel SOS"

            );

        }


        /*
           Stop GPS SOS tracking
        */

        stopSOSLocationTracking();


        /*
           Clear active SOS
        */

        activeSosId =
            null;


        localStorage.removeItem(

            "orca_active_sos_id"

        );


        /*
           Update UI
        */

        updateSOSUI(

            null,

            "SOS_CANCELLED",

            "🟢 SOS cancelled successfully."

        );


        console.log(
            "🟢 SOS cancelled:",
            sosIdToCancel
        );

    }

    catch (error) {

        console.error(

            "SOS cancellation error:",

            error

        );


        updateSOSMessage(

            "❌ Unable to cancel SOS: " +
            error.message

        );

    }

}


/* ============================================================
   STOP SOS GPS TRACKING
============================================================ */

function stopSOSLocationTracking() {

    if (
        sosLocationWatchId !== null
    ) {

        navigator.geolocation.clearWatch(

            sosLocationWatchId

        );

        sosLocationWatchId =
            null;

    }

}


/* ============================================================
   UPDATE SOS UI
============================================================ */

function updateSOSUI(

    sosId,

    status,

    message

) {

    setText(

        "sosId",

        sosId || "--"

    );


    setText(

        "sosStatus",

        status || "No active SOS"

    );


    setText(

        "sosLatitude",

        currentLatitude !== null

            ?

            currentLatitude.toFixed(6)

            :

            "--"

    );


    setText(

        "sosLongitude",

        currentLongitude !== null

            ?

            currentLongitude.toFixed(6)

            :

            "--"

    );


    updateSOSMessage(
        message
    );


    const sendButton =
        document.getElementById(
            "sendSosButton"
        );


    const cancelButton =
        document.getElementById(
            "cancelSosButton"
        );


    const panel =
        document.getElementById(
            "sosPanel"
        );


    if (activeSosId) {

        if (sendButton) {

            sendButton.disabled =
                true;

            sendButton.textContent =
                "🚨 SOS ACTIVE";

        }


        if (cancelButton) {

            cancelButton.style.display =
                "inline-block";

        }


        if (panel) {

            panel.classList.add(
                "sos-active"
            );

        }

    }

    else {

        if (sendButton) {

            sendButton.disabled =
                false;

            sendButton.textContent =
                "🚨 SEND SOS";

        }


        if (cancelButton) {

            cancelButton.style.display =
                "none";

        }


        if (panel) {

            panel.classList.remove(
                "sos-active"
            );

        }

    }

}


/* ============================================================
   SOS MESSAGE
============================================================ */

function updateSOSMessage(
    message
) {

    setText(

        "sosMessage",

        message ||

        "SOS is ready."

    );

}


/* ============================================================
   LOGOUT
============================================================ */

function initializeLogout() {

    const button =
        document.getElementById(
            "logoutButton"
        );


    if (!button) {
        return;
    }


    button.addEventListener(

        "click",

        async () => {

            try {

                await fetch(

                    "/logout",

                    {

                        method:
                            "GET",

                        credentials:
                            "same-origin"

                    }

                );

            }

            catch(error) {

                console.error(
                    "Logout error:",
                    error
                );

            }


            window.location.href =
                "/";

        }

    );

}


/* ============================================================
   WINDOW RESIZE
============================================================ */

function initializeResponsiveMap() {

    window.addEventListener(

        "resize",

        () => {

            if (map) {

                setTimeout(

                    () => {

                        map.invalidateSize();

                    },

                    200

                );

            }

        }

    );

}


/* ============================================================
   INITIALIZE EVERYTHING
============================================================ */

function initializeDashboard() {

    console.log(
        "🚀 ORCA Fisherman Dashboard starting..."
    );


    /* ========================================================
       MAP
    ======================================================== */

    initializeMap();


    /* ========================================================
       GPS
    ======================================================== */

    startGPS();


    /* ========================================================
       BUTTONS
    ======================================================== */

    connectClearButtons();

    connectLocationButton();

    connectFullscreenButton();

    connectVesselRefreshButton();


    /* ========================================================
       NAVIGATION
    ======================================================== */

    initializeNavigation();


    /* ========================================================
       MOBILE MENU
    ======================================================== */

    initializeMobileMenu();


    /* ========================================================
       SOS
    ======================================================== */

    initializeSOS();


    /* ========================================================
       LOGOUT
    ======================================================== */

    initializeLogout();


    /* ========================================================
       RESPONSIVE MAP
    ======================================================== */

    initializeResponsiveMap();


    console.log(
        "✅ ORCA Fisherman Dashboard ready."
    );

}


/* ============================================================
   START AFTER HTML LOAD
============================================================ */

if (
    document.readyState === "loading"
) {

    document.addEventListener(
        "DOMContentLoaded",
        initializeDashboard
    );

}
else {

    initializeDashboard();

}

// ============================================================
// MARINE SAFETY
// ============================================================

let previousMarineRisk = null;

let marineSafetyRequestRunning = false;

let marineSafetyInterval = null;


// ============================================================
// SAFE VALUE
// ============================================================

function getMarineSafetyStatus(value) {

    if (
        value === null ||
        value === undefined ||
        value === "" ||
        String(value).toLowerCase() === "nan" ||
        String(value).toLowerCase() === "undefined"
    ) {
        return "UNKNOWN";
    }

    return String(value);

}


// ============================================================
// LOAD MARINE SAFETY
// ============================================================

async function loadMarineSafety() {

    // --------------------------------------------------------
    // WAIT FOR GPS
    // --------------------------------------------------------

    if (
        typeof currentLatitude === "undefined" ||
        typeof currentLongitude === "undefined"
    ) {

        console.log(
            "🌊 Marine Safety: GPS variables not available yet."
        );

        return;

    }


    if (
        currentLatitude === null ||
        currentLongitude === null ||
        currentLatitude === undefined ||
        currentLongitude === undefined
    ) {

        console.log(
            "🌊 Marine Safety: Waiting for GPS..."
        );

        return;

    }


    // --------------------------------------------------------
    // VALIDATE GPS
    // --------------------------------------------------------

    const latitude =
        Number(currentLatitude);

    const longitude =
        Number(currentLongitude);


    if (
        !Number.isFinite(latitude) ||
        !Number.isFinite(longitude)
    ) {

        console.log(
            "🌊 Marine Safety: Invalid GPS coordinates."
        );

        return;

    }


    // --------------------------------------------------------
    // PREVENT OVERLAPPING REQUESTS
    // --------------------------------------------------------

    if (marineSafetyRequestRunning) {

        console.log(
            "🌊 Marine Safety: Previous request still running."
        );

        return;

    }


    marineSafetyRequestRunning = true;


    try {

        // ----------------------------------------------------
        // API URL
        // ----------------------------------------------------

        const url =
            `/api/marine-safety` +
            `?lat=${encodeURIComponent(latitude)}` +
            `&lon=${encodeURIComponent(longitude)}`;


        console.log(
            "🌊 Marine Safety URL:",
            url
        );


        // ----------------------------------------------------
        // REQUEST
        // ----------------------------------------------------

        const response =
            await fetch(
                url,
                {
                    method: "GET",
                    cache: "no-store",
                    credentials: "same-origin"
                }
            );


        // ----------------------------------------------------
        // READ RESPONSE AS TEXT
        //
        // This protects the frontend if the backend contains
        // NaN / Infinity values in ocean data.
        // ----------------------------------------------------

        const responseText =
            await response.text();


        let data = null;


        try {

            const cleanedResponse =
                responseText
                    .replace(
                        /\bNaN\b/g,
                        "null"
                    )
                    .replace(
                        /\bInfinity\b/g,
                        "null"
                    )
                    .replace(
                        /\b-Infinity\b/g,
                        "null"
                    );


            data =
                JSON.parse(
                    cleanedResponse
                );

        }

        catch (jsonError) {

            console.error(
                "❌ Marine Safety invalid JSON response:",
                jsonError,
                responseText
            );

            updateMarineSafetyUnavailable();

            return;

        }


        console.log(
            "🌊 Marine Safety Data:",
            data
        );


        // ----------------------------------------------------
        // API ERROR
        // ----------------------------------------------------

        if (
            !response.ok ||
            !data ||
            data.success !== true
        ) {

            console.error(
                "❌ Marine Safety API error:",
                data
            );

            updateMarineSafetyUnavailable();

            return;

        }


        // ----------------------------------------------------
        // UPDATE UI
        // ----------------------------------------------------

        updateMarineSafetyUI(
            data
        );


        // ----------------------------------------------------
        // SAFETY ALERT
        // ----------------------------------------------------

        checkMarineSafetyAlert(
            data
        );

    }


    catch (error) {

        console.error(
            "❌ Marine safety request failed:",
            error
        );


        updateMarineSafetyUnavailable();

    }


    finally {

        marineSafetyRequestRunning =
            false;

    }

}


// ============================================================
// UPDATE MARINE SAFETY UI
// ============================================================

function updateMarineSafetyUI(data) {

    if (
        !data ||
        !data.success
    ) {

        updateMarineSafetyUnavailable();

        return;

    }


    // ========================================================
    // OVERALL RISK
    // ========================================================

    const risk =
        getMarineSafetyStatus(
            data.risk
        );


    const overallRisk =
        document.getElementById(
            "overallRisk"
        );


    const riskIcon =
        document.getElementById(
            "overallRiskIcon"
        );


    if (overallRisk) {

        overallRisk.textContent =
            risk;

    }


    if (riskIcon) {

        if (risk === "HIGH") {

            riskIcon.textContent =
                "🔴";

        }

        else if (
            risk === "MODERATE"
        ) {

            riskIcon.textContent =
                "🟡";

        }

        else if (
            risk === "UNKNOWN"
        ) {

            riskIcon.textContent =
                "⚪";

        }

        else if (
            risk === "LOW"
        ) {

            riskIcon.textContent =
                "🟢";

        }

        else {

            riskIcon.textContent =
                "⚪";

        }

    }


    // ========================================================
    // HAZARDS
    // ========================================================

    const hazards =
        data.hazards || {};


    const cyclone =
        document.getElementById(
            "cycloneStatus"
        );


    const lightning =
        document.getElementById(
            "lightningStatus"
        );


    const wave =
        document.getElementById(
            "waveStatus"
        );


    const wind =
        document.getElementById(
            "windStatus"
        );


    // --------------------------------------------------------
    // CYCLONE
    // --------------------------------------------------------

    if (cyclone) {

        cyclone.textContent =
            getMarineSafetyStatus(
                hazards.cyclone?.status
            );

    }


    // --------------------------------------------------------
    // LIGHTNING
    // --------------------------------------------------------

    if (lightning) {

        lightning.textContent =
            getMarineSafetyStatus(
                hazards.lightning?.status
            );

    }


    // --------------------------------------------------------
    // WAVES
    // --------------------------------------------------------

    if (wave) {

        wave.textContent =
            getMarineSafetyStatus(
                hazards.wave?.status
            );

    }


    // --------------------------------------------------------
    // WIND
    // --------------------------------------------------------

    if (wind) {

        wind.textContent =
            getMarineSafetyStatus(
                hazards.wind?.status
            );

    }


    // ========================================================
    // GEOFENCE
    // ========================================================

    const geofence =
        data.geofence || {};


    const boundary =
        document.getElementById(
            "boundaryStatus"
        );


    const protectedArea =
        document.getElementById(
            "protectedStatus"
        );


    const restrictedArea =
        document.getElementById(
            "restrictedStatus"
        );


    // --------------------------------------------------------
    // INTERNATIONAL BOUNDARY
    // --------------------------------------------------------

    if (boundary) {

        boundary.textContent =
            getMarineSafetyStatus(
                geofence
                    .international_boundary
                    ?.status
            );

    }


    // --------------------------------------------------------
    // PROTECTED AREA
    // --------------------------------------------------------

    if (protectedArea) {

        protectedArea.textContent =
            getMarineSafetyStatus(
                geofence
                    .protected_area
                    ?.status
            );

    }


    // --------------------------------------------------------
    // RESTRICTED AREA
    // --------------------------------------------------------

    if (restrictedArea) {

        restrictedArea.textContent =
            getMarineSafetyStatus(
                geofence
                    .restricted_area
                    ?.status
            );

    }


    // ========================================================
    // RECOMMENDATION
    // ========================================================

    const recommendation =
        document.getElementById(
            "safetyRecommendation"
        );


    if (recommendation) {

        if (
            data.recommendation &&
            String(data.recommendation).trim() !== ""
        ) {

            recommendation.textContent =
                data.recommendation;

        }

        else {

            recommendation.textContent =
                "Marine safety recommendation unavailable.";

        }

    }


    // ========================================================
    // LAST UPDATED
    // ========================================================

    const updated =
        document.getElementById(
            "safetyLastUpdated"
        );


    if (updated) {

        updated.textContent =
            "Updated: " +
            new Date().toLocaleTimeString();

    }


    console.log(
        "✅ Marine Safety UI updated using GPS:",
        latitudeForLog(),
        longitudeForLog()
    );

}


// ============================================================
// GPS VALUES FOR LOGGING
// ============================================================

function latitudeForLog() {

    if (
        typeof currentLatitude !== "undefined" &&
        currentLatitude !== null
    ) {

        return currentLatitude;

    }

    return "UNKNOWN";

}


function longitudeForLog() {

    if (
        typeof currentLongitude !== "undefined" &&
        currentLongitude !== null
    ) {

        return currentLongitude;

    }

    return "UNKNOWN";

}


// ============================================================
// MARINE SAFETY UNAVAILABLE
// ============================================================

function updateMarineSafetyUnavailable() {

    // --------------------------------------------------------
    // OVERALL RISK
    // --------------------------------------------------------

    const overallRisk =
        document.getElementById(
            "overallRisk"
        );


    const riskIcon =
        document.getElementById(
            "overallRiskIcon"
        );


    if (overallRisk) {

        overallRisk.textContent =
            "UNKNOWN";

    }


    if (riskIcon) {

        riskIcon.textContent =
            "⚪";

    }


    // --------------------------------------------------------
    // HAZARDS
    // --------------------------------------------------------

    setMarineSafetyUnknown(
        "cycloneStatus"
    );


    setMarineSafetyUnknown(
        "lightningStatus"
    );


    setMarineSafetyUnknown(
        "waveStatus"
    );


    setMarineSafetyUnknown(
        "windStatus"
    );


    // --------------------------------------------------------
    // GEOFENCE
    // --------------------------------------------------------

    setMarineSafetyUnknown(
        "boundaryStatus"
    );


    setMarineSafetyUnknown(
        "protectedStatus"
    );


    setMarineSafetyUnknown(
        "restrictedStatus"
    );


    // --------------------------------------------------------
    // RECOMMENDATION
    // --------------------------------------------------------

    const recommendation =
        document.getElementById(
            "safetyRecommendation"
        );


    if (recommendation) {

        recommendation.textContent =
            "Marine safety data is currently unavailable.";

    }


    // --------------------------------------------------------
    // TIME
    // --------------------------------------------------------

    const updated =
        document.getElementById(
            "safetyLastUpdated"
        );


    if (updated) {

        updated.textContent =
            "Waiting for marine safety data...";

    }

}


// ============================================================
// SET MARINE SAFETY UNKNOWN
// ============================================================

function setMarineSafetyUnknown(id) {

    const element =
        document.getElementById(id);


    if (element) {

        element.textContent =
            "UNKNOWN";

    }

}


// ============================================================
// AUTOMATIC SAFETY ALERT
// ============================================================

function checkMarineSafetyAlert(data) {

    if (
        !data ||
        !data.success
    ) {

        return;

    }


    const risk =
        getMarineSafetyStatus(
            data.risk
        );


    // --------------------------------------------------------
    // Only notify when risk changes to HIGH
    // --------------------------------------------------------

    if (
        risk === "HIGH" &&
        previousMarineRisk !== "HIGH"
    ) {

        showMarineSafetyNotification(
            data.recommendation ||
            "High marine risk detected."
        );

    }


    previousMarineRisk =
        risk;

}


// ============================================================
// ALERT
// ============================================================

function showMarineSafetyNotification(message) {

    console.warn(
        "🚨 MARINE SAFETY ALERT:",
        message
    );


    // --------------------------------------------------------
    // Browser notification
    // --------------------------------------------------------

    if (
        "Notification" in window &&
        Notification.permission === "granted"
    ) {

        new Notification(
            "🚨 ORCA Marine Safety Alert",
            {
                body:
                    String(message)
            }
        );

    }

}


// ============================================================
// START MARINE SAFETY MONITORING
// ============================================================

function initializeMarineSafety() {

    console.log(
        "🌊 Marine Safety Monitoring Started"
    );


    // --------------------------------------------------------
    // Initial attempt
    // --------------------------------------------------------

    loadMarineSafety();


    // --------------------------------------------------------
    // Prevent duplicate intervals
    // --------------------------------------------------------

    if (marineSafetyInterval !== null) {

        return;

    }


    // --------------------------------------------------------
    // Refresh every 10 seconds
    //
    // The function itself checks whether GPS is available.
    // Therefore it is safe to start this before GPS gets a fix.
    // --------------------------------------------------------

    marineSafetyInterval =
        setInterval(
            function() {

                loadMarineSafety();

            },
            10000
        );

}


// ============================================================
// START MARINE SAFETY
// ============================================================

function startMarineSafety() {

    console.log(
        "🌊 Starting Marine Safety GPS monitoring..."
    );


    // --------------------------------------------------------
    // Try immediately
    // --------------------------------------------------------

    loadMarineSafety();


    // --------------------------------------------------------
    // Keep checking until GPS becomes available
    // --------------------------------------------------------

    const safetyGPSInterval =
        setInterval(
            function() {

                if (
                    typeof currentLatitude !== "undefined" &&
                    typeof currentLongitude !== "undefined" &&
                    currentLatitude !== null &&
                    currentLongitude !== null &&
                    Number.isFinite(
                        Number(currentLatitude)
                    ) &&
                    Number.isFinite(
                        Number(currentLongitude)
                    )
                ) {

                    loadMarineSafety();

                }

            },
            5000
        );


    // Store globally so this monitoring loop
    // is not accidentally started more than once.
    window.orcaMarineSafetyGPSInterval =
        safetyGPSInterval;

}


// ============================================================
// START MARINE SAFETY AFTER HTML LOAD
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function() {

        startMarineSafety();

    }
);


// ============================================================
// START NORMAL MARINE SAFETY MONITOR
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function() {

        initializeMarineSafety();

    }
);
