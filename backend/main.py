"""Main module for handling web server operations.

This module sets up a Flask application to handle various web requests, including file uploads and data processing.
CORS is enabled for all origins to allow cross-origin requests.

"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from apscheduler.schedulers.background import BackgroundScheduler
from backend.carboxylase_search.user_data_handling.clean_user_uploads_folder import clean_user_uploads
from backend.carboxylase_search.hmmer.hmmer_search_use_case import run_hmmer_workflow_for_all_profiles
from backend.carboxylase_search.validate_user_input.validate_fasta_input import validate_fasta_input
from backend.repository.HmmProfileRepository import HmmProfileRepository
from backend import run_all_searches

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))[:-7]

USER_DATA_TIME_TO_LIVE = 3600 # seconds -> 1 hour
USER_DATA_CLEANUP_INTERVAL = 24 # hours

UPLOADED_USER_DATA_FOLDER = "uploaded_user_data"
ALLOWED_FILE_EXTENSIONS = {'.fasta'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 M
MAX_CONTENT_LENGTH_STRING = "16 MB"
os.makedirs(UPLOADED_USER_DATA_FOLDER, exist_ok=True)

def create_app():
    """
        Necessary for app setup and tests.
    """
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    app.config['BASE_DIR'] = BASE_DIR

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=scheduled_cleanup, trigger='interval', hours=USER_DATA_CLEANUP_INTERVAL)
    scheduler.start()

    CORS(app, resources={r"/*": {"origins": "*"}})
    return app

def scheduled_cleanup():
    clean_user_uploads(UPLOADED_USER_DATA_FOLDER, USER_DATA_TIME_TO_LIVE)

@app.route("/validate-fasta", methods=['POST'])
def validate_fasta():
    file = request.files['file']
    return validate_fasta_input(file, ALLOWED_FILE_EXTENSIONS, UPLOADED_USER_DATA_FOLDER)

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify(error=f"The file exceeds the maximum file size of {MAX_CONTENT_LENGTH_STRING}"), 413

@app.route("/hmmer-search", methods=['POST'])
def hmmer_search():
    data = request.get_json()
    file_id = data.get('fileId')

    hmm_file_location = os.path.join(BASE_DIR, "resources/carboxylases/hmmers2")
    repository = HmmProfileRepository(hmm_file_location)

    seq_file_location = os.path.join(UPLOADED_USER_DATA_FOLDER, file_id + ".fasta")

    hmmer_hits = run_hmmer_workflow_for_all_profiles(repository, seq_file_location)

    results_by_sequence = run_all_searches.collect_results_by_sequence([hmmer_hits])

    json_ready_hits = {
        outer_key: {
            inner_key: [hit.to_dict() for hit in inner_value]
            for inner_key, inner_value in outer_value.items()
        }
        for outer_key, outer_value in results_by_sequence.items()
    }

    return jsonify(json_ready_hits)

if __name__ == '__main__':
    create_app()
    app.run(debug=True)
