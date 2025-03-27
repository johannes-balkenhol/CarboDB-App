"""Main module for handling web server operations.

This module sets up a Flask application to handle various web requests, including file uploads and data processing.
CORS is enabled for all origins to allow cross-origin requests.

"""
import tempfile
import uuid
from dataclasses import asdict

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from backend.carboxylase_search.hmmer.hmmer_search_use_case import run_hmmer_workflow_for_all_profiles
from backend.carboxylase_search.validate_user_input.fasta_validator import is_valid_fasta
from backend.repository.HmmProfileRepository import HmmProfileRepository

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))[:-7]
UPLOADED_USER_DATA = "uploaded_user_data"
os.makedirs(UPLOADED_USER_DATA, exist_ok=True)

def create_app():
    """
        necessary for tests.
    """
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['BASE_DIR'] = BASE_DIR

    CORS(app, resources={r"/*": {"origins": "*"}})
    return app


@app.route("/validate-fasta", methods=['POST'])
def validate_fasta():
    file = request.files['file']
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOADED_USER_DATA, file_id + ".fasta")
    file.save(file_path)

    is_valid = is_valid_fasta(file_path)
    print("is valide: "+ is_valid+ " File Path: "+file_path)

    if not is_valid == True:
        os.remove(file_path)
        return jsonify({"is_valid": is_valid})

    return jsonify({"is_valid": is_valid, "file_id": file_id})


@app.route("/hmmer-search", methods=['POST'])
def hmmer_search():
    hmm_file_location = os.path.join(BASE_DIR, "resources/carboxylases/hmmers2")
    repository = HmmProfileRepository(hmm_file_location)
    seq_file_location = os.path.join(BASE_DIR, "backend/carboxylase_search/data_acquisition/out/ERZ477576_FASTA_predicted_cds.faa.gz")
    save_file_location = os.path.join(BASE_DIR, "backend/carboxylase_search/data_acquisition/out")
    best_hits = run_hmmer_workflow_for_all_profiles(repository, seq_file_location, save_file_location)
    serialized_hits = [asdict(obj) for obj in best_hits]
    return jsonify(serialized_hits)


if __name__ == '__main__':
    create_app()
    app.run(debug=True)
