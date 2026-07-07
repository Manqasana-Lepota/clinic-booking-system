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

    # Total Doctors
    cursor.execute("SELECT COUNT(*) AS total FROM users WHERE role='doctor'")
    doctors = cursor.fetchone()['total']

     # Total Patients
    cursor.execute("SELECT COUNT(*) AS total FROM users WHERE role='patient'")
    patients = cursor.fetchone()['total']

    # Total Appointments (Temporary)
    appointments = 0

    # Today's Appointments (Temporary)
    today = 0

    cursor.close()

    return render_template(
        "admin/dashboard.html",
        doctors=doctors,
        patients=patients,
        appointments=appointments,
        today=today
    )