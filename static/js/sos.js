"use strict";


/* =========================================================
   GLOBAL VARIABLES
========================================================= */

let lastPosition = null;

let watchId = null;

let currentSosId = null;

let sosState = "INACTIVE";

let confirmTimer = null;

let locationTimer = null;

let fishermanMap = null;

let fishermanMarker = null;

let rescueMap = null;

let rescueMarkers = {};

let alerts = [];

let selectedAlertId = null;


/* =========================================================
   ELEMENTS
========================================================= */

const fishermanView =
    document.getElementById("fishermanView");

const rescuerView =
    document.getElementById("rescuerView");

const fishermanTab =
    document.getElementById("fishermanTab");

const rescuerTab =
    document.getElementById("rescuerTab");

const sosButton =
    document.getElementById("sosButton");

const sosRing =
    document.getElementById("sosRing");

const sosText =
    document.getElementById("sosText");

const sosSubText =
    document.getElementById("sosSubText");

const sosMessage =
    document.getElementById("sosMessage");

const cancelButton =
    document.getElementById("cancelButton");

const emergencyType =
    document.getElementById("emergencyType");

const latitudeElement =
    document.getElementById("latitude");

const longitudeElement =
    document.getElementById("longitude");

const accuracyElement =
    document.getElementById("accuracy");

const locationStatus =
    document.getElementById("locationStatus");

const locationButton =
    document.getElementById("locationButton");

const locationWarning =
    document.getElementById("locationWarning");

const offlineBanner =
    document.getElementById("offlineBanner");

const sosInfoCard =
    document.getElementById("sosInfoCard");


/* =========================================================
   NETWORK
========================================================= */

function updateNetworkStatus() {

    const dot =
        document.getElementById(
            "networkDot"
        );

    const text =
        document.getElementById(
            "networkText"
        );


    if (navigator.onLine) {

        dot.className =
            "status-dot online";

        text.textContent =
            "Online";

        offlineBanner.classList.remove(
            "show"
        );

    }
    else {

        dot.className =
            "status-dot offline";

        text.textContent =
            "Offline";

        offlineBanner.classList.add(
            "show"
        );

    }

}


window.addEventListener(
    "online",
    updateNetworkStatus
);


window.addEventListener(
    "offline",
    updateNetworkStatus
);


/* =========================================================
   TAB SWITCHING
========================================================= */

fishermanTab.addEventListener(
    "click",
    function () {

        fishermanView.classList.remove(
            "hidden"
        );

        rescuerView.classList.add(
            "hidden"
        );

        fishermanTab.classList.add(
            "active"
        );

        rescuerTab.classList.remove(
            "active"
        );

    }
);


rescuerTab.addEventListener(
    "click",
    function () {

        fishermanView.classList.add(
            "hidden"
        );

        rescuerView.classList.remove(
            "hidden"
        );

        fishermanTab.classList.remove(
            "active"
        );

        rescuerTab.classList.add(
            "active"
        );


        setTimeout(
            function () {

                initializeRescueMap();

                loadSOSAlerts();

            },
            100
        );

    }
);


/* =========================================================
   FISHERMAN MAP
========================================================= */

function initializeFishermanMap() {

    if (fishermanMap) {

        return;

    }


    fishermanMap =
        L.map(
            "fishermanMap"
        ).setView(
            [20.5937, 78.9629],
            5
        );


    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 18,
            attribution:
                "&copy; OpenStreetMap contributors"
        }
    ).addTo(
        fishermanMap
    );

}


/* =========================================================
   GPS REQUEST
========================================================= */

function requestLocation() {

    if (!navigator.geolocation) {

        locationStatus.textContent =
            "GPS is not supported by this browser.";

        return;

    }


    locationStatus.textContent =
        "Getting GPS location...";


    navigator.geolocation.getCurrentPosition(

        handleLocationSuccess,

        handleLocationError,

        {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 5000
        }

    );

}


/* =========================================================
   GPS SUCCESS
========================================================= */

