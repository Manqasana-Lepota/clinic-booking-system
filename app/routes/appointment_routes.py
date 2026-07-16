from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app import mysql
from flask import jsonify

appointment_bp = Blueprint('appointment', __name__)


@appointment_bp.route('/admin/appointments')
def appointments():

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    cursor = mysql.connection.cursor()

    # -----------------------------------------
    # Count Total Records
    # -----------------------------------------
    cursor.execute("""
        SELECT COUNT(*) AS total

        FROM appointments a

        JOIN patients p
            ON a.patient_id = p.id

        JOIN users u_patient
            ON p.user_id = u_patient.id

        JOIN doctors d
            ON a.doctor_id = d.id

        JOIN users u_doctor
            ON d.user_id = u_doctor.id

        WHERE
            u_patient.name LIKE %s
            OR u_doctor.name LIKE %s
            OR a.status LIKE %s
    """, (
        f"%{search}%",
        f"%{search}%",
        f"%{search}%"
    ))

    total = cursor.fetchone()['total']

    # -----------------------------------------
    # Load Appointments
    # -----------------------------------------
    cursor.execute("""
        SELECT
            a.id AS appointment_id,
            u_patient.name AS patient_name,
            u_doctor.name AS doctor_name,
            ds.day,
            ds.start_time,
            ds.end_time,
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

        JOIN doctor_schedule ds
            ON a.schedule_id = ds.schedule_id

        WHERE
            u_patient.name LIKE %s
            OR u_doctor.name LIKE %s
            OR a.status LIKE %s

        ORDER BY a.appointment_date DESC

        LIMIT %s OFFSET %s
    """, (
        f"%{search}%",
        f"%{search}%",
        f"%{search}%",
        per_page,
        offset
    ))

    appointments = cursor.fetchall()

    cursor.close()

    total_pages = (total + per_page - 1) // per_page

    return render_template(
    "appointments/index.html",
    appointments=appointments,
    search=search,
    page=page,
    total_pages=total_pages,
    total=total
)

@appointment_bp.route('/admin/get-schedules/<int:doctor_id>')
def get_schedules(doctor_id):

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
        WHERE doctor_id = %s
        AND status = 'Available'
        ORDER BY FIELD(
            day,
            'Monday',
            'Tuesday',
            'Wednesday',
            'Thursday',
            'Friday',
            'Saturday',
            'Sunday'
        )
    """, (doctor_id,))

    schedules = cursor.fetchall()

    cursor.close()

    result = []

    for schedule in schedules:

        result.append({
            "schedule_id": schedule["schedule_id"],
            "day": schedule["day"],
            "start_time": str(schedule["start_time"]),
            "end_time": str(schedule["end_time"])
        })

    return jsonify(result)


@appointment_bp.route('/admin/appointments/add', methods=['GET', 'POST'])
def add_appointment():

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    cursor = mysql.connection.cursor()

    if request.method == 'POST':

        patient_id = request.form['patient_id']
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
                reason
            )

            VALUES (%s, %s, %s, %s, %s)
        """, (
            patient_id,
            doctor_id,
            schedule_id,
            appointment_date,
            reason
        ))

        mysql.connection.commit()

        cursor.close()

        flash("Appointment booked successfully!", "success")

        return redirect(url_for('appointment.appointments'))

    # ----------------------------
    # Load Patients
    # ----------------------------
    cursor.execute("""
        SELECT
            p.id,
            u.name
        FROM patients p
        JOIN users u
            ON p.user_id = u.id
        WHERE p.status='Active'
        ORDER BY u.name
    """)
    patients = cursor.fetchall()

    # ----------------------------
    # Load Doctors
    # ----------------------------
    cursor.execute("""
        SELECT
            d.id,
            u.name
        FROM doctors d
        JOIN users u
            ON d.user_id = u.id
        WHERE d.status='Active'
        ORDER BY u.name
    """)
    doctors = cursor.fetchall()

    cursor.close()

    return render_template(
        "appointments/add.html",
        patients=patients,
        doctors=doctors
    )


@appointment_bp.route('/admin/appointments/view/<int:appointment_id>')
def view_appointment(appointment_id):

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT
            a.id,
            u_patient.name AS patient_name,
            u_patient.email AS patient_email,
            p.phone AS patient_phone,

            u_doctor.name AS doctor_name,
            d.speciality,

            ds.day,
            ds.start_time,
            ds.end_time,

            a.appointment_date,
            a.reason,
            a.status,
            a.created_at

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

        WHERE a.id = %s
    """, (appointment_id,))

    appointment = cursor.fetchone()

    cursor.close()

    if not appointment:

        flash("Appointment not found.", "danger")

        return redirect(url_for('appointment.appointments'))

    return render_template(
        "appointments/view.html",
        appointment=appointment
    )


@appointment_bp.route('/admin/appointments/edit/<int:appointment_id>', methods=['GET', 'POST'])
def edit_appointment(appointment_id):

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    cursor = mysql.connection.cursor()

    if request.method == 'POST':

        patient_id = request.form['patient_id']
        doctor_id = request.form['doctor_id']
        schedule_id = request.form['schedule_id']
        appointment_date = request.form['appointment_date']
        reason = request.form['reason']
        status = request.form['status']

        cursor.execute("""
            UPDATE appointments
            SET
                patient_id=%s,
                doctor_id=%s,
                schedule_id=%s,
                appointment_date=%s,
                reason=%s,
                status=%s
            WHERE id=%s
        """, (
            patient_id,
            doctor_id,
            schedule_id,
            appointment_date,
            reason,
            status,
            appointment_id
        ))

        mysql.connection.commit()

        cursor.close()

        flash("Appointment updated successfully!", "success")

        return redirect(url_for('appointment.appointments'))

    cursor.execute("""
        SELECT *
        FROM appointments
        WHERE id=%s
    """, (appointment_id,))

    appointment = cursor.fetchone()

    cursor.execute("""
        SELECT
            p.id,
            u.name
        FROM patients p
        JOIN users u
            ON p.user_id=u.id
        WHERE p.status='Active'
        ORDER BY u.name
    """)
    patients = cursor.fetchall()

    cursor.execute("""
        SELECT
            d.id,
            u.name
        FROM doctors d
        JOIN users u
            ON d.user_id=u.id
        WHERE d.status='Active'
        ORDER BY u.name
    """)
    doctors = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM doctor_schedule
        WHERE doctor_id=%s
        AND status='Available'
    """, (appointment['doctor_id'],))

    schedules = cursor.fetchall()

    cursor.close()

    return render_template(
        "appointments/edit.html",
        appointment=appointment,
        patients=patients,
        doctors=doctors,
        schedules=schedules
    )


@appointment_bp.route('/admin/appointments/cancel/<int:appointment_id>')
def cancel_appointment(appointment_id):

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    cursor = mysql.connection.cursor()

    cursor.execute("""
        UPDATE appointments
        SET status='Cancelled'
        WHERE id=%s
    """, (appointment_id,))

    mysql.connection.commit()

    cursor.close()

    flash(
        "Appointment cancelled successfully!",
        "success"
    )

    return redirect(
        url_for('appointment.appointments')
    )