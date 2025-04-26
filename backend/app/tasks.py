import os

from flask import current_app, send_file, jsonify
from backend.app.utils import clean_user_uploads
from backend.carboxylase_search.validate_user_input.validate_fasta_task import validate_fasta_task
from backend.carboxylase_search.hmmer.hmmer_search_task import hmmer_search_task


__all__ = [
    "validate_fasta_task",
    "hmmer_search_task",
    "scheduled_cleanup_task",
    "download_results_task"
]


def scheduled_cleanup_task():
    upload_folder = current_app.config['UPLOADED_USER_DATA_FOLDER']
    ttl = current_app.config['USER_DATA_TIME_TO_LIVE']
    clean_user_uploads(upload_folder, ttl)


def download_results_task(file_id):
    filename_pdf = f"{file_id}.pdf"
    file_path_pdf = os.path.join(current_app.config['UPLOADED_USER_DATA_FOLDER_PATH'], filename_pdf)

    try:
        return send_file(file_path_pdf, mimetype='application/pdf', as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "The requested PDF was not found."}), 404
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500