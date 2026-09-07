/* =========================================================
   ORCA - OFFLINE MARINE SAFETY SYSTEM
   =========================================================

   Features:
   1. Stores latest weather/ocean/marine safety data locally
   2. Works when internet is unavailable
   3. Stores SOS locally when network is unavailable
   4. Automatically sends pending SOS when network returns
   5. Automatically refreshes safety data when network returns
   6. Stores the fisherman's latest GPS location
   7. Shows whether data is LIVE or OFFLINE
   ========================================================= */


/* =========================================================
   CONFIGURATION
   ========================================================= */

const ORCA_DB_NAME = "ORCA_OfflineDB";
const ORCA_DB_VERSION = 1;

const SAFETY_STORE = "safety_data";
const SOS_STORE = "sos_queue";
const LOCATION_STORE = "location_data";

const SAFETY_DATA_ID = "latest";


/* =========================================================
   1. OPEN OFFLINE DATABASE
   ========================================================= */

function openOfflineDB() {

    return new Promise((resolve, reject) => {

        const request = indexedDB.open(
            ORCA_DB_NAME,
            ORCA_DB_VERSION
        );


        /* -------------------------------------------------
           Create database stores
           ------------------------------------------------- */

        request.onupgradeneeded = function(event) {

            const db = event.target.result;


            // Safety data
            if (!db.objectStoreNames.contains(SAFETY_STORE)) {

                db.createObjectStore(
                    SAFETY_STORE,
                    {
                        keyPath: "id"
                    }
                );
            }


            // SOS queue
            if (!db.objectStoreNames.contains(SOS_STORE)) {

                db.createObjectStore(
                    SOS_STORE,
                    {
                        keyPath: "id"
                    }
                );
            }


            // GPS location
            if (!db.objectStoreNames.contains(LOCATION_STORE)) {

                db.createObjectStore(
                    LOCATION_STORE,
                    {
                        keyPath: "id"
                    }
                );
            }
        };


        request.onsuccess = function(event) {

            resolve(event.target.result);
        };


        request.onerror = function() {

            console.error(
                "ORCA Offline DB Error:",
                request.error
            );

            reject(request.error);
        };
    });
}


/* =========================================================
   2. SAVE SAFETY DATA
   ========================================================= */

async function saveOfflineSafety(data) {

    try {

        const db = await openOfflineDB();


        return new Promise((resolve, reject) => {

            const transaction = db.transaction(
                SAFETY_STORE,
                "readwrite"
            );

            const store =
                transaction.objectStore(
                    SAFETY_STORE
                );


            store.put({

                id: SAFETY_DATA_ID,

                saved_at:
                    new Date().toISOString(),

                data: data
            });


            transaction.oncomplete = function() {

                console.log(
                    "ORCA: Safety data saved offline."
                );

                resolve(true);
            };


            transaction.onerror = function() {

                console.error(
                    "ORCA: Failed to save safety data.",
                    transaction.error
                );

                reject(transaction.error);
            };
        });

    } catch (error) {

        console.error(
            "ORCA: saveOfflineSafety error:",
            error
        );

        return false;
    }
}


/* =========================================================
   3. GET CACHED SAFETY DATA
   ========================================================= */

async function getOfflineSafety() {

    try {

        const db = await openOfflineDB();


        return new Promise((resolve, reject) => {

            const transaction = db.transaction(
                SAFETY_STORE,
                "readonly"
            );

            const store =
                transaction.objectStore(
                    SAFETY_STORE
                );


            const request =
                store.get(SAFETY_DATA_ID);


            request.onsuccess = function() {

                if (request.result) {

                    resolve(request.result);

                } else {

                    resolve(null);
                }
            };


            request.onerror = function() {

                reject(request.error);
            };
        });

    } catch (error) {

        console.error(
            "ORCA: getOfflineSafety error:",
            error
        );

        return null;
    }
}


