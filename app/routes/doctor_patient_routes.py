from flask import Blueprint, render_template, session, redirect, url_for, flash
from app import mysql

doctor_patient_bp = Blueprint(
    "doctor_patient",
    __name__
)


@doctor_patient_bp.route("/doctor/patient/<int:patient_id>")
def patient_profile(patient_id):

    # ---------------------------------
    # Check Login
    # ---------------------------------
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # ---------------------------------
    # Check Doctor Role
    # ---------------------------------
    if session.get("role") != "doctor":
        return redirect(url_for("auth.login"))

    cursor = mysql.connection.cursor()

    # ---------------------------------
    # Patient Information
    # ---------------------------------
    cursor.execute("""
        SELECT
            p.id,
            u.name,
            u.email,
            p.phone,
            p.gender,
            p.date_of_birth,
            p.address,
            p.status
        FROM patients p

        JOIN users u
            ON p.user_id = u.id

        WHERE p.id=%s
    """, (patient_id,))

    patient = cursor.fetchone()

    if not patient:
        cursor.close()

        flash("Patient not found.", "danger")

        return redirect(
            url_for("doctor_appointment.appointments")
        )

    # ---------------------------------
    # Appointment History
    # ---------------------------------
    cursor.execute("""
        SELECT
            a.id AS appointment_id,
            a.appointment_date,
            a.reason,
            a.status,
            u.name AS doctor_name

        FROM appointments a

        JOIN doctors d
            ON a.doctor_id = d.id

        JOIN users u
            ON d.user_id = u.id

        WHERE a.patient_id=%s

        ORDER BY a.appointment_date DESC
    """, (patient_id,))

    appointments = cursor.fetchall()

    # ---------------------------------
    # Consultation History
    # ---------------------------------
    cursor.execute("""
        SELECT
            a.id AS appointment_id,
            a.appointment_date,

            c.diagnosis,
            c.prescription,
            c.instructions,
            c.consultation_notes,
            c.created_at

        FROM consultation_records c

        JOIN appointments a
            ON c.appointment_id = a.id

        WHERE a.patient_id=%s

        ORDER BY a.appointment_date DESC
    """, (patient_id,))

    consultations = cursor.fetchall()

    cursor.close()

    return render_template(
        "doctor/patient_profile.html",
        patient=patient,
        appointments=appointments,
        consultations=consultations
    )