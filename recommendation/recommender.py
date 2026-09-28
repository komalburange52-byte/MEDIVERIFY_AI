def calculate_score(
    doctor,
    specialization,
    location,
    preference
):
    """
    Transparent doctor recommendation scoring.

    Weights:
    Specialization = 50%
    Location       = 25%
    Availability   = 15%
    Preference      = 10%
    """

    score = 0

    # --------------------------------
    # 1. Specialization Match - 50%
    # --------------------------------

    if specialization:

        if doctor["specialization"].lower() == specialization.lower():
            score += 50

    # --------------------------------
    # 2. Location Match - 25%
    # --------------------------------

    if location:

        if doctor["location"].lower() == location.lower():
            score += 25

    # --------------------------------
    # 3. Availability - 15%
    # --------------------------------

    availability = str(
        doctor.get("availability", "")
    ).lower()

    if availability in [
        "available",
        "yes",
        "true",
        "1"
    ]:
        score += 15

    # --------------------------------
    # 4. User Preference - 10%
    # --------------------------------

    if preference:

        preference = preference.lower()

        searchable_text = (
            str(doctor.get("doctor_name", "")) + " " +
            str(doctor.get("qualification", "")) + " " +
            str(doctor.get("specialization", "")) + " " +
            str(doctor.get("location", ""))
        ).lower()

        if preference in searchable_text:
            score += 10

    return score


def recommend_doctors(
    doctors,
    specialization,
    location,
    preference
):

    recommendations = []

    for doctor in doctors:

        # Only recommend verified doctors
        if doctor["verification_status"] != "VERIFIED":
            continue

        score = calculate_score(
            doctor,
            specialization,
            location,
            preference
        )

        doctor_copy = doctor.copy()

        doctor_copy["recommendation_score"] = score

        recommendations.append(
            doctor_copy
        )

    # Highest score first
    recommendations.sort(
        key=lambda x: x["recommendation_score"],
        reverse=True
    )

    return recommendations