"""Main module for handling web server operations.

This module sets up a Flask application to handle various web requests, including file uploads and data processing.
CORS is enabled for all origins to allow cross-origin requests.

"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from backend.carboxylase_search.hmmer.hmmer_search_use_case import run_hmmer_workflow_for_all_profiles
from backend.repository.HmmProfileRepository import HmmProfileRepository

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))[:-7]

def create_app():
    """
        necessary for tests.
    """
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['BASE_DIR'] = BASE_DIR

    CORS(app, resources={r"/*": {"origins": "*"}})
    return app


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/validate-fasta", methods=['POST'])
def validate_fasta():
    is_valid = True
    return jsonify(is_valid)


@app.route("/hmmer-search", methods=['POST'])
def hmmer_search():
    hmm_file_location = os.path.join(BASE_DIR, "resources/carboxylases/hmmers2")
    repository = HmmProfileRepository(hmm_file_location)
    seq_file_location = os.path.join(BASE_DIR, "backend/carboxylase_search/data-acquisition/out/ERZ477576_FASTA_predicted_cds.faa.gz")
    save_file_location = os.path.join(BASE_DIR, "backend/carboxylase_search/data-acquisition/out")
    run_hmmer_workflow_for_all_profiles(repository, seq_file_location, save_file_location)
    return jsonify(True)


if __name__ == '__main__':
    create_app()
    app.run(debug=True)
