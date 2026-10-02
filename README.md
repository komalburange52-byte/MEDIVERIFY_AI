# MediVerify AI – Smart Doctor Verification & Recommendation Management System

MediVerify AI is a web-based doctor verification and recommendation management system developed using Flask, MySQL, Python, HTML, CSS, and JavaScript.

The system allows users to search doctor records, verify registration information against a controlled demo registry, view doctor profiles, generate secure QR verification links, and receive doctor recommendations based on specialization, location, and availability.

> **Prototype Notice:** MediVerify AI validates information against a controlled demo registry available to the application. It does not legally determine whether a person is a genuine or fake doctor.

---

## Features

### Doctor Search

Users can search doctor records using:

- Doctor name
- Registration number
- Specialization
- Location
- Availability
- Verification status

The search system displays matching doctor profiles and their current verification status.

### Doctor Verification

The system compares doctor information with records available in the controlled demo registry.

The application supports three verification outcomes:

- **VERIFIED** – Matching registration information was found and the registration status is ACTIVE.
- **UNABLE TO VERIFY** – No matching registration record was found.
- **DATA NEEDS UPDATE** – A registration record was found, but the registration status is not currently ACTIVE.

### Doctor Profiles

Each doctor has a dedicated profile containing:

- Doctor name
- Registration number
- Registration authority
- Qualification
- Specialization
- Location
- Registration status
- Verification source
- Availability

### Secure QR Verification

The system can generate a QR code for a doctor profile.

The QR code contains a secure verification URL rather than exposing the complete doctor registration information.

When the QR code is scanned, the system checks the verification token and displays the corresponding verification result.

### AI-Assisted Doctor Recommendations

MediVerify AI includes a recommendation system that recommends doctors based on:

- Specialization
- Location
- Availability
- Verification status

The recommendation system is designed to help users discover relevant doctor records from the available application data.

### Admin Dashboard

The administrator can manage system information through the admin dashboard.

Admin functionality includes:

- Doctor management
- Add doctor
- Edit doctor
- Manage users
- Verification records
- Verification logs
- Doctor search and management

### Verification Logs

The system maintains a history of verification checks.

Each verification log can contain:

- Doctor
- Registration number
- Verification status
- Verification source
- Date and time
- Verification remarks

This allows administrators to review previous verification activity.

---

## Technology Stack

### Backend

- Python
- Flask
- MySQL

### Frontend

- HTML5
- CSS3
- JavaScript
- Jinja2 Templates

### QR Verification

- Python QR code generation
- Secure verification tokens
- SHA-256 token hashing

### Recommendation System

- Python
- Rule-based recommendation logic
- Specialization matching
- Location matching
- Availability matching
- Verification status filtering

### Development Tools

- Visual Studio Code
- MySQL
- Git
- GitHub
- Python Virtual Environment

---

## System Workflow

```text
User
  |
  v
Search Doctors
  |
  v
Doctor Profile
  |
  +----------------------+
  |                      |
  v                      v
Verify Registration   Generate QR
  |                      |
  v                      v
Verification Result   Secure QR URL
  |                      |
  +----------+-----------+
             |
             v
      Verification Logs
```

---

## Verification Workflow

```text
Doctor Information
        |
        v
Controlled Demo Registry
        |
        v
Compare Registration Information
        |
        +----------------------+
        |          |           |
        v          v           v
    VERIFIED   DATA NEEDS   UNABLE TO
                UPDATE       VERIFY
```

### VERIFIED

A matching registration record is found and the registration status is `ACTIVE`.

### DATA NEEDS UPDATE

A registration record is found, but its registration status is not currently `ACTIVE`.

### UNABLE TO VERIFY

No matching registration record is found in the controlled demo registry.

---

## Sample Demo Records

The project includes controlled sample records for demonstration.

| Doctor | Registration Number | Specialization | Location | Status |
|---|---|---|---|---|
| Dr. Ananya Sharma | DEMO-MH-10001 | Dermatology | Pune | VERIFIED |
| Dr. Rahul Patil | DEMO-MH-10002 | Cardiology | Mumbai | DATA NEEDS UPDATE |
| Dr. Priya Deshmukh | DEMO-MH-99999 | Pediatrics | Solapur | UNABLE TO VERIFY |
| Dr. Demo Kulkarni | DEMO-MH-10003 | General Medicine | Mumbai | VERIFIED |