/* =========================================================
   4. SAVE FISHERMAN GPS LOCATION
   ========================================================= */

async function saveOfflineLocation(
    latitude,
    longitude
) {

    try {

        const db = await openOfflineDB();


        return new Promise((resolve, reject) => {

            const transaction = db.transaction(
                LOCATION_STORE,
                "readwrite"
            );

            const store =
                transaction.objectStore(
                    LOCATION_STORE
                );


            store.put({

                id: "latest",

                latitude: latitude,

                longitude: longitude,

                saved_at:
                    new Date().toISOString()
            });


            transaction.oncomplete = function() {

                // Also keep location in localStorage
                localStorage.setItem(
                    "orca_latitude",
                    latitude
                );

                localStorage.setItem(
                    "orca_longitude",
                    longitude
                );


                resolve(true);
            };


            transaction.onerror = function() {

                reject(transaction.error);
            };
        });

    } catch (error) {

        console.error(
            "ORCA: saveOfflineLocation error:",
            error
        );

        return false;
    }
}


/* =========================================================
   5. GET LAST GPS LOCATION
   ========================================================= */

async function getOfflineLocation() {

    try {

        const db = await openOfflineDB();


        return new Promise((resolve, reject) => {

            const transaction = db.transaction(
                LOCATION_STORE,
                "readonly"
            );

            const store =
                transaction.objectStore(
                    LOCATION_STORE
                );


            const request =
                store.get("latest");


            request.onsuccess = function() {

                if (request.result) {

                    resolve(request.result);

                } else {

                    resolve(null);
                }
            };


            request.onerror = function() {

                reject(request.error);
            };
        });

    } catch (error) {

        console.error(
            "ORCA: getOfflineLocation error:",
            error
        );

        return null;
    }
}


/* =========================================================
   6. UPDATE GPS LOCATION
   ========================================================= */

function startOfflineLocationTracking() {

    if (!navigator.geolocation) {

        console.warn(
            "ORCA: Geolocation is not supported."
        );

        return;
    }


    navigator.geolocation.watchPosition(

        async function(position) {

            const latitude =
                position.coords.latitude;

            const longitude =
                position.coords.longitude;


            await saveOfflineLocation(
                latitude,
                longitude
            );


            console.log(
                "ORCA GPS:",
                latitude,
                longitude
            );
        },


        function(error) {

            console.warn(
                "ORCA GPS Error:",
                error.message
            );
        },


        {
            enableHighAccuracy: true,

            maximumAge: 30000,

            timeout: 15000
        }
    );
}


/* =========================================================
   7. DOWNLOAD AND CACHE SAFETY DATA
   ========================================================= */

async function syncOfflineSafety(
    latitude,
    longitude
) {

    if (!navigator.onLine) {

        console.log(
            "ORCA: Offline. Using cached safety data."
        );

        return false;
    }


    try {

        const response = await fetch(

            `/api/offline-safety?lat=${encodeURIComponent(latitude)}&lon=${encodeURIComponent(longitude)}`,

            {
                method: "GET",

                cache: "no-store"
            }
        );


        if (!response.ok) {

            throw new Error(
                `Safety API returned ${response.status}`
            );
        }


        const data =
            await response.json();


        if (!data.success) {

            throw new Error(
                data.message ||
                "Safety API failed"
            );
        }


        await saveOfflineSafety(data);


        console.log(
            "ORCA: Offline safety data updated."
        );


        updateOfflineStatus(
            "ONLINE",
            data.cached_at
        );


        return true;

    } catch (error) {

        console.error(
            "ORCA: Safety sync failed:",
            error
        );


        updateOfflineStatus(
            "OFFLINE"
        );


        return false;
    }
}


/* =========================================================
   8. LOAD SAFETY DATA
   =========================================================

   If network exists:
       Try live data first.

   If network fails:
       Use cached data.

   ========================================================= */

