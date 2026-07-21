from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app import mysql
from werkzeug.security import generate_password_hash, check_password_hash

# Blueprint creation
auth_bp = Blueprint('auth', __name__)

# Register route
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        cursor = mysql.connection.cursor()

        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            flash("Email is already registered. Please log in.", "warning")
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(password)

        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, hashed_password, role)
        )

        mysql.connection.commit()
        cursor.close()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('register.html')

# Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        print("Email entered:", email)
        print("Password entered:", password)

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        print("User from DB:", user)

        if user:
            print("Stored password:", user['password'])
            print("Password match:", check_password_hash(user['password'], password))

        if user and check_password_hash(user['password'], password):

            session['user_id'] = user['id']
            session['role'] = user['role']
            session['user_name'] = user['name']

            print("Login successful!")
            
            if user['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            
            elif user['role'] == 'doctor':
                return redirect(url_for('doctor_dashboard.dashboard'))
            
            elif user['role'] == 'patient':
                return redirect(url_for('patient_dashboard.dashboard'))
            
        else:
            flash("Invalid user role.", "danger")
            return redirect(url_for('auth.login'))

        flash("Invalid email or password.", "danger")

    return render_template('login.html')


# Logout route
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
