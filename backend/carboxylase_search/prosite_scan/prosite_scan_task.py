import os

from flask import current_app, jsonify

from backend.carboxylase_search.export_as_pdf import export_hits_to_pdf
from backend.carboxylase_search.prosite_scan.prosite_scan_use_case import run_prosite_scan_workflow_for_all_patterns
from backend.carboxylase_search.run_all_searches import collect_results_by_sequence
from backend.repository.PrositePatternRepository import PrositePatternRepository


def prosite_scan_task(file_id):
    """
        Performs a PROSITE pattern scan on a user-uploaded FASTA file and processes the results.

        This function:
        1. Loads PROSITE patterns from a repository.
        2. Locates the input FASTA file based on the provided file ID.
        3. Runs a PROSITE scan across all provided patterns against the input sequences.
        4. Collects and organizes the PROSITE hits by sequence.
        5. Exports the search results to a PDF file for download.
        6. Prepares the search results in JSON format for API response.

        Args:
            file_id (str): Unique identifier for the uploaded FASTA file (without extension).

        Returns:
            Response: A Flask `jsonify` object containing the organized PROSITE hits,
                      ready for API consumption.

    """
    repository = PrositePatternRepository()

    seq_file_location = os.path.join(current_app.config['UPLOADED_USER_DATA_FOLDER'], file_id + ".fasta")

    prosite_hits = run_prosite_scan_workflow_for_all_patterns(repository, current_app.config['BASE_DIR'], seq_file_location, current_app.config['PROSITE_SCAN_OUTPUT_FOLDER'])

    results_by_sequence = collect_results_by_sequence([prosite_hits])

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