These records are intended only for application demonstration and testing.

---

## Project Structure

```text
MEDIVERVERIFY_AI/
│
├── database/
├── models/
│
├── qr/
│   ├── __init__.py
│   └── qr_generator.py
│
├── recommendation/
│   ├── __init__.py
│   └── recommender.py
│
├── static/
│
├── templates/
│   ├── add_doctor.html
│   ├── admin_dashboard.html
│   ├── dashboard.html
│   ├── doctor_profile.html
│   ├── edit_doctor.html
│   ├── index.html
│   ├── login.html
│   ├── manage_doctors.html
│   ├── manage_users.html
│   ├── qr_display.html
│   ├── qr_verification.html
│   ├── qr_verification_page.html
│   ├── recommendations.html
│   ├── register.html
│   ├── search_results.html
│   ├── verification_logs.html
│   ├── verification_records.html
│   └── verification_result.html
│
├── verification/
│   └── verification_engine.py
│
├── .env
├── .gitignore
├── app.py
├── README.md
└── requirements.txt
```

> The `venv/`, `.env`, generated QR images, cache files, and local database files are excluded from Git using `.gitignore`.

---

## Database

The application uses MySQL for storing application data.

The database contains information related to:

- Doctors
- Users
- Trusted registry records
- QR verification records
- Verification logs

The verification system compares doctor information with the controlled registry before displaying the verification result.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/komalburange52-byte/MEDIVERIFY_AI.git
```

### 2. Open the project

```bash
cd MEDIVERIFY_AI
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the virtual environment on Windows

```powershell
venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure environment variables

Create a `.env` file in the project root.

Example:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=mediverify_ai
DB_PORT=3306
```

Replace `your_mysql_password` with your local MySQL password.

> Do not upload `.env` to GitHub because it may contain sensitive database credentials.

---

## Run the Application

Activate the virtual environment:

```powershell
venv\Scripts\activate
```

Then run:

```powershell
python app.py
```

Open the application in your browser:

```text
http://127.0.0.1:5000
```

---

## Testing the Verification System

The project can be tested using the sample doctor records.

### Test 1 – VERIFIED

Search for:

```text
Doctor: Dr. Ananya Sharma
Registration: DEMO-MH-10001
```

Expected result:

```text
VERIFIED
```

### Test 2 – DATA NEEDS UPDATE

Search for:

```text
Doctor: Dr. Rahul Patil
Registration: DEMO-MH-10002
```

Expected result:

```text
DATA NEEDS UPDATE
```

### Test 3 – UNABLE TO VERIFY

Search for:

```text
Doctor: Dr. Priya Deshmukh
Registration: DEMO-MH-99999
```

Expected result:

```text
UNABLE TO VERIFY
```

### Test 4 – QR Verification

Open a doctor profile and select:

```text
Generate QR
```

Scan the generated QR code to open the secure verification URL.

---

## Security Considerations

MediVerify AI uses a secure verification-token approach for QR verification.

Instead of placing complete registration information directly inside the QR code, the QR code contains a verification URL associated with a secure token.

The verification system uses hashing to protect the stored token.

The project also excludes sensitive and local files using `.gitignore`, including:

```text
.env
venv/
*.sql
*.sqlite
*.db
```

---

## Future Enhancements

Possible future improvements include:

- Integration with an authorized medical registration API
- Real-time registry verification
- Improved recommendation algorithms
- Machine learning-based doctor recommendations
- User feedback and rating system
- Advanced admin analytics dashboard
- Verification notification system
- Email notifications
- Doctor credential document verification
- Cloud deployment
- Production database integration
- Role-based access control improvements

---

## Project Purpose

MediVerify AI was developed as an academic/prototype project to demonstrate how a web application can combine:

- Doctor information management
- Registration verification
- QR-based verification
- Recommendation systems
- Admin management
- Verification history
- MySQL database integration

The system demonstrates the technical workflow using a controlled demo registry and should not be considered a replacement for official medical registration authorities.

---

## Author

**Komal Burange**

B.Tech – Artificial Intelligence & Data Science

Fabtech Technical Campus, Sangola

---

## Disclaimer

MediVerify AI is a prototype application developed for educational and demonstration purposes.

The application validates information against a controlled demo registry available to the application. It does not legally determine whether a person is a genuine or fake doctor.

For real-world deployment, verification data should be obtained from an appropriate authorized medical registration authority or officially authorized API.