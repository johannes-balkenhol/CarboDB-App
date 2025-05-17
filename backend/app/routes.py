from flask import Blueprint, request, current_app, jsonify
from backend.app.tasks import *
from backend.carboxylase_search.run_all_searches_task import combined_search_task

main = Blueprint('main', __name__)


@main.route("/validate-fasta", methods=['POST'])
def validate_fasta():
    file = request.files['file']
    return validate_fasta_task(file, current_app.config['ALLOWED_FILE_EXTENSIONS'], current_app.config['UPLOADED_USER_DATA_FOLDER'])


@main.errorhandler(413)
def request_entity_too_large(error):
    return jsonify(error=f"The file exceeds the maximum file size of {current_app.config['MAX_CONTENT_LENGTH_STRING']}"), 413


@main.route("/hmmer-search", methods=['POST'])
def hmmer_search():
    data = request.get_json()
    file_id = data.get('fileId')
    return hmmer_search_task(file_id)


@main.route("/prosite-scan", methods=['POST'])
def prosite_scan():
    data = request.get_json()
    file_id = data.get('fileId')
    return prosite_scan_task(file_id)


@main.route("/all-searches", methods=['POST'])
def all_searches():
    data = request.get_json()
    file_id = data.get('fileId')
    return combined_search_task(file_id)


@main.route("/download-results", methods=['GET'])
def download_results():
    file_id = request.args.get('fileId')
    return download_results_task(file_id)

