from flask import Blueprint, render_template, session, redirect, url_for
from app import mysql

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/dashboard')
def dashboard():

    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # Check if user is admin
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    cursor = mysql.connection.cursor()

    # ---------------------------------
    # Total Doctors
    # ---------------------------------
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM users
        WHERE role='doctor'
    """)
    doctors = cursor.fetchone()['total']

    # ---------------------------------
    # Total Patients
    # ---------------------------------
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM users
        WHERE role='patient'
    """)
    patients = cursor.fetchone()['total']

    # ---------------------------------
    # Total Appointments
    # ---------------------------------
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM appointments
    """)
    appointments = cursor.fetchone()['total']

    # ---------------------------------
    # Today's Appointments
    # ---------------------------------
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM appointments
        WHERE appointment_date = CURDATE()
    """)
    today = cursor.fetchone()['total']

    # ---------------------------------
    # Pending Appointments
    # ---------------------------------
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM appointments
        WHERE status='Pending'
    """)
    pending = cursor.fetchone()['total']

    # ---------------------------------
    # Approved Appointments
    # ---------------------------------
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM appointments
        WHERE status='Approved'
    """)
    approved = cursor.fetchone()['total']

    # ---------------------------------
    # Completed Appointments
    # ---------------------------------
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM appointments
        WHERE status='Completed'
    """)
    completed = cursor.fetchone()['total']

    # ---------------------------------
    # Cancelled Appointments
    # ---------------------------------
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM appointments
        WHERE status='Cancelled'
    """)
    cancelled = cursor.fetchone()['total']


    # ---------------------------------
# Today's Schedule
# ---------------------------------
    cursor.execute("""
    SELECT
        u_patient.name AS patient_name,
        ds.start_time,
        ds.end_time

    FROM appointments a

    JOIN patients p
        ON a.patient_id = p.id

    JOIN users u_patient
        ON p.user_id = u_patient.id

    JOIN doctor_schedule ds
        ON a.schedule_id = ds.schedule_id

    WHERE a.appointment_date = CURDATE()

    ORDER BY ds.start_time
""")

    today_schedule = cursor.fetchall()

    # ---------------------------------
# Recent Appointments
# ---------------------------------
    cursor.execute("""
    SELECT
        u_patient.name AS patient_name,
        u_doctor.name AS doctor_name,
        a.appointment_date,
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

    ORDER BY a.created_at DESC

    LIMIT 5
""")

    recent_appointments = cursor.fetchall()

    cursor.close()
    return render_template(
    "admin/dashboard.html",
    doctors=doctors,
    patients=patients,
    appointments=appointments,
    today=today,
    pending=pending,
    approved=approved,
    completed=completed,
    cancelled=cancelled,
    today_schedule=today_schedule,
    recent_appointments=recent_appointments
) 