function handleLocationSuccess(
    position
) {

    lastPosition =
        position;


    const latitude =
        position.coords.latitude;

    const longitude =
        position.coords.longitude;

    const accuracy =
        position.coords.accuracy;


    latitudeElement.textContent =
        latitude.toFixed(6);

    longitudeElement.textContent =
        longitude.toFixed(6);

    accuracyElement.textContent =
        "±" +
        Math.round(
            accuracy
        ) +
        " m";


    locationStatus.textContent =
        "GPS location acquired · " +
        new Date().toLocaleTimeString();


    locationWarning.classList.add(
        "hidden"
    );


    locationButton.textContent =
        "Location Enabled ✓";


    initializeFishermanMap();


    if (!fishermanMarker) {

        fishermanMarker =
            L.marker(
                [
                    latitude,
                    longitude
                ]
            )
            .addTo(
                fishermanMap
            );

    }
    else {

        fishermanMarker.setLatLng(
            [
                latitude,
                longitude
            ]
        );

    }


    fishermanMarker.bindPopup(
        "Your current location"
    );


    fishermanMap.setView(
        [
            latitude,
            longitude
        ],
        13
    );


    /*
       If SOS is already active,
       send updated location.
    */

    if (currentSosId) {

        sendLocationUpdate();

    }

}


/* =========================================================
   GPS ERROR
========================================================= */

function handleLocationError(
    error
) {

    console.error(
        "GPS ERROR:",
        error
    );


    locationWarning.classList.remove(
        "hidden"
    );


    locationStatus.textContent =
        "Unable to get current GPS location.";

}


/* =========================================================
   ENABLE LOCATION
========================================================= */

locationButton.addEventListener(
    "click",
    requestLocation
);


/* =========================================================
   CONTINUOUS GPS WATCH
========================================================= */

function startLocationWatch() {

    if (!navigator.geolocation) {

        return;

    }


    if (watchId !== null) {

        return;

    }


    watchId =
        navigator.geolocation.watchPosition(

            handleLocationSuccess,

            handleLocationError,

            {
                enableHighAccuracy: true,
                timeout: 15000,
                maximumAge: 5000
            }

        );

}


/* =========================================================
   STOP GPS WATCH
========================================================= */

function stopLocationWatch() {

    if (watchId !== null) {

        navigator.geolocation.clearWatch(
            watchId
        );

        watchId = null;

    }

}


/* =========================================================
   SOS BUTTON
========================================================= */

sosButton.addEventListener(
    "click",
    function () {

        if (
            sosState === "INACTIVE"
        ) {

            prepareSOS();

            return;

        }


        if (
            sosState === "CONFIRM"
        ) {

            activateSOS();

            return;

        }

    }
);


/* =========================================================
   PREPARE SOS
========================================================= */

function prepareSOS() {

    sosState =
        "CONFIRM";


    sosButton.classList.add(
        "confirm"
    );


    sosText.textContent =
        "CONFIRM SOS";


    sosSubText.textContent =
        "Tap again to send";


    sosMessage.textContent =
        "Tap again to activate the emergency alert.";


    confirmTimer =
        setTimeout(
            function () {

                if (
                    sosState === "CONFIRM"
                ) {

                    resetSOS();

                }

            },
            7000
        );

}


/* =========================================================
   ACTIVATE SOS
========================================================= */

async function activateSOS() {

    clearTimeout(
        confirmTimer
    );


    sosState =
        "ACTIVE";


    sosButton.classList.remove(
        "confirm"
    );

    sosButton.classList.add(
        "active"
    );


    sosRing.classList.add(
        "active"
    );


    sosText.textContent =
        "SOS ACTIVE";


    sosSubText.textContent =
        "Sending alert...";


    cancelButton.classList.add(
        "show"
    );


    sosMessage.textContent =
        "Getting your GPS location...";


    /*
       First try to get GPS.
    */

    if (!lastPosition) {

        requestLocation();

        /*
           Give browser a short time
           to obtain location.
        */

        await waitForLocation();

    }


    try {

        const data =
            await createSOS();


        currentSosId =
            data.sos_id;


        sosSubText.textContent =
            "Alert sent";


        sosMessage.textContent =
            "Emergency alert sent successfully. SOS ID: " +
            currentSosId;


        showSOSInformation(
            data
        );


        startLocationWatch();

        startPeriodicLocationUpdates();

    }
    catch (error) {

        console.error(
            "SOS ERROR:",
            error
        );


        sosSubText.textContent =
            "Alert failed";


        sosMessage.textContent =
            error.message ||
            "Unable to send SOS alert.";


        offlineBanner.classList.add(
            "show"
        );

    }

}


/* =========================================================
   WAIT FOR GPS
========================================================= */

