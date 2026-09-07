import smtplib
import os

from email.message import EmailMessage


# ============================================================
# EMAIL CONFIGURATION
# ============================================================

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

SENDER_EMAIL = os.getenv("kshitij.1251010307@vit.edu")
SENDER_PASSWORD = os.getenv("1251010307")

RESCUE_EMAIL = os.getenv("kshitijgabhnae7@gmail.com")


# ============================================================
# SEND EMERGENCY EMAIL
# ============================================================

def send_emergency_notification(
    sos_id,
    latitude,
    longitude,
    emergency_type
):

    try:

        # ----------------------------------------------------
        # Check configuration
        # ----------------------------------------------------

        if not SENDER_EMAIL:
            print("ERROR: ORCA_EMAIL is not configured")
            return False

        if not SENDER_PASSWORD:
            print("ERROR: ORCA_EMAIL_PASSWORD is not configured")
            return False

        if not RESCUE_EMAIL:
            print("ERROR: ORCA_RESCUE_EMAIL is not configured")
            return False


        # ----------------------------------------------------
        # Create email
        # ----------------------------------------------------

        message = EmailMessage()

        message["Subject"] = f"ORCA EMERGENCY ALERT - {sos_id}"

        message["From"] = SENDER_EMAIL

        message["To"] = RESCUE_EMAIL


        # ----------------------------------------------------
        # Email body
        # ----------------------------------------------------

        body = f"""
ORCA MARINE SAFETY SYSTEM
==========================

EMERGENCY ALERT

SOS ID:
{sos_id}

Emergency Type:
{emergency_type}

Location:
Latitude: {latitude}
Longitude: {longitude}

The fisherman has activated an emergency SOS.

Please check the ORCA Rescue Dashboard
and initiate the appropriate rescue response.

==========================
ORCA Emergency System
"""

        message.set_content(body)


        # ----------------------------------------------------
        # Send email
        # ----------------------------------------------------

        with smtplib.SMTP_SSL(
            SMTP_SERVER,
            SMTP_PORT
        ) as server:

            server.login(
                SENDER_EMAIL,
                SENDER_PASSWORD
            )

            server.send_message(message)


        print("================================")
        print("EMERGENCY EMAIL SENT")
        print("SOS ID:", sos_id)
        print("Emergency:", emergency_type)
        print("To:", RESCUE_EMAIL)
        print("================================")


        return True


    except Exception as e:

        print("================================")
        print("EMAIL ALERT FAILED")
        print("ERROR:", str(e))
        print("================================")

        return False