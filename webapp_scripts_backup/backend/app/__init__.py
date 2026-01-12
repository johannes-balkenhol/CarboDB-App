"""
CarboxyPred Flask Application Factory
"""

import os
from flask import Flask
from flask_cors import CORS

from apscheduler.schedulers.background import BackgroundScheduler

from .routes import main as main_blueprint
from .db_routes import db_bp
from .tasks import scheduled_cleanup_task
from backend.config import BaseConfig


def create_app(config_class=BaseConfig):
    """
    Application factory for CarboxyPred
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Create necessary directories
    os.makedirs(app.config.get("UPLOADED_USER_DATA_FOLDER", "/tmp/uploads"), exist_ok=True)
    os.makedirs(app.config.get("PROSITE_SCAN_OUTPUT_FOLDER", "/tmp/prosite"), exist_ok=True)

    # Setup scheduled cleanup task
    def job_wrapper():
        with app.app_context():
            scheduled_cleanup_task()

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=job_wrapper, 
        trigger='interval', 
        hours=app.config.get('USER_DATA_CLEANUP_INTERVAL', 24)
    )
    scheduler.start()

    # Register blueprints
    app.register_blueprint(main_blueprint)
    app.register_blueprint(db_bp)

    # Enable CORS
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    return app
