from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app import mysql

doctor_appointment_bp = Blueprint(
    "doctor_appointment",
    __name__
)
@doctor_appointment_bp.route("/doctor/appointments")
def appointments():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "doctor":
        return redirect(url_for("auth.login"))

    search = request.args.get("search", "")

    page = request.args.get("page", 1, type=int)

    per_page = 5

    offset = (page - 1) * per_page

    cursor = mysql.connection.cursor()

    # Get doctor ID
    cursor.execute("""
        SELECT id
        FROM doctors
        WHERE user_id=%s
    """, (session["user_id"],))

    doctor = cursor.fetchone()

    doctor_id = doctor["id"]

    # Count appointments
    cursor.execute("""
        SELECT COUNT(*) AS total

        FROM appointments a

        JOIN patients p
            ON a.patient_id = p.id

        JOIN users u
            ON p.user_id = u.id

        WHERE a.doctor_id=%s

        AND (
            u.name LIKE %s
            OR a.status LIKE %s
        )
    """, (
        doctor_id,
        "%" + search + "%",
        "%" + search + "%"
    ))

    total = cursor.fetchone()["total"]

    total_pages = max((total + per_page - 1) // per_page, 1)

    # Get appointments
    cursor.execute("""
        SELECT

            a.id AS appointment_id,

            u.name AS patient_name,

            ds.day,

            ds.start_time,

            ds.end_time,

            a.appointment_date,

            a.reason,

            a.status

        FROM appointments a

        JOIN patients p
            ON a.patient_id = p.id

        JOIN users u
            ON p.user_id = u.id

        JOIN doctor_schedule ds
            ON a.schedule_id = ds.schedule_id

        WHERE a.doctor_id=%s

        AND (
            u.name LIKE %s
            OR a.status LIKE %s
        )

        ORDER BY a.appointment_date DESC

        LIMIT %s OFFSET %s
    """, (
        doctor_id,
        "%" + search + "%",
        "%" + search + "%",
        per_page,
        offset
    ))

    appointments = cursor.fetchall()

    cursor.close()

    return render_template(
        "doctor/appointments.html",
        appointments=appointments,
        search=search,
        page=page,
        total_pages=total_pages,
        total=total
    )


@doctor_appointment_bp.route("/doctor/appointment/<int:appointment_id>")
def view_appointment(appointment_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

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

    doctor_id = doctor["id"]

    # Fetch appointment details
    cursor.execute("""
        SELECT
            a.id AS appointment_id,
            p.id AS patient_id,
            u_patient.name AS patient_name,
            u_doctor.name AS doctor_name,
            ds.day,
            ds.start_time,
            ds.end_time,
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

        JOIN doctor_schedule ds
            ON a.schedule_id = ds.schedule_id

        WHERE a.id=%s
        AND a.doctor_id=%s
    """, (appointment_id, doctor_id))

    appointment = cursor.fetchone()

    # Get consultation record
    cursor.execute("""
    SELECT
        diagnosis,
        prescription,
        consultation_notes,
        created_at
    FROM consultation_records
    WHERE appointment_id=%s
""", (appointment_id,))

    consultation = cursor.fetchone()

    cursor.close()

    if not appointment:
        flash("Appointment not found.", "danger")
        return redirect(url_for("doctor_appointment.appointments"))

    return render_template(
        "doctor/view_appointment.html",
        appointment=appointment,
        consultation=consultation
    )

@doctor_appointment_bp.route("/doctor/appointment/<int:appointment_id>/approve")
def approve_appointment(appointment_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "doctor":
        return redirect(url_for("auth.login"))

    cursor = mysql.connection.cursor()

    # Get doctor ID
    cursor.execute("""
        SELECT id
        FROM doctors
        WHERE user_id=%s
    """, (session["user_id"],))

    doctor = cursor.fetchone()

    cursor.execute("""
        UPDATE appointments
        SET status='Approved'
        WHERE id=%s
        AND doctor_id=%s
        AND status='Pending'
    """, (
        appointment_id,
        doctor["id"]
    ))

    mysql.connection.commit()

    cursor.close()

    flash("Appointment approved successfully.", "success")

    return redirect(
        url_for(
            "doctor_appointment.view_appointment",
            appointment_id=appointment_id
        )
    )

@doctor_appointment_bp.route("/doctor/appointment/<int:appointment_id>/complete")
def complete_appointment(appointment_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "doctor":
        return redirect(url_for("auth.login"))

    cursor = mysql.connection.cursor()

    # Get doctor ID
    cursor.execute("""
        SELECT id
        FROM doctors
        WHERE user_id=%s
    """, (session["user_id"],))

    doctor = cursor.fetchone()

    cursor.execute("""
        UPDATE appointments
        SET status='Completed'
        WHERE id=%s
        AND doctor_id=%s
        AND status='Approved'
    """, (
        appointment_id,
        doctor["id"]
    ))

    mysql.connection.commit()

    cursor.close()

    flash("Appointment marked as completed.", "success")

    return redirect(
        url_for(
            "doctor_appointment.view_appointment",
            appointment_id=appointment_id
        )
    )


@doctor_appointment_bp.route("/doctor/appointment/<int:appointment_id>/cancel")
def cancel_appointment(appointment_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

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

    cursor.execute("""
        UPDATE appointments
        SET status='Cancelled'
        WHERE id=%s
        AND doctor_id=%s
        AND status='Pending'
    """, (
        appointment_id,
        doctor["id"]
    ))

    mysql.connection.commit()

    cursor.close()

    flash("Appointment cancelled successfully.", "warning")

    return redirect(
        url_for(
            "doctor_appointment.view_appointment",
            appointment_id=appointment_id
        )
    )