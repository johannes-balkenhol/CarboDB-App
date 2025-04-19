from flask import current_app
from backend.app.utils import clean_user_uploads

def scheduled_cleanup():
    upload_folder = current_app.config['UPLOADED_USER_DATA_FOLDER']
    ttl = current_app.config['USER_DATA_TIME_TO_LIVE']
    clean_user_uploads(upload_folder, ttl)