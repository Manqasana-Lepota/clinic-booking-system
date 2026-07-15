from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
from app import mysql

patient_bp = Blueprint('patient', __name__)


@patient_bp.route('/admin/patients')
def patients():

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)

    per_page = 5
    offset = (page - 1) * per_page

    cursor = mysql.connection.cursor()

    # Count total records
    cursor.execute("""
        SELECT COUNT(*)
        FROM users u
        JOIN patients p
            ON u.id = p.user_id
        WHERE
            u.name LIKE %s
            OR u.email LIKE %s
            OR p.phone LIKE %s
            OR p.gender LIKE %s
    """,
    (
        '%' + search + '%',
        '%' + search + '%',
        '%' + search + '%',
        '%' + search + '%'
    ))

    total_patients = cursor.fetchone()['COUNT(*)']

    # Fetch current page
    cursor.execute("""
        SELECT
            p.id AS patient_id,
            u.name,
            u.email,
            p.phone,
            p.gender,
            p.date_of_birth,
            p.address,
            p.status

        FROM users u
        JOIN patients p
            ON u.id = p.user_id

        WHERE
            u.name LIKE %s
            OR u.email LIKE %s
            OR p.phone LIKE %s
            OR p.gender LIKE %s

        ORDER BY u.name

        LIMIT %s OFFSET %s
    """,
    (
        '%' + search + '%',
        '%' + search + '%',
        '%' + search + '%',
        '%' + search + '%',
        per_page,
        offset
    ))

    patients = cursor.fetchall()

    cursor.close()

    total_pages = (total_patients + per_page - 1) // per_page

    return render_template(
        "patients/index.html",
        patients=patients,
        page=page,
        total_pages=total_pages,
        search=search
    )

@patient_bp.route('/admin/patients/add', methods=['GET', 'POST'])
def add_patient():

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        phone = request.form['phone']
        gender = request.form['gender']
        date_of_birth = request.form['date_of_birth']
        address = request.form['address']

        cursor = mysql.connection.cursor()

        # Check if email already exists
        cursor.execute(
            "SELECT id FROM users WHERE email=%s",
            (email,)
        )

        existing = cursor.fetchone()

        if existing:
            flash("Email already exists.", "danger")
            cursor.close()
            return redirect(url_for('patient.add_patient'))

        hashed_password = generate_password_hash(password)

        # Create user
        cursor.execute("""
            INSERT INTO users
            (name, email, password, role)
            VALUES (%s, %s, %s, %s)
        """, (
            name,
            email,
            hashed_password,
            'patient'
        ))

        user_id = cursor.lastrowid

        # Create patient profile
        cursor.execute("""
            INSERT INTO patients
            (user_id, phone, gender, date_of_birth, address)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            user_id,
            phone,
            gender,
            date_of_birth,
            address
        ))

        mysql.connection.commit()

        cursor.close()

        flash("Patient added successfully!", "success")

        return redirect(url_for('patient.patients'))

    return render_template("patients/add.html")


@patient_bp.route('/admin/patients/view/<int:patient_id>')
def view_patient(patient_id):

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))


    cursor = mysql.connection.cursor()


    cursor.execute("""
        SELECT
            p.id AS patient_id,
            u.name,
            u.email,
            p.phone,
            p.gender,
            p.date_of_birth,
            p.address,
            p.status

        FROM patients p

        JOIN users u

        ON p.user_id = u.id

        WHERE p.id=%s

    """,
    (patient_id,))


    patient = cursor.fetchone()


    cursor.close()


    if not patient:

        flash("Patient not found.", "danger")

        return redirect(
            url_for('patient.patients')
        )


    return render_template(
        "patients/view.html",
        patient=patient
    )


@patient_bp.route('/admin/patients/edit/<int:patient_id>', methods=['GET', 'POST'])
def edit_patient(patient_id):

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))


    cursor = mysql.connection.cursor()


    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']

        phone = request.form['phone']
        gender = request.form['gender']
        date_of_birth = request.form['date_of_birth']
        address = request.form['address']
        status = request.form['status']


        # Get user_id
        cursor.execute("""
            SELECT user_id
            FROM patients
            WHERE id=%s
        """,
        (patient_id,))


        patient_user = cursor.fetchone()


        if patient_user:

            user_id = patient_user['user_id']


            # Update users table

            cursor.execute("""
                UPDATE users
                SET name=%s,
                    email=%s
                WHERE id=%s
            """,
            (
                name,
                email,
                user_id
            ))



            # Update patients table

            cursor.execute("""
                UPDATE patients
                SET phone=%s,
                    gender=%s,
                    date_of_birth=%s,
                    address=%s,
                    status=%s
                WHERE id=%s
            """,
            (
                phone,
                gender,
                date_of_birth,
                address,
                status,
                patient_id
            ))


            mysql.connection.commit()


            flash(
                "Patient updated successfully!",
                "success"
            )


            cursor.close()


            return redirect(
                url_for('patient.patients')
            )



    # GET request

    cursor.execute("""
        SELECT
            p.id,
            u.name,
            u.email,
            p.phone,
            p.gender,
            p.date_of_birth,
            p.address,
            p.status

        FROM patients p

        JOIN users u

        ON p.user_id=u.id

        WHERE p.id=%s
    """,
    (patient_id,))


    patient = cursor.fetchone()


    cursor.close()



    if not patient:

        flash(
            "Patient not found.",
            "danger"
        )

        return redirect(
            url_for('patient.patients')
        )



    return render_template(
        "patients/edit.html",
        patient=patient
    )


@patient_bp.route('/admin/patients/deactivate/<int:patient_id>')
def deactivate_patient(patient_id):

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))


    cursor = mysql.connection.cursor()


    cursor.execute("""
        UPDATE patients
        SET status='Inactive'
        WHERE id=%s
    """,
    (patient_id,))


    mysql.connection.commit()


    cursor.close()


    flash(
        "Patient deactivated successfully!",
        "success"
    )


    return redirect(
        url_for('patient.patients')
    )