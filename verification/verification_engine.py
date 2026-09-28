import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():

    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "mediverify_ai")
    )


def verify_doctor(doctor_id):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        # Get doctor profile
        cursor.execute(
            """
            SELECT
                id,
                doctor_name,
                registration_number,
                registration_authority,
                qualification,
                specialization,
                location
            FROM doctors
            WHERE id = %s
            """,
            (doctor_id,)
        )

        doctor = cursor.fetchone()

        if doctor is None:

            return {
                "success": False,
                "status": "UNABLE TO VERIFY",
                "message": "Doctor record was not found."
            }

        # Search trusted registry using registration number
        cursor.execute(
            """
            SELECT
                doctor_name,
                registration_number,
                registration_authority,
                registration_status,
                qualification,
                specialization,
                location,
                source_name,
                last_checked
            FROM trusted_registry
            WHERE registration_number = %s
            """,
            (doctor["registration_number"],)
        )

        registry = cursor.fetchone()

        # No matching registration record
        if registry is None:

            result = "UNABLE TO VERIFY"

            remarks = (
                "No matching registration record was found "
                "in the controlled demo registry."
            )

            source = "Controlled Demo Registry"

        else:

            # Compare important registration information
            name_match = (
                doctor["doctor_name"].strip().lower()
                == registry["doctor_name"].strip().lower()
            )

            authority_match = (
                doctor["registration_authority"].strip().lower()
                == registry["registration_authority"].strip().lower()
            )

            registration_match = (
                doctor["registration_number"].strip().lower()
                == registry["registration_number"].strip().lower()
            )

            # Registration exists but status is not active
            if registry["registration_status"].upper() != "ACTIVE":

                result = "DATA NEEDS UPDATE"

                remarks = (
                    "A registration record was found, but its "
                    "registration status is not currently ACTIVE."
                )

                source = registry["source_name"]

            # Registration exists and important details match
            elif (
                name_match
                and authority_match
                and registration_match
            ):

                result = "VERIFIED"

                remarks = (
                    "Registration number, doctor name, and "
                    "registration authority matched the "
                    "controlled demo registry."
                )

                source = registry["source_name"]

            else:

                result = "UNABLE TO VERIFY"

                remarks = (
                    "A registration record was found, but "
                    "important profile information did not match."
                )

                source = registry["source_name"]

        # Store verification result in verification_logs
        cursor.execute(
            """
            INSERT INTO verification_logs
            (
                doctor_id,
                checked_at,
                result,
                source,
                remarks
            )
            VALUES
            (
                %s,
                NOW(),
                %s,
                %s,
                %s
            )
            """,
            (
                doctor_id,
                result,
                source,
                remarks
            )
        )

        connection.commit()

        return {
            "success": True,
            "status": result,
            "message": remarks,
            "source": source,
            "doctor": doctor
        }

    except Exception as e:

        if connection:
            connection.rollback()

        return {
            "success": False,
            "status": "UNABLE TO VERIFY",
            "message": str(e)
        }

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()