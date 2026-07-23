from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app import mysql

doctor_dashboard_bp = Blueprint(
    "doctor_dashboard",
    __name__
)


@doctor_dashboard_bp.route("/doctor/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "doctor":
        return redirect(url_for("auth.login"))

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT
            d.id AS doctor_id,
            u.name,
            u.email,
            d.phone,
            d.gender,
            d.speciality,
            d.qualification,
            d.experience,
            d.status

        FROM users u

        JOIN doctors d
            ON u.id = d.user_id

        WHERE u.id = %s
    """, (session["user_id"],))

    doctor = cursor.fetchone()

    # Total appointments
    cursor.execute("""
    SELECT COUNT(*) AS total
    FROM appointments
    WHERE doctor_id=%s
""", (doctor["doctor_id"],))

    appointments = cursor.fetchone()["total"]


# Today's appointments
    cursor.execute("""
    SELECT COUNT(*) AS total
    FROM appointments
    WHERE doctor_id=%s
    AND appointment_date = CURDATE()
""", (doctor["doctor_id"],))

    today = cursor.fetchone()["total"]


# Pending appointments
    cursor.execute("""
    SELECT COUNT(*) AS total
    FROM appointments
    WHERE doctor_id=%s
    AND status='Pending'
""", (doctor["doctor_id"],))

    pending = cursor.fetchone()["total"]


# Completed appointments
    cursor.execute("""
    SELECT COUNT(*) AS total
    FROM appointments
    WHERE doctor_id=%s
    AND status='Completed'
""", (doctor["doctor_id"],))

    completed = cursor.fetchone()["total"]


# Today's schedule
    cursor.execute("""
    SELECT
        u.name AS patient_name,
        ds.start_time,
        ds.end_time
    FROM appointments a

    JOIN patients p
        ON a.patient_id = p.id

    JOIN users u
        ON p.user_id = u.id

    JOIN doctor_schedule ds
        ON a.schedule_id = ds.schedule_id

    WHERE a.doctor_id=%s
    AND a.appointment_date = CURDATE()

    ORDER BY ds.start_time
""", (doctor["doctor_id"],))

    today_schedule = cursor.fetchall()


# Recent appointments
    cursor.execute("""
    SELECT
        a.id AS appointment_id,
        u.name AS patient_name,
        a.appointment_date,
        a.status

    FROM appointments a

    JOIN patients p
        ON a.patient_id = p.id

    JOIN users u
        ON p.user_id = u.id

    WHERE a.doctor_id=%s

    ORDER BY a.appointment_date DESC

    LIMIT 5
""", (doctor["doctor_id"],))

    recent_appointments = cursor.fetchall()

    cursor.close()
    
    return render_template(
    "doctor/dashboard.html",
    doctor=doctor,
    appointments=appointments,
    today=today,
    pending=pending,
    completed=completed,
    today_schedule=today_schedule,
    recent_appointments=recent_appointments
)


