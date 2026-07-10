from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
from app import mysql

doctor_bp = Blueprint('doctor', __name__)

# Doctor route
# Doctor route with pagination
@doctor_bp.route('/admin/doctors')
def doctors():

    # Check login
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # Check admin
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))


    # Search value
    search = request.args.get('search', '')


    # Current page
    page = request.args.get('page', 1, type=int)


    # Records per page
    per_page = 10


    offset = (page - 1) * per_page


    cursor = mysql.connection.cursor()


    # Count doctors
    cursor.execute("""
        SELECT COUNT(*) AS total

        FROM doctors d

        JOIN users u
        ON d.user_id = u.id

        WHERE u.name LIKE %s
        OR d.speciality LIKE %s

    """,
    (
        f"%{search}%",
        f"%{search}%"
    ))


    total_doctors = cursor.fetchone()['total']


    # Get doctors
    cursor.execute("""
        SELECT

            d.id AS doctor_id,
            u.id AS user_id,
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


        WHERE u.name LIKE %s

        OR d.speciality LIKE %s


        ORDER BY u.name


        LIMIT %s OFFSET %s


    """,
    (
        f"%{search}%",
        f"%{search}%",
        per_page,
        offset
    ))


    doctors = cursor.fetchall()


    cursor.close()


    # Calculate pages
    total_pages = (
        total_doctors + per_page - 1
    ) // per_page


    return render_template(
        "doctors/index.html",
        doctors=doctors,
        page=page,
        total_pages=total_pages,
        search=search
    )

# Add Doctor Page
@doctor_bp.route('/admin/doctors/add', methods=['GET', 'POST'])
def add_doctor():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        gender = request.form['gender']
        speciality = request.form['speciality']
        qualification = request.form['qualification']
        experience = request.form['experience']
        password = request.form['password']
        
        cursor = mysql.connection.cursor()
        
        # Check existing email
        cursor.execute(
            "SELECT id FROM users WHERE email=%s",
            (email,)
            )
        
        existing = cursor.fetchone()

        if existing:
            cursor.close()
            
            flash(
                "Email already exists.",
                "danger"
                )
            
            return redirect(
                url_for('doctor.add_doctor')
                )
        
        # Hash password
        hashed_password = generate_password_hash(password)
        
        # Insert into users table
        cursor.execute("""
                       INSERT INTO users
                       (name,email,password,role)
                       VALUES(%s,%s,%s,%s)
                        """,
                        (
                            name,
                            email,
                            hashed_password,
                            "doctor"
                            ))
        
        # Get created user id
        user_id = cursor.lastrowid
        
        # Insert into doctors table
        cursor.execute("""
                       INSERT INTO doctors
                       (
                       user_id,
                       phone,
                       gender,
                       speciality,
                       qualification,
                       experience
                       )
                       VALUES(%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            user_id,
                            phone,
                            gender,
                            speciality,
                            qualification,
                            experience
                            ))
        mysql.connection.commit()
        
        cursor.close()
        
        flash(
            "Doctor added successfully!",
            "success"
            )
        
        return redirect(
            url_for('doctor.doctors')
            )
    # This handles GET request
    return render_template(
        "doctors/add.html"
    )


# Edit Doctor
@doctor_bp.route('/admin/doctors/edit/<int:doctor_id>', methods=['GET', 'POST'])
def edit_doctor(doctor_id):

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
        speciality = request.form['speciality']
        qualification = request.form['qualification']
        experience = request.form['experience']
        status = request.form['status']


        # Get user_id belonging to this doctor
        cursor.execute("""
            SELECT user_id
            FROM doctors
            WHERE id=%s
        """, (doctor_id,))


        doctor_user = cursor.fetchone()


        if doctor_user:


            user_id = doctor_user['user_id']


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



            # Update doctors table
            cursor.execute("""
                UPDATE doctors
                SET phone=%s,
                    gender=%s,
                    speciality=%s,
                    qualification=%s,
                    experience=%s,
                    status=%s
                WHERE id=%s
            """,
            (
                phone,
                gender,
                speciality,
                qualification,
                experience,
                status,
                doctor_id
            ))


            mysql.connection.commit()


            flash(
                "Doctor updated successfully!",
                "success"
            )


            cursor.close()


            return redirect(
                url_for('doctor.doctors')
            )



    # GET request
    cursor.execute("""
        SELECT
            d.id,
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
            ON d.user_id=u.id
        WHERE d.id=%s
    """,
    (doctor_id,))


    doctor = cursor.fetchone()


    cursor.close()


    if not doctor:

        flash(
            "Doctor not found.",
            "danger"
        )

        return redirect(
            url_for('doctor.doctors')
        )


    return render_template(
        "doctors/edit.html",
        doctor=doctor
    )

# View Doctor Profile
@doctor_bp.route('/admin/doctors/view/<int:doctor_id>')
def view_doctor(doctor_id):

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if session.get('role') != 'admin':
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

        WHERE d.id=%s

    """, (doctor_id,))


    doctor = cursor.fetchone()


    cursor.close()


    if not doctor:

        flash("Doctor not found.", "danger")

        return redirect(url_for('doctor.doctors'))


    return render_template(
        "doctors/view.html",
        doctor=doctor
    )


# Deactivate Doctor
@doctor_bp.route('/admin/doctors/deactivate/<int:doctor_id>')
def deactivate_doctor(doctor_id):

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    cursor = mysql.connection.cursor()

    cursor.execute("""
        UPDATE doctors
        SET status='Inactive'
        WHERE id=%s
    """, (doctor_id,))

    mysql.connection.commit()

    cursor.close()

    flash("Doctor deactivated successfully!", "success")

    return redirect(url_for('doctor.doctors'))