async function loadSafetyData(
    latitude,
    longitude
) {

    /* -----------------------------------------------------
       Try live data
       ----------------------------------------------------- */

    if (navigator.onLine) {

        const synced =
            await syncOfflineSafety(
                latitude,
                longitude
            );


        if (synced) {

            const cached =
                await getOfflineSafety();

            if (cached) {

                return cached.data;
            }
        }
    }


    /* -----------------------------------------------------
       Network unavailable
       Use cached data
       ----------------------------------------------------- */

    const cached =
        await getOfflineSafety();


    if (cached) {

        console.log(
            "ORCA: Using cached marine safety data."
        );


        updateOfflineStatus(
            "OFFLINE",
            cached.saved_at
        );


        return cached.data;
    }


    /* -----------------------------------------------------
       Nothing available
       ----------------------------------------------------- */

    console.warn(
        "ORCA: No offline safety data available."
    );


    updateOfflineStatus(
        "NO DATA"
    );


    return null;
}


/* =========================================================
   9. CREATE OFFLINE SOS
   ========================================================= */

async function createOfflineSOS(
    latitude,
    longitude,
    message = "Emergency SOS from fisherman"
) {

    const sos = {

        id:
            "SOS-" +
            Date.now() +
            "-" +
            Math.random()
                .toString(36)
                .substring(2, 8),

        latitude:
            latitude,

        longitude:
            longitude,

        message:
            message,

        created_at:
            new Date().toISOString(),

        status:
            "PENDING_UPLOAD",

        attempts:
            0,

        last_attempt:
            null
    };


    try {

        const db =
            await openOfflineDB();


        return new Promise((resolve, reject) => {

            const transaction =
                db.transaction(
                    SOS_STORE,
                    "readwrite"
                );

            const store =
                transaction.objectStore(
                    SOS_STORE
                );


            store.add(sos);


            transaction.oncomplete =
                function() {

                    console.log(
                        "🚨 ORCA: SOS stored offline."
                    );


                    /*
                     * Also keep a simple flag
                     * so the application knows
                     * an SOS is waiting.
                     */

                    localStorage.setItem(
                        "orca_sos_pending",
                        "true"
                    );


                    resolve(sos);
                };


            transaction.onerror =
                function() {

                    console.error(
                        "ORCA: Failed to store SOS.",
                        transaction.error
                    );


                    reject(
                        transaction.error
                    );
                };
        });

    } catch (error) {

        console.error(
            "ORCA: createOfflineSOS error:",
            error
        );


        return null;
    }
}


/* =========================================================
   10. GET ALL PENDING SOS
   ========================================================= */

async function getPendingSOS() {

    try {

        const db =
            await openOfflineDB();


        return new Promise((resolve, reject) => {

            const transaction =
                db.transaction(
                    SOS_STORE,
                    "readonly"
                );

            const store =
                transaction.objectStore(
                    SOS_STORE
                );


            const request =
                store.getAll();


            request.onsuccess =
                function() {

                    resolve(
                        request.result || []
                    );
                };


            request.onerror =
                function() {

                    reject(
                        request.error
                    );
                };
        });

    } catch (error) {

        console.error(
            "ORCA: getPendingSOS error:",
            error
        );

        return [];
    }
}


/* =========================================================
   11. DELETE SOS FROM QUEUE
   ========================================================= */

async function removePendingSOS(
    sosId
) {

    try {

        const db =
            await openOfflineDB();


        return new Promise((resolve, reject) => {

            const transaction =
                db.transaction(
                    SOS_STORE,
                    "readwrite"
                );

            const store =
                transaction.objectStore(
                    SOS_STORE
                );


            store.delete(sosId);


            transaction.oncomplete =
                function() {

                    resolve(true);
                };


            transaction.onerror =
                function() {

                    reject(
                        transaction.error
                    );
                };
        });

    } catch (error) {

        console.error(
            "ORCA: removePendingSOS error:",
            error
        );

        return false;
    }
}


