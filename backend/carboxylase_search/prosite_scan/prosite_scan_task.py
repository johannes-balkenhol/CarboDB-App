import os

from flask import current_app

from backend.carboxylase_search.prosite_scan.prosite_scan_use_case import run_prosite_scan_for_all_patterns
from backend.carboxylase_search.search_utils import collect_results_by_sequence, save_pdf, jsonify_hits
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

    prosite_hits = run_prosite_workflow(file_id)

    results_by_sequence = collect_results_by_sequence([prosite_hits])

    save_pdf(file_id, results_by_sequence)

    return jsonify_hits(results_by_sequence)


def run_prosite_workflow(file_id):
    """
        1. Initializes prosite pattern repository
        2. Runs a prosite scan across all profiles against the input sequences.
    Args:
        file_id (str): Unique identifier for the uploaded FASTA file (without extension).

    Returns:
        The compiled search results in a dictionary with the prosite accession numbers as keys and lists of PrositeSearchResult objects as values
    """
    repository = PrositePatternRepository()

    seq_file_location = os.path.join(current_app.config['UPLOADED_USER_DATA_FOLDER'], file_id + ".fasta")

    return run_prosite_scan_for_all_patterns(repository, current_app.config['BASE_DIR'], seq_file_location,
                                                     current_app.config['PROSITE_SCAN_OUTPUT_FOLDER'])