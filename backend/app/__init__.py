import os

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_cors import CORS

from .routes import main as main_blueprint
from .tasks import scheduled_cleanup_task
from backend.config import BaseConfig


def create_app(config_class=BaseConfig):
    """
        Necessary for app setup and tests.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOADED_USER_DATA_FOLDER"], exist_ok=True)
    os.makedirs(app.config["PROSITE_SCAN_OUTPUT_FOLDER"], exist_ok=True)

    def job_wrapper():
        with app.app_context():
            scheduled_cleanup_task()

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=job_wrapper, trigger='interval', hours=app.config['USER_DATA_CLEANUP_INTERVAL'])
    scheduler.start()

    app.register_blueprint(main_blueprint)

    CORS(app, resources={r"/*": {"origins": "*"}})
    return app