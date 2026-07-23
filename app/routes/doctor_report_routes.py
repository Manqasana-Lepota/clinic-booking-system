from flask import Blueprint, render_template, session, redirect, url_for, flash
from app import mysql

doctor_report_bp = Blueprint(
    "doctor_report",
    __name__
)


@doctor_report_bp.route("/doctor/medical-report/<int:appointment_id>")
def medical_report(appointment_id):

    # ----------------------------
    # Check Login
    # ----------------------------
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # ----------------------------
    # Check Doctor Role
    # ----------------------------
    if session.get("role") != "doctor":
        return redirect(url_for("auth.login"))

    cursor = mysql.connection.cursor()

    # ----------------------------
    # Medical Report
    # ----------------------------
    cursor.execute("""
        SELECT

            a.id AS appointment_id,
            a.appointment_date,
            a.reason,
            a.status,

            ds.day,
            ds.start_time,
            ds.end_time,

            u_patient.name AS patient_name,
            u_patient.email AS patient_email,

            p.phone,
            p.gender,
            p.date_of_birth,
            p.address,

            u_doctor.name AS doctor_name,
            u_doctor.email AS doctor_email,

            d.speciality,
            d.qualification,
            d.experience,

            c.diagnosis,
            c.prescription,
            c.instructions,
            c.consultation_notes,
            c.created_at

        FROM appointments a

        JOIN patients p
            ON a.patient_id = p.id

        JOIN users u_patient
            ON p.user_id = u_patient.id

        JOIN doctors d
            ON a.doctor_id = d.id

        JOIN users u_doctor
            ON d.user_id = u_doctor.id

        JOIN doctor_schedule ds
            ON a.schedule_id = ds.schedule_id

        LEFT JOIN consultation_records c
            ON c.appointment_id = a.id

        WHERE a.id=%s
    """, (appointment_id,))

    report = cursor.fetchone()

    cursor.close()

    if not report:

        flash("Medical report not found.", "danger")

        return redirect(
            url_for("doctor_appointment.appointments")
        )

    return render_template(
        "doctor/medical_report.html",
        report=report
    )