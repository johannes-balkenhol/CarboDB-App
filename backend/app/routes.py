import os
from flask import Blueprint, request, current_app, jsonify, send_file

from backend.carboxylase_search.run_all_searches import collect_results_by_sequence
from backend.carboxylase_search.export_as_pdf import export_hits_to_pdf
from backend.carboxylase_search.hmmer.hmmer_search_use_case import run_hmmer_workflow_for_all_profiles
from backend.carboxylase_search.validate_user_input.validate_fasta_input import validate_fasta_input
from backend.repository.HmmProfileRepository import HmmProfileRepository


main = Blueprint('main', __name__)


@main.route("/validate-fasta", methods=['POST'])
def validate_fasta():
    file = request.files['file']
    return validate_fasta_input(file, current_app.config['ALLOWED_FILE_EXTENSIONS'], current_app.config['UPLOADED_USER_DATA_FOLDER'])


@main.errorhandler(413)
def request_entity_too_large(error):
    return jsonify(error=f"The file exceeds the maximum file size of {current_app.config['MAX_CONTENT_LENGTH_STRING']}"), 413


@main.route("/hmmer-search", methods=['POST'])
def hmmer_search():
    data = request.get_json()
    file_id = data.get('fileId')

    hmm_file_location = os.path.join(current_app.config['BASE_DIR'], "resources/carboxylases/hmmers2")
    repository = HmmProfileRepository(hmm_file_location)

    seq_file_location = os.path.join(current_app.config['UPLOADED_USER_DATA_FOLDER'], file_id + ".fasta")

    hmmer_hits = run_hmmer_workflow_for_all_profiles(repository, seq_file_location)

    results_by_sequence = collect_results_by_sequence([hmmer_hits])

    filename_pdf = f"{file_id}.pdf"
    file_path_pdf = os.path.join(current_app.config['UPLOADED_USER_DATA_FOLDER'], filename_pdf)
    export_hits_to_pdf(results_by_sequence, file_path_pdf)

    json_ready_hits = {
        outer_key: {
            inner_key: [hit.to_dict() for hit in inner_value]
            for inner_key, inner_value in outer_value.items()
        }
        for outer_key, outer_value in results_by_sequence.items()
    }

    return jsonify(json_ready_hits)


@main.route("/download-results", methods=['GET'])
def download_results():
    file_id = request.args.get('fileId')

    filename_pdf = f"{file_id}.pdf"
    file_path_pdf = os.path.join(current_app.config['UPLOADED_USER_DATA_FOLDER_PATH'], filename_pdf)

    try:
        return send_file(file_path_pdf, mimetype='application/pdf', as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "The requested PDF was not found."}), 404
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500