function waitForLocation() {

    return new Promise(
        function (resolve) {

            let attempts = 0;


            const timer =
                setInterval(
                    function () {

                        if (lastPosition) {

                            clearInterval(
                                timer
                            );

                            resolve();

                            return;

                        }


                        attempts++;


                        if (
                            attempts >= 20
                        ) {

                            clearInterval(
                                timer
                            );

                            resolve();

                        }

                    },
                    250
                );

        }
    );

}


/* =========================================================
   CREATE SOS
========================================================= */

async function createSOS() {

    /*
       Backend requires a location.
    */

    if (!lastPosition) {

        throw new Error(
            "GPS location is unavailable. Please enable location."
        );

    }


    const payload = {

        user_id:
            "USER001",

        latitude:
            lastPosition.coords.latitude,

        longitude:
            lastPosition.coords.longitude,

        accuracy:
            lastPosition.coords.accuracy,

        emergency_type:
            emergencyType.value

    };


    console.log(
        "Sending SOS:",
        payload
    );


    const response =
        await fetch(
            "/api/sos/create",
            {

                method: "POST",

                headers: {

                    "Content-Type":
                        "application/json"

                },

                body:
                    JSON.stringify(
                        payload
                    )

            }
        );


    const data =
        await response
            .json()
            .catch(
                function () {

                    return {};

                }
            );


    if (
        !response.ok ||
        !data.success
    ) {

        throw new Error(
            data.message ||
            "Backend failed to create SOS."
        );

    }


    return data;

}


/* =========================================================
   SHOW SOS INFORMATION
========================================================= */

function showSOSInformation(
    data
) {

    sosInfoCard.classList.remove(
        "hidden"
    );


    document.getElementById(
        "currentSosId"
    ).textContent =
        data.sos_id;


    document.getElementById(
        "currentSosStatus"
    ).textContent =
        "SOS ACTIVE";


    document.getElementById(
        "currentEmergency"
    ).textContent =
        emergencyType.value;


    document.getElementById(
        "currentLocationTime"
    ).textContent =
        new Date().toLocaleTimeString();

}


/* =========================================================
   PERIODIC LOCATION UPDATES
========================================================= */

function startPeriodicLocationUpdates() {

    clearInterval(
        locationTimer
    );


    locationTimer =
        setInterval(
            function () {

                if (
                    currentSosId &&
                    lastPosition
                ) {

                    sendLocationUpdate();

                }

            },
            15000
        );

}


/* =========================================================
   SEND LOCATION UPDATE
========================================================= */

async function sendLocationUpdate() {

    if (
        !currentSosId ||
        !lastPosition
    ) {

        return;

    }


    const payload = {

        latitude:
            lastPosition.coords.latitude,

        longitude:
            lastPosition.coords.longitude,

        accuracy:
            lastPosition.coords.accuracy

    };


    try {

        const response =
            await fetch(
                "/api/sos/" +
                currentSosId +
                "/location",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify(
                            payload
                        )

                }
            );


        const data =
            await response.json();


        console.log(
            "Location update:",
            data
        );


        if (data.success) {

            document.getElementById(
                "currentLocationTime"
            ).textContent =
                new Date().toLocaleTimeString();

        }

    }
    catch (error) {

        console.error(
            "Location update failed:",
            error
        );

    }

}


/* =========================================================
   CANCEL SOS
========================================================= */

cancelButton.addEventListener(
    "click",
    function () {

        stopLocationWatch();

        clearInterval(
            locationTimer
        );


        /*
           Current backend does not yet
           have a dedicated cancel route.

           Therefore this resets the frontend.
        */

        currentSosId = null;


        resetSOS();


        sosMessage.textContent =
            "SOS cancelled on this device.";

    }
);


/* =========================================================
   RESET SOS UI
========================================================= */

function resetSOS() {

    sosState =
        "INACTIVE";


    sosButton.classList.remove(
        "confirm",
        "active"
    );


    sosRing.classList.remove(
        "active"
    );


    sosText.textContent =
        "SOS";


    sosSubText.textContent =
        "Press for emergency";


    sosMessage.textContent =
        "Press SOS once and confirm.";


    cancelButton.classList.remove(
        "show"
    );

}


/* =========================================================
   SHARE LOCATION
========================================================= */

document
.getElementById(
    "shareLocationButton"
)
.addEventListener(
    "click",
    function () {

        if (!lastPosition) {

            requestLocation();

            return;

        }


        /*
           If there is an active SOS,
           update backend.

           Otherwise this just shows
           the current GPS location.
        */

        if (currentSosId) {

            sendLocationUpdate();

        }


        locationStatus.textContent =
            "Location shared · " +
            new Date().toLocaleTimeString();

    }
);