/* =========================================================
   12. UPDATE SOS ATTEMPT
   ========================================================= */

async function updateSOSAttempt(
    sos
) {

    try {

        const db =
            await openOfflineDB();


        return new Promise((resolve, reject) => {

            const transaction =
                db.transaction(
                    SOS_STORE,
                    "readwrite"
                );

            const store =
                transaction.objectStore(
                    SOS_STORE
                );


            sos.attempts =
                (sos.attempts || 0) + 1;

            sos.last_attempt =
                new Date().toISOString();


            store.put(sos);


            transaction.oncomplete =
                function() {

                    resolve(true);
                };


            transaction.onerror =
                function() {

                    reject(
                        transaction.error
                    );
                };
        });

    } catch (error) {

        console.error(
            "ORCA: updateSOSAttempt error:",
            error
        );

        return false;
    }
}


/* =========================================================
   13. SEND ONE SOS TO SERVER
   ========================================================= */

async function sendSingleSOS(
    sos
) {

    if (!navigator.onLine) {

        return false;
    }


    try {

        await updateSOSAttempt(sos);


        const response =
            await fetch(
                "/api/sos/create",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        latitude:
                            sos.latitude,

                        longitude:
                            sos.longitude,

                        message:
                            sos.message
                    })
                }
            );


        if (!response.ok) {

            throw new Error(
                `SOS API returned ${response.status}`
            );
        }


        const result =
            await response.json();


        /*
         * Only delete the local SOS after
         * the server confirms success.
         */

        await removePendingSOS(
            sos.id
        );


        console.log(
            "🚨 ORCA: Offline SOS successfully sent.",
            result
        );


        return true;

    } catch (error) {

        console.error(
            "ORCA: SOS upload failed:",
            error
        );


        return false;
    }
}


/* =========================================================
   14. SEND ALL QUEUED SOS
   ========================================================= */

async function sendQueuedSOS() {

    if (!navigator.onLine) {

        console.log(
            "ORCA: Still offline. SOS remains queued."
        );

        return false;
    }


    const pendingSOS =
        await getPendingSOS();


    if (
        !pendingSOS ||
        pendingSOS.length === 0
    ) {

        localStorage.removeItem(
            "orca_sos_pending"
        );

        return true;
    }


    console.log(
        `ORCA: ${pendingSOS.length} pending SOS found.`
    );


    let allSent = true;


    for (const sos of pendingSOS) {

        const sent =
            await sendSingleSOS(sos);


        if (!sent) {

            allSent = false;
        }
    }


    /*
     * Check again after uploading.
     */

    const remaining =
        await getPendingSOS();


    if (remaining.length === 0) {

        localStorage.removeItem(
            "orca_sos_pending"
        );

        console.log(
            "ORCA: All pending SOS messages sent."
        );

    } else {

        localStorage.setItem(
            "orca_sos_pending",
            "true"
        );
    }


    return allSent;
}


/* =========================================================
   15. MAIN SOS FUNCTION
   =========================================================

   Use this function for your SOS button.

   Example:

       handleOfflineSOS();

   ========================================================= */

