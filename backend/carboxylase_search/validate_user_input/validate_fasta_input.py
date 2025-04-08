import os
import uuid
from backend.carboxylase_search.validate_user_input.fasta_validator import is_valid_fasta
from flask import jsonify

def validate_fasta_input(file, allowed_file_extensions, uploaded_user_data_folder):
    if not file:
        return jsonify({"error": "No file provided"}), 400

    original_filename = file.filename
    ext = os.path.splitext(original_filename)[1].lower()

    if ext not in allowed_file_extensions:
        return jsonify({"error": f"Invalid file extension: {ext}"}), 400

    file_id = str(uuid.uuid4())
    filename = f"{file_id}.fasta"
    file_path = os.path.join(uploaded_user_data_folder, filename)

    try:
        file.save(file_path)

        if os.path.getsize(file_path) == 0:
            os.remove(file_path)
            return jsonify({"error": "Input is empty"}), 400

        is_valid = is_valid_fasta(file_path)

        if not is_valid == True:
            os.remove(file_path)
            return jsonify({"is_valid": is_valid})

        return jsonify({"is_valid": is_valid, "file_id": file_id})

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": "File upload and validation failed", "details": str(e)}), 500
