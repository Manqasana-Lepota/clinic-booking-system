from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from app import mysql


doctor_profile_bp = Blueprint(
    'doctor_profile',
    __name__
)


@doctor_profile_bp.route('/doctor/profile')
def profile():

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))


    if session.get('role') != 'doctor':
        return redirect(url_for('auth.login'))


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

        FROM doctors d

        JOIN users u
        ON d.user_id = u.id

        WHERE d.user_id = %s

    """, (session['user_id'],))


    doctor = cursor.fetchone()


    cursor.close()


    if not doctor:

        flash(
            "Doctor profile not found.",
            "danger"
        )

        return redirect(
            url_for('doctor_dashboard.dashboard')
        )


    return render_template(
        "doctor/profile.html",
        doctor=doctor
    )

@doctor_profile_bp.route('/doctor/profile/edit', methods=['GET','POST'])
def edit_profile():

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))


    if session.get('role') != 'doctor':
        return redirect(url_for('auth.login'))


    cursor = mysql.connection.cursor()


    # Get doctor ID

    cursor.execute("""
        SELECT id
        FROM doctors
        WHERE user_id=%s
    """,
    (session['user_id'],))


    doctor = cursor.fetchone()


    if not doctor:

        cursor.close()

        flash(
            "Doctor profile not found.",
            "danger"
        )

        return redirect(
            url_for('doctor_dashboard.dashboard')
        )


    doctor_id = doctor['id']


    if request.method == 'POST':

        phone = request.form['phone']
        qualification = request.form['qualification']
        experience = request.form['experience']


        cursor.execute("""
            UPDATE doctors

            SET phone=%s,
                qualification=%s,
                experience=%s

            WHERE id=%s

        """,
        (
            phone,
            qualification,
            experience,
            doctor_id
        ))


        mysql.connection.commit()


        cursor.close()


        flash(
            "Profile updated successfully!",
            "success"
        )


        return redirect(
            url_for('doctor_profile.profile')
        )


    cursor.execute("""
        SELECT
            phone,
            qualification,
            experience

        FROM doctors

        WHERE id=%s

    """,
    (doctor_id,))


    doctor_data = cursor.fetchone()


    cursor.close()


    return render_template(
        "doctor/edit_profile.html",
        doctor=doctor_data
    )