from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from werkzeug.security import check_password_hash, generate_password_hash
from app import mysql
from flask import jsonify

patient_dashboard_bp = Blueprint(
    "patient_dashboard",
    __name__
)


@patient_dashboard_bp.route("/patient/dashboard")
def dashboard():

    # Check login
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # Check role
    if session.get("role") != "patient":
        return redirect(url_for("auth.login"))

    cursor = mysql.connection.cursor()

    # Get patient profile
    cursor.execute("""
        SELECT id
        FROM patients
        WHERE user_id = %s
    """, (session["user_id"],))

    patient = cursor.fetchone()

    if not patient:
        cursor.close()
        return redirect(url_for("auth.logout"))

    patient_id = patient["id"]

    # Total appointments
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM appointments
        WHERE patient_id = %s
    """, (patient_id,))

    total_appointments = cursor.fetchone()["total"]

    # Upcoming appointments
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM appointments
        WHERE patient_id = %s
        AND appointment_date >= CURDATE()
    """, (patient_id,))

    upcoming = cursor.fetchone()["total"]

    # Completed appointments
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM appointments
        WHERE patient_id = %s
        AND status = 'Completed'
    """, (patient_id,))

    completed = cursor.fetchone()["total"]

    # Pending appointments
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM appointments
        WHERE patient_id = %s
        AND status = 'Pending'
    """, (patient_id,))

    pending = cursor.fetchone()["total"]

    cursor.close()

    return render_template(
        "patient/dashboard.html",
        total_appointments=total_appointments,
        upcoming=upcoming,
        completed=completed,
        pending=pending
    )


@patient_dashboard_bp.route("/patient/appointments")
def appointments():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "patient":
        return redirect(url_for("auth.login"))

    search = request.args.get("search", "")

    page = request.args.get("page", 1, type=int)

    per_page = 5

    offset = (page - 1) * per_page

    cursor = mysql.connection.cursor()

    # Get patient ID
    cursor.execute("""
        SELECT id
        FROM patients
        WHERE user_id=%s
    """, (session["user_id"],))

    patient = cursor.fetchone()

    patient_id = patient["id"]

    # Count appointments
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM appointments a
        JOIN doctors d
            ON a.doctor_id=d.id
        JOIN users u
            ON d.user_id=u.id
        WHERE a.patient_id=%s
        AND (
            u.name LIKE %s
            OR a.status LIKE %s
        )
    """, (
        patient_id,
        "%" + search + "%",
        "%" + search + "%"
    ))

    total = cursor.fetchone()["total"]

    total_pages = max((total + per_page - 1) // per_page, 1)

    # Get appointments
    cursor.execute("""
        SELECT
            a.id AS appointment_id,
            u.name AS doctor_name,
            ds.day,
            ds.start_time,
            ds.end_time,
            a.appointment_date,
            a.reason,
            a.status

        FROM appointments a

        JOIN doctors d
            ON a.doctor_id=d.id

        JOIN users u
            ON d.user_id=u.id

        JOIN doctor_schedule ds
            ON a.schedule_id=ds.schedule_id

        WHERE a.patient_id=%s

        AND (
            u.name LIKE %s
            OR a.status LIKE %s
        )

        ORDER BY a.appointment_date DESC

        LIMIT %s OFFSET %s
    """, (
        patient_id,
        "%" + search + "%",
        "%" + search + "%",
        per_page,
        offset
    ))

    appointments = cursor.fetchall()

    cursor.close()

    return render_template(
        "patient/appointments.html",
        appointments=appointments,
        search=search,
        page=page,
        total_pages=total_pages,
        total=total
    )


@patient_dashboard_bp.route("/patient/appointments/<int:appointment_id>")
def view_appointment(appointment_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "patient":
        return redirect(url_for("auth.login"))

    cursor = mysql.connection.cursor()

    # Get logged-in patient's ID
    cursor.execute("""
        SELECT id
        FROM patients
        WHERE user_id=%s
    """, (session["user_id"],))

    patient = cursor.fetchone()

    if not patient:
        cursor.close()
        flash("Patient not found.", "danger")
        return redirect(url_for("patient_dashboard.appointments"))

    patient_id = patient["id"]

    # Get appointment (only if it belongs to this patient)
    cursor.execute("""
        SELECT
            a.id AS appointment_id,
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
        AND a.patient_id=%s
    """, (appointment_id, patient_id))

    appointment = cursor.fetchone()

    cursor.close()

    if not appointment:
        flash("Appointment not found.", "danger")
        return redirect(url_for("patient_dashboard.appointments"))

    return render_template(
        "patient/view_appointment.html",
        appointment=appointment
    )


@patient_dashboard_bp.route('/patient/book-appointment', methods=['GET', 'POST'])
def book_appointment():

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if session.get('role') != 'patient':
        return redirect(url_for('auth.login'))

    cursor = mysql.connection.cursor()

    # Get patient ID
    cursor.execute("""
        SELECT id
        FROM patients
        WHERE user_id=%s
    """, (session['user_id'],))

    patient = cursor.fetchone()

    if not patient:
        cursor.close()
        flash('Patient profile not found.', 'danger')
        return redirect(url_for('auth.login'))

    patient_id = patient['id']

    # Load doctors
    cursor.execute("""
        SELECT
            d.id,
            u.name
        FROM doctors d
        JOIN users u
            ON d.user_id = u.id
        ORDER BY u.name
    """)

    doctors = cursor.fetchall()

    if request.method == 'POST':

        doctor_id = request.form['doctor_id']
        schedule_id = request.form['schedule_id']
        appointment_date = request.form['appointment_date']
        reason = request.form['reason']

        cursor.execute("""
            INSERT INTO appointments
            (
                patient_id,
                doctor_id,
                schedule_id,
                appointment_date,
                reason,
                status
            )
            VALUES (%s, %s, %s, %s, %s, 'Pending')
        """, (
            patient_id,
            doctor_id,
            schedule_id,
            appointment_date,
            reason
        ))

        mysql.connection.commit()
        cursor.close()

        flash('Appointment booked successfully!', 'success')

        return redirect(url_for('patient_dashboard.appointments'))

    cursor.close()

    return render_template(
        'patient/book_appointment.html',
        doctors=doctors
    )


@patient_dashboard_bp.route('/patient/get-schedules/<int:doctor_id>')
def get_schedules(doctor_id):
    print(f"Doctor ID received: {doctor_id}")

    if 'user_id' not in session:
        return jsonify([])

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT
            schedule_id,
            day,
            start_time,
            end_time
        FROM doctor_schedule
        WHERE doctor_id=%s
        AND status='Available'
        ORDER BY FIELD(day,
            'Monday',
            'Tuesday',
            'Wednesday',
            'Thursday',
            'Friday',
            'Saturday',
            'Sunday')
    """, (doctor_id,))

    schedules = cursor.fetchall()

    # Convert time objects to strings
    result = []

    for s in schedules:
        result.append({
            'schedule_id': s['schedule_id'],
            'day': s['day'],
            'start_time': str(s['start_time']),
            'end_time': str(s['end_time'])
        })

    cursor.close()

    return jsonify(result)


