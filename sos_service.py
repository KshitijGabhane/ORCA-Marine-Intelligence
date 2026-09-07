from datetime import datetime
from database import get_db_connection
import uuid


# ==========================================
# 1. CREATE SOS
# ==========================================

def create_sos(user_id, latitude, longitude, accuracy, emergency_type):

    connection = get_db_connection()
    cursor = connection.cursor()

    # Generate unique SOS ID
    sos_id = "SOS-" + str(uuid.uuid4())[:8].upper()

    current_time = datetime.now()

    query = """
        INSERT INTO emergency_events
        (
            sos_id,
            user_id,
            latitude,
            longitude,
            accuracy,
            location_timestamp,
            emergency_type,
            status,
            location_type,
            alert_status,
            last_known_latitude,
            last_known_longitude,
            last_known_timestamp
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        sos_id,
        user_id,
        latitude,
        longitude,
        accuracy,
        current_time,
        emergency_type,
        "SOS_ACTIVE",
        "CURRENT",
        "PENDING",
        latitude,
        longitude,
        current_time
    )

    cursor.execute(query, values)

    connection.commit()

    cursor.close()
    connection.close()

    return sos_id


# ==========================================
# 2. UPDATE SOS STATUS
# ==========================================

def update_sos_status(sos_id, new_status):

    connection = get_db_connection()
    cursor = connection.cursor()

    if new_status == "EMERGENCY_RESOLVED":

        query = """
            UPDATE emergency_events
            SET status = %s,
                resolved_at = %s
            WHERE sos_id = %s
        """

        cursor.execute(
            query,
            (
                new_status,
                datetime.now(),
                sos_id
            )
        )

    else:

        query = """
            UPDATE emergency_events
            SET status = %s
            WHERE sos_id = %s
        """

        cursor.execute(
            query,
            (
                new_status,
                sos_id
            )
        )

    connection.commit()

    updated = cursor.rowcount > 0

    cursor.close()
    connection.close()

    return updated


# ==========================================
# 3. GET ALL ACTIVE SOS
# ==========================================

def get_active_sos():

    connection = get_db_connection()

    # dictionary=True gives column names
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            id,
            sos_id,
            user_id,
            latitude,
            longitude,
            accuracy,
            location_timestamp,
            emergency_type,
            status,
            location_type,
            alert_status,
            last_known_latitude,
            last_known_longitude,
            last_known_timestamp,
            created_at
        FROM emergency_events
        WHERE status NOT IN (
            'EMERGENCY_RESOLVED',
            'SOS_CANCELLED'
        )
        ORDER BY created_at DESC
    """

    cursor.execute(query)

    alerts = cursor.fetchall()

    cursor.close()
    connection.close()

    # Convert datetime objects to strings
    for alert in alerts:

        if alert["location_timestamp"]:
            alert["location_timestamp"] = \
                alert["location_timestamp"].isoformat()

        if alert["last_known_timestamp"]:
            alert["last_known_timestamp"] = \
                alert["last_known_timestamp"].isoformat()

        if alert["created_at"]:
            alert["created_at"] = \
                alert["created_at"].isoformat()

    return alerts


# ==========================================
# 4. GET ONE SOS
# ==========================================

def get_sos(sos_id):

    connection = get_db_connection()

    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            id,
            sos_id,
            user_id,
            latitude,
            longitude,
            accuracy,
            location_timestamp,
            emergency_type,
            status,
            location_type,
            alert_status,
            last_known_latitude,
            last_known_longitude,
            last_known_timestamp,
            created_at,
            resolved_at
        FROM emergency_events
        WHERE sos_id = %s
    """

    cursor.execute(query, (sos_id,))

    sos = cursor.fetchone()

    cursor.close()
    connection.close()

    if sos:

        if sos["location_timestamp"]:
            sos["location_timestamp"] = \
                sos["location_timestamp"].isoformat()

        if sos["last_known_timestamp"]:
            sos["last_known_timestamp"] = \
                sos["last_known_timestamp"].isoformat()

        if sos["created_at"]:
            sos["created_at"] = \
                sos["created_at"].isoformat()

        if sos["resolved_at"]:
            sos["resolved_at"] = \
                sos["resolved_at"].isoformat()

    return sos


# ==========================================
# 5. UPDATE SOS LOCATION
# ==========================================

def update_sos_location(
    sos_id,
    latitude,
    longitude,
    accuracy
):

    connection = get_db_connection()

    cursor = connection.cursor()

    current_time = datetime.now()

    query = """
        UPDATE emergency_events
        SET
            latitude = %s,
            longitude = %s,
            accuracy = %s,
            location_timestamp = %s,
            location_type = %s,
            last_known_latitude = %s,
            last_known_longitude = %s,
            last_known_timestamp = %s
        WHERE sos_id = %s
    """

    values = (
        latitude,
        longitude,
        accuracy,
        current_time,
        "CURRENT",
        latitude,
        longitude,
        current_time,
        sos_id
    )

    cursor.execute(query, values)

    connection.commit()

    updated = cursor.rowcount > 0

    cursor.close()
    connection.close()

    return updated