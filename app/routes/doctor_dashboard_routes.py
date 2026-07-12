from flask import Blueprint, render_template, session, redirect, url_for
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

        # Today's appointments count
   # cursor.execute("""
    #    SELECT COUNT(*) AS total
     #   FROM appointments a
      #  WHERE a.doctor_id = %s
       # AND DATE(a.appointment_date) = CURDATE()
    #""", (doctor['doctor_id'],))

    #today_appointments = cursor.fetchone()['total']


    # Total patients
   # cursor.execute("""
    #    SELECT COUNT(DISTINCT patient_id) AS total
     #   FROM appointments
      #  WHERE doctor_id = %s
    #""", (doctor['doctor_id'],))

    #total_patients = cursor.fetchone()['total']


    # Completed appointments today
    # #cursor.execute("""
       # SELECT COUNT(*) AS total
        #FROM appointments
        #WHERE doctor_id = %s
        #AND status = 'Completed'
        #AND DATE(appointment_date) = CURDATE()
    #""", (doctor['doctor_id'],))

    #completed_today = cursor.fetchone()['total']

    cursor.close()
    
    return render_template(
        "doctor/dashboard.html",
        doctor=doctor,
        #today_appointments=today_appointments,
        #total_patients=total_patients,
       # completed_today=completed_today
)