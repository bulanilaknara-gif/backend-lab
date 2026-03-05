from flask import Flask
from flask_cors import CORS

from nexus.lab.routes import lab_bp
from nexus.patient.routes import patient_bp
from nexus.admin.routes import admin_bp

def create_app():
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(lab_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(admin_bp)

    return app