/* =========================================================
   SMS FALLBACK
========================================================= */

document
.getElementById(
    "smsButton"
)
.addEventListener(
    "click",
    function () {

        let message =
            "ORCA SOS - Emergency assistance required.";


        if (lastPosition) {

            message +=
                " Location: " +
                lastPosition.coords.latitude.toFixed(6) +
                ", " +
                lastPosition.coords.longitude.toFixed(6);

        }


        window.location.href =
            "sms:?body=" +
            encodeURIComponent(
                message
            );

    }
);


/* =========================================================
   PHONE FALLBACK
========================================================= */

document
.getElementById(
    "callButton"
)
.addEventListener(
    "click",
    function () {

        /*
           Replace this number with
           your actual configured
           rescue number.
        */

        window.location.href =
            "tel:1554";

    }
);


/* =========================================================
   RESCUER MAP
========================================================= */

function initializeRescueMap() {

    if (rescueMap) {

        rescueMap.invalidateSize();

        return;

    }


    rescueMap =
        L.map(
            "rescueMap"
        ).setView(
            [20.5937,78.9629],
            5
        );


    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {

            maxZoom: 18,

            attribution:
                "&copy; OpenStreetMap contributors"

        }
    ).addTo(
        rescueMap
    );

}


/* =========================================================
   LOAD SOS ALERTS
========================================================= */

async function loadSOSAlerts() {

    try {

        const response =
            await fetch(
                "/api/sos/active"
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.message ||
                "Unable to load alerts."
            );

        }


        alerts =
            data.alerts || [];


        renderDashboard();


    }
    catch (error) {

        console.error(
            "Dashboard error:",
            error
        );

    }

}


/* =========================================================
   RENDER DASHBOARD
========================================================= */

function renderDashboard() {

    updateKPIs();

    renderIncidentList();

    renderIncidentDetails();

    renderRescueMarkers();

}


/* =========================================================
   KPI
========================================================= */

function updateKPIs() {

    let active = 0;

    let acknowledged = 0;

    let resolved = 0;


    alerts.forEach(
        function (alert) {

            if (
                alert.status ===
                "SOS_ACTIVE"
            ) {

                active++;

            }


            if (
                alert.status ===
                "RESCUE_ACKNOWLEDGED"
            ) {

                acknowledged++;

            }


            if (
                alert.status ===
                "EMERGENCY_RESOLVED"
            ) {

                resolved++;

            }

        }
    );


    document.getElementById(
        "activeCount"
    ).textContent =
        active;


    document.getElementById(
        "acknowledgedCount"
    ).textContent =
        acknowledged;


    document.getElementById(
        "totalCount"
    ).textContent =
        alerts.length;


    document.getElementById(
        "resolvedCount"
    ).textContent =
        resolved;

}


/* =========================================================
   INCIDENT LIST
========================================================= */

function renderIncidentList() {

    const list =
        document.getElementById(
            "incidentList"
        );


    list.innerHTML = "";


    if (
        alerts.length === 0
    ) {

        list.innerHTML =
            '<div class="empty-message">' +
            'No emergency alerts.' +
            '</div>';

        return;

    }


    alerts.forEach(
        function (alert) {

            const button =
                document.createElement(
                    "button"
                );


            button.className =
                "incident-item";


            if (
                selectedAlertId ===
                alert.sos_id
            ) {

                button.classList.add(
                    "selected"
                );

            }


            button.innerHTML =

                '<div class="incident-title">' +

                escapeHTML(
                    alert.sos_id
                ) +

                ' · ' +

                escapeHTML(
                    alert.emergency_type ||
                    "Emergency"
                ) +

                '</div>' +


                '<div class="incident-sub">' +

                'Location: ' +

                Number(
                    alert.latitude
                ).toFixed(5) +

                ', ' +

                Number(
                    alert.longitude
                ).toFixed(5) +

                '<br>' +

                'User: ' +

                escapeHTML(
                    alert.user_id
                ) +

                '</div>' +


                '<span class="status-badge ' +

                getStatusClass(
                    alert.status
                ) +

                '">' +

                formatStatus(
                    alert.status
                ) +

                '</span>';


            button.addEventListener(
                "click",
                function () {

                    selectedAlertId =
                        alert.sos_id;

                    renderDashboard();

                }
            );


            list.appendChild(
                button
            );

        }
    );

}


