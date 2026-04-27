from flask import Blueprint, render_template, request, redirect, url_for, session
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

        hash_password = generate_password_hash(password)

        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, hash_password, role)
        )
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('auth_login'))
    
    return render_template('register.html')

# Login route
@auth_bp.route('/login', methods=['GET', 'POST'] )
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']

            if user['role'] == 'admin':
                return "Admin Dashboard"
            elif user['role'] == 'doctor':
                return "Doctor Dashboard"
            else:
                return "Patient Dashboard"
            
        return "Invalid credentials"
    
    return render_template('login.html')


# Logout route
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