async function handleOfflineSOS(
    message = "Emergency SOS from fisherman"
) {

    /* -----------------------------------------------------
       Get latest GPS
       ----------------------------------------------------- */

    let location =
        await getOfflineLocation();


    let latitude = null;
    let longitude = null;


    if (location) {

        latitude =
            parseFloat(location.latitude);

        longitude =
            parseFloat(location.longitude);
    }


    /*
     * If IndexedDB does not have the location,
     * try localStorage.
     */

    if (
        latitude === null ||
        longitude === null ||
        Number.isNaN(latitude) ||
        Number.isNaN(longitude)
    ) {

        latitude =
            parseFloat(
                localStorage.getItem(
                    "orca_latitude"
                )
            );

        longitude =
            parseFloat(
                localStorage.getItem(
                    "orca_longitude"
                )
            );
    }


    /* -----------------------------------------------------
       Make sure GPS exists
       ----------------------------------------------------- */

    if (
        latitude === null ||
        longitude === null ||
        Number.isNaN(latitude) ||
        Number.isNaN(longitude)
    ) {

        alert(
            "⚠️ GPS location is not available.\n\n" +
            "Please enable location services and try again."
        );


        return false;
    }


    /* -----------------------------------------------------
       ONLINE
       ----------------------------------------------------- */

    if (navigator.onLine) {

        try {

            const response =
                await fetch(
                    "/api/sos/create",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({

                            latitude:
                                latitude,

                            longitude:
                                longitude,

                            message:
                                message
                        })
                    }
                );


            if (response.ok) {

                const result =
                    await response.json();


                console.log(
                    "🚨 ORCA: SOS sent successfully.",
                    result
                );


                alert(
                    "🚨 SOS SENT SUCCESSFULLY\n\n" +
                    `Location: ${latitude.toFixed(5)}, ` +
                    `${longitude.toFixed(5)}`
                );


                return true;
            }

        } catch (error) {

            console.warn(
                "ORCA: Online SOS failed. " +
                "Switching to offline queue.",
                error
            );
        }
    }


    /* -----------------------------------------------------
       OFFLINE OR ONLINE REQUEST FAILED
       Store SOS locally.
       ----------------------------------------------------- */

    const sos =
        await createOfflineSOS(
            latitude,
            longitude,
            message
        );


    if (sos) {

        alert(
            "🚨 SOS STORED OFFLINE\n\n" +

            "Network is unavailable.\n" +

            "Your SOS and GPS location have been " +
            "saved on this device.\n\n" +

            "ORCA will automatically send the SOS " +
            "when network connectivity returns."
        );


        return true;
    }


    alert(
        "❌ SOS could not be stored.\n\n" +
        "Please try again."
    );


    return false;
}


/* =========================================================
   16. NETWORK STATUS
   ========================================================= */

function updateOfflineStatus(
    status,
    timestamp = null
) {

    console.log(
        "ORCA Network Status:",
        status
    );


    /*
     * If the HTML contains an element with
     * id="offline-status", update it.
     */

    const statusElement =
        document.getElementById(
            "offline-status"
        );


    if (!statusElement) {

        return;
    }


    if (status === "ONLINE") {

        statusElement.textContent =
            "🟢 ONLINE";


        statusElement.title =
            "Live ORCA data is available.";

    }

    else if (status === "OFFLINE") {

        statusElement.textContent =
            "🔴 OFFLINE";


        if (timestamp) {

            statusElement.title =
                "Using cached safety data. " +
                "Last updated: " +
                new Date(timestamp)
                    .toLocaleString();

        } else {

            statusElement.title =
                "Using cached safety data.";
        }

    }

    else {

        statusElement.textContent =
            "⚠️ NO DATA";


        statusElement.title =
            "No cached marine safety data is available.";
    }
}


/* =========================================================
   17. SHOW CACHED DATA WARNING
   ========================================================= */

async function showOfflineDataInfo() {

    const cached =
        await getOfflineSafety();


    if (!cached) {

        return;
    }


    const savedTime =
        new Date(
            cached.saved_at
        ).toLocaleString();


    console.log(
        "ORCA Offline Data",
        "Last updated:",
        savedTime
    );


    /*
     * Optional HTML element:
     *
     * <div id="offline-data-info"></div>
     */

    const infoElement =
        document.getElementById(
            "offline-data-info"
        );


    if (infoElement) {

        infoElement.textContent =
            `⚠️ Offline data — Last updated: ${savedTime}`;
    }
}


/* =========================================================
   18. INITIALIZE ORCA OFFLINE SYSTEM
   ========================================================= */