/* =========================================================
   INCIDENT DETAILS
========================================================= */

function renderIncidentDetails() {

    const details =
        document.getElementById(
            "incidentDetails"
        );


    const alert =
        alerts.find(
            function (item) {

                return (
                    item.sos_id ===
                    selectedAlertId
                );

            }
        );


    if (!alert) {

        details.innerHTML =
            '<div class="empty-message">' +
            'Select an emergency alert to view details.' +
            '</div>';

        return;

    }


    let buttons = "";


    if (
        alert.status ===
        "SOS_ACTIVE"
    ) {

        buttons +=

            '<button class="detail-btn warning" ' +

            'onclick="changeSOSStatus(\'' +

            alert.sos_id +

            '\',\'RESCUE_ACKNOWLEDGED\')">' +

            'Acknowledge' +

            '</button>';

    }


    if (
        alert.status ===
        "RESCUE_ACKNOWLEDGED"
    ) {

        buttons +=

            '<button class="detail-btn primary" ' +

            'onclick="changeSOSStatus(\'' +

            alert.sos_id +

            '\',\'RESCUE_IN_PROGRESS\')">' +

            'Start Rescue' +

            '</button>';

    }


    if (
        alert.status ===
        "RESCUE_IN_PROGRESS"
    ) {

        buttons +=

            '<button class="detail-btn primary" ' +

            'onclick="changeSOSStatus(\'' +

            alert.sos_id +

            '\',\'EMERGENCY_RESOLVED\')">' +

            'Mark Resolved' +

            '</button>';

    }


    details.innerHTML =

        '<div class="card-header">' +

        '<h3>' +

        escapeHTML(
            alert.sos_id
        ) +

        '</h3>' +

        '<p>' +

        escapeHTML(
            alert.emergency_type ||
            "Emergency"
        ) +

        '</p>' +

        '</div>' +


        '<div class="info-row">' +

        '<span>User</span>' +

        '<strong>' +

        escapeHTML(
            alert.user_id
        ) +

        '</strong>' +

        '</div>' +


        '<div class="info-row">' +

        '<span>Latitude</span>' +

        '<strong>' +

        Number(
            alert.latitude
        ).toFixed(6) +

        '</strong>' +

        '</div>' +


        '<div class="info-row">' +

        '<span>Longitude</span>' +

        '<strong>' +

        Number(
            alert.longitude
        ).toFixed(6) +

        '</strong>' +

        '</div>' +


        '<div class="info-row">' +

        '<span>Accuracy</span>' +

        '<strong>' +

        Math.round(
            alert.accuracy || 0
        ) +

        ' m</strong>' +

        '</div>' +


        '<div class="info-row">' +

        '<span>Status</span>' +

        '<strong>' +

        formatStatus(
            alert.status
        ) +

        '</strong>' +

        '</div>' +


        '<div class="info-row">' +

        '<span>Alert time</span>' +

        '<strong>' +

        formatDate(
            alert.created_at
        ) +

        '</strong>' +

        '</div>' +


        '<div class="detail-actions">' +

        buttons +

        '<button class="detail-btn" ' +

        'onclick="focusAlert(\'' +

        alert.sos_id +

        '\')">' +

        'View on Map' +

        '</button>' +

        '</div>';

}


/* =========================================================
   STATUS CLASS
========================================================= */

function getStatusClass(
    status
) {

    if (
        status ===
        "RESCUE_ACKNOWLEDGED"
    ) {

        return "status-ack";

    }


    if (
        status ===
        "RESCUE_IN_PROGRESS"
    ) {

        return "status-rescue";

    }


    if (
        status ===
        "EMERGENCY_RESOLVED"
    ) {

        return "status-resolved";

    }


    return "status-active";

}


/* =========================================================
   FORMAT STATUS
========================================================= */

function formatStatus(
    status
) {

    const names = {

        "SOS_ACTIVE":
            "SOS ACTIVE",

        "LOCATION_ACQUIRED":
            "LOCATION ACQUIRED",

        "ALERT_SENT":
            "ALERT SENT",

        "ALERT_FAILED":
            "ALERT FAILED",

        "RESCUE_ACKNOWLEDGED":
            "RESCUE ACKNOWLEDGED",

        "RESCUE_IN_PROGRESS":
            "RESCUE IN PROGRESS",

        "EMERGENCY_RESOLVED":
            "EMERGENCY RESOLVED"

    };


    return (
        names[status] ||
        status ||
        "UNKNOWN"
    );

}


