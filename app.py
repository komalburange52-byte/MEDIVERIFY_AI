from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from recommendation.recommender import recommend_doctors
from verification.verification_engine import verify_doctor
import mysql.connector
import os
from dotenv import load_dotenv
import secrets
import hashlib


from qr.qr_generator import generate_qr
load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "dev-only-secret-key"
)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "mediverify-development-secret"
)


def get_db_connection():
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "mediverify_ai")
    )

    return connection


@app.route("/")
def home():
    return render_template("index.html")
@app.route("/verify-doctor/<int:doctor_id>")
def verify_doctor_route(doctor_id):

    result = verify_doctor(doctor_id)

    return render_template(
        "verification_result.html",
        result=result
    )


@app.route("/test-db")
def test_db():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM doctors")
        doctor_count = cursor.fetchone()[0]

        cursor.close()
        connection.close()

        return {
            "success": True,
            "message": "MySQL connection successful",
            "doctor_count": doctor_count
        }

    except Exception as e:
        return {
            "success": False,
            "message": "Database connection failed",
            "error": str(e)
        }

@app.route("/search")
def search_doctors():

    name = request.args.get("name", "").strip()
    registration_number = request.args.get(
        "registration_number", ""
    ).strip()
    specialization = request.args.get(
        "specialization", ""
    ).strip()
    location = request.args.get(
        "location", ""
    ).strip()
    availability = request.args.get(
        "availability", ""
    ).strip()
    
    verification_status = request.args.get(
        "verification_status", ""
    ).strip()

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                id,
                doctor_name,
                registration_number,
                registration_authority,
                qualification,
                specialization,
                location,
                registration_status,
                verification_status,
                verification_source,
                verification_date,
                availability
            FROM doctors
            WHERE 1=1
        """

        parameters = []

        # Doctor name
        if name:
            query += """
                AND LOWER(doctor_name) LIKE %s
            """
            parameters.append("%" + name.lower() + "%")

        # Registration number
        if registration_number:
            query += """
                AND LOWER(registration_number) LIKE %s
            """
            parameters.append(
                "%" + registration_number.lower() + "%"
            )

        # Specialization
        if specialization:
            query += """
                AND LOWER(specialization) LIKE %s
            """
            parameters.append(
                "%" + specialization.lower() + "%"
            )

        # Location
        if location:
            query += """
                AND LOWER(location) LIKE %s
            """
            parameters.append(
                "%" + location.lower() + "%"
            )

        # Availability
        if availability:
            query += """
                AND availability = %s
            """
            parameters.append(availability)

        # Verification status
        if verification_status:
            query += """
                AND verification_status = %s
            """
            parameters.append(verification_status)

        query += """
            ORDER BY doctor_name ASC
        """

        cursor.execute(
            query,
            parameters
        )

        doctors = cursor.fetchall()

        return render_template(
            "search_results.html",
            doctors=doctors,
            name=name,
            registration_number=registration_number,
            specialization=specialization,
            location=location,
            availability=availability,
            verification_status=verification_status
        )

    except Exception as e:

        return f"""
        <h2>Search Error</h2>
        <p>{e}</p>
        """

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()
@app.route("/doctor/<int:doctor_id>")
def doctor_profile(doctor_id):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        # Get selected doctor
        cursor.execute(
            """
            SELECT
                id,
                doctor_name,
                registration_number,
                registration_authority,
                qualification,
                specialization,
                location,
                registration_status,
                verification_status,
                verification_source,
                verification_date,
                availability
            FROM doctors
            WHERE id = %s
            """,
            (doctor_id,)
        )

        doctor = cursor.fetchone()

        if doctor is None:
            return "Doctor not found", 404


        # Get other verified doctors for recommendation
        cursor.execute(
            """
            SELECT
                id,
                doctor_name,
                registration_number,
                registration_authority,
                qualification,
                specialization,
                location,
                registration_status,
                verification_status,
                verification_source,
                verification_date,
                availability
            FROM doctors
            WHERE verification_status = 'VERIFIED'
              AND id != %s
            """,
            (doctor_id,)
        )

        doctors = cursor.fetchall()


        # Generate recommendations
        recommendations = recommend_doctors(
            doctors=doctors,
            specialization=doctor["specialization"],
            location=doctor["location"],
            preference=""
        )


        # Show only top 3 recommendations
        recommendations = recommendations[:3]


        return render_template(
            "doctor_profile.html",
            doctor=doctor,
            recommendations=recommendations
        )


    except Exception as e:

        return f"""
        <h2>Database Error</h2>
        <p>{e}</p>
        """


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

@app.route("/generate-qr/<int:doctor_id>")
def generate_doctor_qr(doctor_id):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        # Get doctor
        cursor.execute(
            """
            SELECT
                id,
                doctor_name,
                verification_status
            FROM doctors
            WHERE id = %s
            """,
            (doctor_id,)
        )

        doctor = cursor.fetchone()

        if doctor is None:

            return "Doctor not found", 404

        # Verify the doctor before generating QR
        verification_result = verify_doctor(doctor_id)

        if verification_result["status"] != "VERIFIED":

            return render_template(
                "verification_result.html",
                result=verification_result
            )

        # Generate secure random token
        raw_token = secrets.token_urlsafe(32)

        # Store only the hash in database
        token_hash = hashlib.sha256(
            raw_token.encode()
        ).hexdigest()

        cursor.execute(
            """
            INSERT INTO qr_records
            (
                doctor_id,
                verification_token,
                status
            )
            VALUES
            (
                %s,
                %s,
                %s
            )
            """,
            (
                doctor_id,
                token_hash,
                "ACTIVE"
            )
        )

        connection.commit()

        # Create verification URL
        verification_url = (
            request.host_url.rstrip("/")
            + "/verify/"
            + raw_token
        )

        # QR image path
        qr_folder = os.path.join(
            app.root_path,
            "static",
            "images",
            "qr"
        )

        os.makedirs(
            qr_folder,
            exist_ok=True
        )

        qr_filename = f"doctor_{doctor_id}.png"

        qr_path = os.path.join(
            qr_folder,
            qr_filename
        )

        generate_qr(
            verification_url,
            qr_path
        )

        qr_image_url = (
            "/static/images/qr/"
            + qr_filename
        )

        return render_template(
            "qr_display.html",
            doctor=doctor,
            qr_image_url=qr_image_url,
            verification_url=verification_url
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"QR generation failed: {str(e)}", 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close() 

@app.route("/qr-verification")
def qr_verification_page():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "qr_verification_page.html"
    )                       

@app.route("/verify/<token>")
def qr_verify(token):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        token_hash = hashlib.sha256(
            token.encode()
        ).hexdigest()

        cursor.execute(
            """
            SELECT
                qr_records.id,
                qr_records.doctor_id,
                qr_records.status,
                doctors.doctor_name,
                doctors.registration_number,
                doctors.registration_authority,
                doctors.qualification,
                doctors.specialization,
                doctors.location
            FROM qr_records
            JOIN doctors
                ON qr_records.doctor_id = doctors.id
            WHERE qr_records.verification_token = %s
            AND qr_records.status = 'ACTIVE'
            ORDER BY qr_records.created_at DESC
            LIMIT 1
            """,
            (token_hash,)
        )

        record = cursor.fetchone()

        if record is None:

            return render_template(
                "qr_verification.html",
                record=None
            )

        # Check current verification status
        verification_result = verify_doctor(
            record["doctor_id"]
        )

        record["current_status"] = (
            verification_result["status"]
        )

        record["verification_message"] = (
            verification_result["message"]
        )

        record["verification_source"] = (
            verification_result.get(
                "source",
                "Controlled Demo Registry"
            )
        )

        return render_template(
            "qr_verification.html",
            record=record
        )

    except Exception as e:

        return f"QR verification failed: {str(e)}", 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

@app.route("/recommendations", methods=["GET", "POST"])
def recommendations():

    recommendations_list = []

    specialization = ""
    location = ""
    preference = ""

    searched = False

    if request.method == "POST":

        searched = True

        specialization = request.form.get(
            "specialization",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        preference = request.form.get(
            "preference",
            ""
        ).strip()

        connection = None
        cursor = None

        try:

            connection = get_db_connection()

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute(
                """
                SELECT *
                FROM doctors
                WHERE verification_status = 'VERIFIED'
                """
            )

            doctors = cursor.fetchall()

            recommendations_list = recommend_doctors(
                doctors,
                specialization,
                location,
                preference
            )

        except Exception as e:

            return f"Recommendation system error: {str(e)}", 500

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()


    return render_template(
        "recommendations.html",
        recommendations=recommendations_list,
        specialization=specialization,
        location=location,
        preference=preference,
        searched=searched
    )      

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        # Basic validation

        if not name or not email or not password:

            return render_template(
                "register.html",
                error="Please fill in all fields."
            )

        if password != confirm_password:

            return render_template(
                "register.html",
                error="Passwords do not match."
            )

        if len(password) < 6:

            return render_template(
                "register.html",
                error="Password must contain at least 6 characters."
            )

        connection = None
        cursor = None

        try:

            connection = get_db_connection()

            cursor = connection.cursor(
                dictionary=True
            )

            # Check whether email already exists

            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            existing_user = cursor.fetchone()

            if existing_user:

                return render_template(
                    "register.html",
                    error="An account with this email already exists."
                )

            # Hash password

            password_hash = generate_password_hash(
                password
            )

            # Create patient account

            cursor.execute(
                """
                INSERT INTO users
                (
                    name,
                    email,
                    password_hash,
                    role
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    name,
                    email,
                    password_hash,
                    "PATIENT"
                )
            )

            connection.commit()

            return redirect(
                url_for("login")
            )

        except Exception as e:

            if connection:
                connection.rollback()

            return render_template(
                "register.html",
                error=f"Registration failed: {str(e)}"
            )

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()


    return render_template(
        "register.html"
    )     

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template(
                "login.html",
                error="Please enter email and password."
            )

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            user = cursor.fetchone()

            if not user:
                return render_template(
                    "login.html",
                    error="Invalid email or password."
                )

            if not check_password_hash(
                user["password_hash"],
                password
            ):
                return render_template(
                    "login.html",
                    error="Invalid email or password."
                )

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            if user["role"] == "ADMIN":
              return redirect(
        url_for("admin_dashboard")
    )

              return redirect(
    url_for("dashboard")
)

        except Exception as e:

            return render_template(
                "login.html",
                error=f"Login failed: {str(e)}"
            )

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template("login.html") 

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html"
    )

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )

@app.route("/admin/dashboard")
def admin_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "ADMIN":
        return redirect(url_for("dashboard"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Total doctors
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM doctors
            """
        )
        total_doctors = cursor.fetchone()["total"]

        # Verified doctors
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM doctors
            WHERE verification_status = 'VERIFIED'
            """
        )
        verified_doctors = cursor.fetchone()["total"]

        # Doctors needing data update
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM doctors
            WHERE verification_status = 'DATA NEEDS UPDATE'
            """
        )
        update_doctors = cursor.fetchone()["total"]

        # Total verification logs
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM verification_logs
            """
        )
        total_verifications = cursor.fetchone()["total"]

        return render_template(
            "admin_dashboard.html",
            total_doctors=total_doctors,
            verified_doctors=verified_doctors,
            update_doctors=update_doctors,
            total_verifications=total_verifications
        )

    except Exception as e:
        return f"Error loading admin dashboard: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

@app.route("/admin/verification-logs")
def verification_logs():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "ADMIN":
        return redirect(url_for("dashboard"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                vl.id,
                vl.doctor_id,
                d.doctor_name,
                d.registration_number,
                vl.checked_at,
                vl.result,
                vl.source,
                vl.remarks
            FROM verification_logs vl
            JOIN doctors d
                ON vl.doctor_id = d.id
            ORDER BY vl.id DESC
            """
        )

        logs = cursor.fetchall()

        return render_template(
            "verification_logs.html",
            logs=logs
        )

    except Exception as e:
        return f"Error loading verification logs: {e}"

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()

@app.route("/admin/verification-records")
def verification_records():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "ADMIN":
        return redirect(url_for("dashboard"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id,
                doctor_name,
                registration_number,
                registration_authority,
                qualification,
                specialization,
                location,
                registration_status,
                verification_status,
                verification_source,
                verification_date,
                availability
            FROM doctors
            ORDER BY id DESC
            """
        )

        doctors = cursor.fetchall()

        return render_template(
            "verification_records.html",
            doctors=doctors
        )

    except Exception as e:
        return f"Error loading verification records: {e}"

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()    

@app.route("/admin/users")
def manage_users():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "ADMIN":
        return redirect(url_for("dashboard"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id,
                name,
                email,
                role,
                created_at
            FROM users
            ORDER BY id DESC
            """
        )

        users = cursor.fetchall()

        return render_template(
            "manage_users.html",
            users=users
        )

    except Exception as e:
        return f"Error loading users: {e}"

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()                    

@app.route("/admin/add-doctor", methods=["GET", "POST"])
def add_doctor():

    # Only logged-in admins can access this page
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "ADMIN":
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        doctor_name = request.form.get(
            "doctor_name", ""
        ).strip()

        registration_number = request.form.get(
            "registration_number", ""
        ).strip()

        registration_authority = request.form.get(
            "registration_authority", ""
        ).strip()

        qualification = request.form.get(
            "qualification", ""
        ).strip()

        specialization = request.form.get(
            "specialization", ""
        ).strip()

        location = request.form.get(
            "location", ""
        ).strip()

        availability = request.form.get(
            "availability", ""
        ).strip()

        registration_status = request.form.get(
            "registration_status", ""
        ).strip()

        # Check required fields
        if not all([
            doctor_name,
            registration_number,
            registration_authority,
            qualification,
            specialization,
            location,
            availability,
            registration_status
        ]):
            return render_template(
                "add_doctor.html",
                error="Please fill in all fields."
            )

        connection = None
        cursor = None

        try:

            connection = get_db_connection()

            cursor = connection.cursor(
                dictionary=True
            )

            # Check duplicate registration number
            cursor.execute(
                """
                SELECT id
                FROM doctors
                WHERE registration_number = %s
                """,
                (registration_number,)
            )

            existing_doctor = cursor.fetchone()

            if existing_doctor:

                return render_template(
                    "add_doctor.html",
                    error="A doctor with this registration number already exists."
                )

            # Set initial verification status
            if registration_status == "ACTIVE":
                verification_status = "VERIFIED"
            else:
                verification_status = "DATA NEEDS UPDATE"

            cursor.execute(
                """
                INSERT INTO doctors
                (
                    doctor_name,
                    registration_number,
                    registration_authority,
                    qualification,
                    specialization,
                    location,
                    registration_status,
                    verification_status,
                    verification_source,
                    verification_date,
                    availability
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    CURRENT_TIMESTAMP,
                    %s
                )
                """,
                (
                    doctor_name,
                    registration_number,
                    registration_authority,
                    qualification,
                    specialization,
                    location,
                    registration_status,
                    verification_status,
                    "Controlled Demo Registry",
                    availability
                )
            )

            connection.commit()

            return render_template(
                "add_doctor.html",
                success="Doctor added successfully."
            )

        except Exception as e:

            if connection:
                connection.rollback()

            return render_template(
                "add_doctor.html",
                error=f"Failed to add doctor: {str(e)}"
            )

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template(
        "add_doctor.html"
    )

@app.route("/admin/doctors")
def manage_doctors():

    # Only logged-in admins can access this page
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "ADMIN":
        return redirect(url_for("dashboard"))

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                id,
                doctor_name,
                registration_number,
                registration_authority,
                qualification,
                specialization,
                location,
                registration_status,
                verification_status,
                verification_source,
                verification_date,
                availability
            FROM doctors
            ORDER BY id DESC
            """
        )

        doctors = cursor.fetchall()

        return render_template(
            "manage_doctors.html",
            doctors=doctors
        )

    except Exception as e:

        return f"Failed to load doctors: {str(e)}", 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

@app.route("/admin/edit-doctor/<int:doctor_id>", methods=["GET", "POST"])
def edit_doctor(doctor_id):

    # Only logged-in admins can access this page
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "ADMIN":
        return redirect(url_for("dashboard"))

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # Get the doctor
        cursor.execute(
            """
            SELECT
                id,
                doctor_name,
                registration_number,
                registration_authority,
                qualification,
                specialization,
                location,
                registration_status,
                availability
            FROM doctors
            WHERE id = %s
            """,
            (doctor_id,)
        )

        doctor = cursor.fetchone()

        if doctor is None:
            return "Doctor not found", 404

        # Handle form submission
        if request.method == "POST":

            doctor_name = request.form.get(
                "doctor_name", ""
            ).strip()

            registration_number = request.form.get(
                "registration_number", ""
            ).strip()

            registration_authority = request.form.get(
                "registration_authority", ""
            ).strip()

            qualification = request.form.get(
                "qualification", ""
            ).strip()

            specialization = request.form.get(
                "specialization", ""
            ).strip()

            location = request.form.get(
                "location", ""
            ).strip()

            availability = request.form.get(
                "availability", ""
            ).strip()

            registration_status = request.form.get(
                "registration_status", ""
            ).strip()

            # Validate fields
            if not all([
                doctor_name,
                registration_number,
                registration_authority,
                qualification,
                specialization,
                location,
                availability,
                registration_status
            ]):

                return render_template(
                    "edit_doctor.html",
                    doctor=doctor,
                    error="Please fill in all fields."
                )

            # Check whether another doctor
            # already uses this registration number
            cursor.execute(
                """
                SELECT id
                FROM doctors
                WHERE registration_number = %s
                AND id != %s
                """,
                (
                    registration_number,
                    doctor_id
                )
            )

            duplicate = cursor.fetchone()

            if duplicate:

                return render_template(
                    "edit_doctor.html",
                    doctor=doctor,
                    error="Another doctor already uses this registration number."
                )

            # Determine verification status
            if registration_status == "ACTIVE":
                verification_status = "VERIFIED"
            else:
                verification_status = "DATA NEEDS UPDATE"

            # Update doctor
            cursor.execute(
                """
                UPDATE doctors
                SET
                    doctor_name = %s,
                    registration_number = %s,
                    registration_authority = %s,
                    qualification = %s,
                    specialization = %s,
                    location = %s,
                    registration_status = %s,
                    verification_status = %s,
                    verification_source = %s,
                    verification_date = CURRENT_TIMESTAMP,
                    availability = %s
                WHERE id = %s
                """,
                (
                    doctor_name,
                    registration_number,
                    registration_authority,
                    qualification,
                    specialization,
                    location,
                    registration_status,
                    verification_status,
                    "Controlled Demo Registry",
                    availability,
                    doctor_id
                )
            )

            connection.commit()

            return redirect(
                url_for("manage_doctors")
            )

        return render_template(
            "edit_doctor.html",
            doctor=doctor
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Failed to update doctor: {str(e)}", 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

if __name__ == "__main__":
    app.run(debug=True)