@patient_dashboard_bp.route("/patient/appointment/<int:appointment_id>/cancel")
def cancel_appointment(appointment_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "patient":
        return redirect(url_for("auth.login"))

    cursor = mysql.connection.cursor()

    # Get patient ID
    cursor.execute("""
        SELECT id
        FROM patients
        WHERE user_id=%s
    """, (session["user_id"],))

    patient = cursor.fetchone()

    # Cancel only the logged-in patient's pending appointment
    cursor.execute("""
        UPDATE appointments
        SET status='Cancelled'
        WHERE id=%s
        AND patient_id=%s
        AND status='Pending'
    """, (
        appointment_id,
        patient["id"]
    ))

    mysql.connection.commit()

    cursor.close()

    flash("Appointment cancelled successfully.", "success")

    return redirect(url_for("patient_dashboard.appointments"))

@patient_dashboard_bp.route("/patient/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "patient":
        return redirect(url_for("auth.login"))

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT
            u.name,
            u.email,
            p.phone,
            p.gender,
            p.date_of_birth,
            p.address
        FROM users u
        JOIN patients p
            ON u.id = p.user_id
        WHERE u.id = %s
    """, (session["user_id"],))

    patient = cursor.fetchone()

    cursor.close()

    return render_template(
        "patient/profile.html",
        patient=patient
    )


@patient_dashboard_bp.route("/patient/profile/edit", methods=["GET", "POST"])
def edit_profile():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "patient":
        return redirect(url_for("auth.login"))

    cursor = mysql.connection.cursor()

    if request.method == "POST":

        phone = request.form["phone"]
        address = request.form["address"]

        cursor.execute("""
            UPDATE patients
            SET
                phone=%s,
                address=%s
            WHERE user_id=%s
        """, (
            phone,
            address,
            session["user_id"]
        ))

        mysql.connection.commit()

        flash("Profile updated successfully.", "success")

        cursor.close()

        return redirect(url_for("patient_dashboard.profile"))

    cursor.execute("""
        SELECT
            u.name,
            u.email,
            p.phone,
            p.gender,
            p.date_of_birth,
            p.address
        FROM users u
        JOIN patients p
            ON u.id=p.user_id
        WHERE u.id=%s
    """, (session["user_id"],))

    patient = cursor.fetchone()

    cursor.close()

    return render_template(
        "patient/edit_profile.html",
        patient=patient
    )


@patient_dashboard_bp.route("/patient/change-password", methods=["GET", "POST"])
def change_password():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "patient":
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT password
            FROM users
            WHERE id=%s
        """, (session["user_id"],))

        user = cursor.fetchone()

        if not check_password_hash(user["password"], current_password):

            flash("Current password is incorrect.", "danger")

            cursor.close()

            return redirect(url_for("patient_dashboard.change_password"))

        if new_password != confirm_password:

            flash("New passwords do not match.", "danger")

            cursor.close()

            return redirect(url_for("patient_dashboard.change_password"))

        hashed_password = generate_password_hash(new_password)

        cursor.execute("""
            UPDATE users
            SET password=%s
            WHERE id=%s
        """, (
            hashed_password,
            session["user_id"]
        ))

        mysql.connection.commit()

        cursor.close()

        flash("Password changed successfully.", "success")

        return redirect(url_for("patient_dashboard.profile"))

    return render_template("patient/change_password.html")