/* =========================================================
   RESCUE MAP MARKERS
========================================================= */

function renderRescueMarkers() {

    if (!rescueMap) {

        return;

    }


    alerts.forEach(
        function (alert) {

            const lat =
                Number(
                    alert.latitude
                );

            const lon =
                Number(
                    alert.longitude
                );


            if (
                !Number.isFinite(lat) ||
                !Number.isFinite(lon)
            ) {

                return;

            }


            const markerColor =
                alert.status ===
                "EMERGENCY_RESOLVED"

                    ? "green"

                    :

                alert.status ===
                "RESCUE_IN_PROGRESS"

                    ? "teal"

                    :

                alert.status ===
                "RESCUE_ACKNOWLEDGED"

                    ? "orange"

                    :

                      "red";


            if (
                rescueMarkers[
                    alert.sos_id
                ]
            ) {

                rescueMarkers[
                    alert.sos_id
                ].setLatLng(
                    [lat,lon]
                );

                return;

            }


            const marker =
                L.circleMarker(
                    [lat,lon],
                    {

                        radius: 9,

                        color:
                            markerColor,

                        fillColor:
                            markerColor,

                        fillOpacity: 0.85,

                        weight: 2

                    }
                );


            marker.addTo(
                rescueMap
            );


            marker.bindPopup(

                "<strong>" +

                escapeHTML(
                    alert.sos_id
                ) +

                "</strong><br>" +

                escapeHTML(
                    alert.emergency_type ||
                    "Emergency"
                ) +

                "<br>" +

                formatStatus(
                    alert.status
                )

            );


            marker.on(
                "click",
                function () {

                    selectedAlertId =
                        alert.sos_id;

                    renderDashboard();

                }
            );


            rescueMarkers[
                alert.sos_id
            ] =
                marker;

        }
    );

}


/* =========================================================
   FOCUS ALERT
========================================================= */

function focusAlert(
    sosId
) {

    const alert =
        alerts.find(
            function (item) {

                return (
                    item.sos_id ===
                    sosId
                );

            }
        );


    if (
        !alert ||
        !rescueMap
    ) {

        return;

    }


    rescueMap.setView(
        [
            Number(
                alert.latitude
            ),

            Number(
                alert.longitude
            )
        ],
        14
    );


    if (
        rescueMarkers[sosId]
    ) {

        rescueMarkers[sosId].openPopup();

    }

}


/* =========================================================
   CHANGE SOS STATUS
========================================================= */

async function changeSOSStatus(
    sosId,
    newStatus
) {

    try {

        const response =
            await fetch(
                "/api/sos/" +
                sosId +
                "/status",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

                            status:
                                newStatus

                        })

                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.message ||
                "Status update failed."
            );

        }


        selectedAlertId =
            sosId;


        await loadSOSAlerts();

    }
    catch (error) {

        console.error(
            "Status update error:",
            error
        );


        alert(
            error.message
        );

    }

}


/* =========================================================
   DATE
========================================================= */

function formatDate(
    value
) {

    if (!value) {

        return "Unknown";

    }


    const date =
        new Date(value);


    if (
        isNaN(
            date.getTime()
        )
    ) {

        return "Unknown";

    }


    return date.toLocaleString();

}


/* =========================================================
   HTML ESCAPE
========================================================= */

function escapeHTML(
    value
) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }


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


/* =========================================================
   AUTO REFRESH
========================================================= */

setInterval(
    function () {

        if (
            !rescuerView.classList.contains(
                "hidden"
            )
        ) {

            loadSOSAlerts();

        }

    },
    5000
);


/* =========================================================
   ASSISTANT
========================================================= */

const assistantButton =
    document.getElementById(
        "assistantButton"
    );

const assistantPanel =
    document.getElementById(
        "assistantPanel"
    );

const assistantClose =
    document.getElementById(
        "assistantClose"
    );


assistantButton.addEventListener(
    "click",
    function () {

        assistantPanel.classList.toggle(
            "hidden"
        );

    }
);


assistantClose.addEventListener(
    "click",
    function () {

        assistantPanel.classList.add(
            "hidden"
        );

    }
);


/* =========================================================
   INITIALIZE
========================================================= */

function initialize() {

    updateNetworkStatus();

    initializeFishermanMap();

    requestLocation();

}


initialize();