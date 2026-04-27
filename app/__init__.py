from flask import Flask
from flask_mysqldb import MySQL
from flask import Config

mysql = MySQL()

def create_app():
    app = Flask(__name__)

    # Load Confog from config.py
    app.config.from_object(Config)

    # MySQL Initialization
    mysql.init_app(app)

    # Register Blueprints
    from app.routes.main_routes import main_bp
    app.register_blueprint(main_bp)

    from app.routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp)

    #from app.routes.admin_routes import admin_bp
    #app.register_blueprint(admin_bp)

    #from app.routes.doctor_routes import doctor_bp
    #app.register_blueprint(doctor_bp)

    #from app.routes.patient_routes import patient_bp
    #app.register_blueprint(patient_bp)

    return app