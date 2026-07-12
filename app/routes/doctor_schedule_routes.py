from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app import mysql


doctor_schedule_bp = Blueprint(
    'doctor_schedule',
    __name__
)


@doctor_schedule_bp.route('/doctor/schedule')
def schedule():

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if session.get('role') != 'doctor':
        return redirect(url_for('auth.login'))


    cursor = mysql.connection.cursor()


    # Get logged-in doctor's ID
    cursor.execute("""
        SELECT id
        FROM doctors
        WHERE user_id = %s
    """, (session['user_id'],))


    doctor = cursor.fetchone()


    if not doctor:
        cursor.close()
        flash("Doctor profile not found.", "danger")
        return redirect(url_for('auth.login'))


    doctor_id = doctor['id']


    # Get schedules
    cursor.execute("""
        SELECT *
        FROM doctor_schedule
        WHERE doctor_id = %s
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


    cursor.close()


    return render_template(
        "doctor/schedule.html",
        schedules=schedules
    )

@doctor_schedule_bp.route('/doctor/schedule/add', methods=['GET','POST'])
def add_schedule():

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if session.get('role') != 'doctor':
        return redirect(url_for('auth.login'))


    cursor = mysql.connection.cursor()


    cursor.execute("""
        SELECT id
        FROM doctors
        WHERE user_id=%s
    """, (session['user_id'],))


    doctor = cursor.fetchone()


    if not doctor:
        cursor.close()
        flash("Doctor profile not found.", "danger")
        return redirect(url_for('auth.login'))


    doctor_id = doctor['id']


    if request.method == 'POST':

        day = request.form['day']
        start_time = request.form['start_time']
        end_time = request.form['end_time']


        cursor.execute("""
            INSERT INTO doctor_schedule
            (
                doctor_id,
                day,
                start_time,
                end_time
            )

            VALUES(%s,%s,%s,%s)

        """,
        (
            doctor_id,
            day,
            start_time,
            end_time
        ))


        mysql.connection.commit()

        cursor.close()


        flash(
            "Schedule added successfully!",
            "success"
        )


        return redirect(
            url_for('doctor_schedule.schedule')
        )


    cursor.close()


    return render_template(
        "doctor/add_schedule.html"
    )

@doctor_schedule_bp.route('/doctor/schedule/edit/<int:schedule_id>', methods=['GET', 'POST'])
def edit_schedule(schedule_id):

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if session.get('role') != 'doctor':
        return redirect(url_for('auth.login'))

    cursor = mysql.connection.cursor()

    if request.method == 'POST':

        day = request.form['day']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        status = request.form['status']

        cursor.execute("""
            UPDATE doctor_schedule
            SET day=%s,
                start_time=%s,
                end_time=%s,
                status=%s
            WHERE schedule_id=%s
        """, (
            day,
            start_time,
            end_time,
            status,
            schedule_id
        ))

        mysql.connection.commit()

        cursor.close()

        flash(
            "Schedule updated successfully!",
            "success"
        )

        return redirect(url_for('doctor_schedule.schedule'))

    cursor.execute("""
        SELECT *
        FROM doctor_schedule
        WHERE schedule_id=%s
    """, (schedule_id,))

    schedule = cursor.fetchone()

    cursor.close()

    if not schedule:

        flash("Schedule not found.", "danger")

        return redirect(url_for('doctor_schedule.schedule'))

    return render_template(
        "doctor/edit_schedule.html",
        schedule=schedule
    )

@doctor_schedule_bp.route('/doctor/schedule/delete/<int:schedule_id>')
def delete_schedule(schedule_id):

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if session.get('role') != 'doctor':
        return redirect(url_for('auth.login'))

    cursor = mysql.connection.cursor()

    cursor.execute("""
        DELETE FROM doctor_schedule
        WHERE schedule_id=%s
    """, (schedule_id,))

    mysql.connection.commit()

    cursor.close()

    flash(
        "Schedule deleted successfully!",
        "success"
    )

    return redirect(
        url_for('doctor_schedule.schedule')
    )