async function initializeOfflineSafety() {

    console.log(
        "======================================"
    );

    console.log(
        "ORCA OFFLINE SAFETY SYSTEM"
    );

    console.log(
        "Initializing..."
    );

    console.log(
        "======================================"
    );


    /* -----------------------------------------------------
       Start GPS tracking
       ----------------------------------------------------- */

    startOfflineLocationTracking();


    /* -----------------------------------------------------
       Check network
       ----------------------------------------------------- */

    if (navigator.onLine) {

        console.log(
            "ORCA: Network available."
        );


        updateOfflineStatus(
            "ONLINE"
        );


        /*
         * Get latest location and sync.
         */

        const location =
            await getOfflineLocation();


        if (location) {

            await syncOfflineSafety(
                location.latitude,
                location.longitude
            );
        }


        /*
         * Send any SOS that was queued
         * during previous offline period.
         */

        await sendQueuedSOS();

    } else {

        console.log(
            "ORCA: Device is currently offline."
        );


        updateOfflineStatus(
            "OFFLINE"
        );


        await showOfflineDataInfo();
    }


    /*
     * Check if there are pending SOS messages.
     */

    const pendingSOS =
        await getPendingSOS();


    if (pendingSOS.length > 0) {

        console.log(
            `ORCA: ${pendingSOS.length} SOS waiting for upload.`
        );

    } else {

        console.log(
            "ORCA: No pending SOS."
        );
    }
}


/* =========================================================
   19. NETWORK RETURNS
   ========================================================= */

window.addEventListener(
    "online",
    async function() {

        console.log(
            "======================================"
        );

        console.log(
            "📶 ORCA NETWORK AVAILABLE"
        );

        console.log(
            "======================================"
        );


        updateOfflineStatus(
            "ONLINE"
        );


        /*
         * Get latest GPS
         */

        const location =
            await getOfflineLocation();


        /*
         * Update cached safety information.
         */

        if (location) {

            await syncOfflineSafety(
                location.latitude,
                location.longitude
            );
        }


        /*
         * Send queued SOS.
         */

        await sendQueuedSOS();


        /*
         * Show latest offline data.
         */

        await showOfflineDataInfo();
    }
);


/* =========================================================
   20. NETWORK LOST
   ========================================================= */

window.addEventListener(
    "offline",
    async function() {

        console.log(
            "======================================"
        );

        console.log(
            "📵 ORCA NETWORK LOST"
        );

        console.log(
            "Using cached marine safety information."
        );

        console.log(
            "======================================"
        );


        updateOfflineStatus(
            "OFFLINE"
        );


        await showOfflineDataInfo();
    }
);


/* =========================================================
   21. PERIODIC SOS RETRY
   =========================================================

   Even if the "online" event is not fired correctly,
   ORCA periodically checks whether the network has
   returned.

   ========================================================= */

setInterval(
    async function() {

        if (navigator.onLine) {

            const pendingSOS =
                await getPendingSOS();


            if (
                pendingSOS &&
                pendingSOS.length > 0
            ) {

                console.log(
                    "ORCA: Retrying queued SOS..."
                );


                await sendQueuedSOS();
            }
        }

    },
    30000
);


/* =========================================================
   22. PERIODIC SAFETY DATA UPDATE
   =========================================================

   Every 15 minutes, if internet exists,
   refresh the offline safety cache.

   ========================================================= */

setInterval(
    async function() {

        if (!navigator.onLine) {

            return;
        }


        const location =
            await getOfflineLocation();


        if (!location) {

            return;
        }


        console.log(
            "ORCA: Refreshing offline safety data..."
        );


        await syncOfflineSafety(
            location.latitude,
            location.longitude
        );

    },
    15 * 60 * 1000
);


/* =========================================================
   23. START SYSTEM WHEN PAGE LOADS
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function() {

        initializeOfflineSafety();

    }
);


/* =========================================================
   END OF ORCA OFFLINE SAFETY SYSTEM
   ========================================================= */