from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app import mysql

doctor_consultation_bp = Blueprint(
    "doctor_consultation",
    __name__
)


@doctor_consultation_bp.route(
    "/doctor/consultation/<int:appointment_id>",
    methods=["GET", "POST"]
)
def consultation(appointment_id):

    # Check login
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # Check role
    if session.get("role") != "doctor":
        return redirect(url_for("auth.login"))

    cursor = mysql.connection.cursor()

    # Get logged-in doctor's ID
    cursor.execute("""
        SELECT id
        FROM doctors
        WHERE user_id=%s
    """, (session["user_id"],))

    doctor = cursor.fetchone()

    if not doctor:
        cursor.close()
        flash("Doctor not found.", "danger")
        return redirect(url_for("auth.login"))

    doctor_id = doctor["id"]

    # -----------------------------
    # Save Consultation
    # -----------------------------
    if request.method == "POST":

        diagnosis = request.form["diagnosis"]
        prescription = request.form["prescription"]
        instructions = request.form["instructions"]
        consultation_notes = request.form["consultation_notes"]

        # Check if consultation already exists
        cursor.execute("""
            SELECT id
            FROM consultation_records
            WHERE appointment_id=%s
        """, (appointment_id,))

        existing = cursor.fetchone()

        if existing:
            cursor.close()

            flash(
                "Consultation has already been recorded.",
                "warning"
            )

            return redirect(
                url_for(
                    "doctor_appointment.view_appointment",
                    appointment_id=appointment_id
                )
            )

        # Save consultation
        cursor.execute("""
            INSERT INTO consultation_records
            (
                appointment_id,
                diagnosis,
                prescription,
                instructions,
                consultation_notes
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            appointment_id,
            diagnosis,
            prescription,
            instructions,
            consultation_notes
        ))

        # Mark appointment as completed
        cursor.execute("""
            UPDATE appointments
            SET status='Completed'
            WHERE id=%s
        """, (appointment_id,))

        mysql.connection.commit()

        cursor.close()

        flash(
            "Consultation saved successfully.",
            "success"
        )

        return redirect(
            url_for(
                "doctor_appointment.view_appointment",
                appointment_id=appointment_id
            )
        )

    # -----------------------------
    # Load Appointment
    # -----------------------------
    cursor.execute("""
        SELECT
            a.id AS appointment_id,
            u_patient.name AS patient_name,
            u_doctor.name AS doctor_name,
            a.appointment_date,
            a.reason,
            a.status

        FROM appointments a

        JOIN patients p
            ON a.patient_id = p.id

        JOIN users u_patient
            ON p.user_id = u_patient.id

        JOIN doctors d
            ON a.doctor_id = d.id

        JOIN users u_doctor
            ON d.user_id = u_doctor.id

        WHERE a.id=%s
        AND a.doctor_id=%s
        AND a.status='Approved'
    """, (
        appointment_id,
        doctor_id
    ))

    appointment = cursor.fetchone()

    cursor.close()

    if not appointment:
        flash(
            "Appointment not found or is not approved.",
            "danger"
        )

        return redirect(
            url_for("doctor_appointment.appointments")
        )

    return render_template(
        "doctor/consultation.html",
        appointment=appointment
    )