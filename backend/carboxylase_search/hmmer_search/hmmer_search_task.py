import os

from flask import current_app

from backend.carboxylase_search.hmmer_search.hmmer_search_use_case import run_hmmer_search_for_all_profiles
from backend.carboxylase_search.search_utils import collect_results_by_sequence, save_pdf, jsonify_hits
from backend.repository.HmmProfileRepository import HmmProfileRepository


def hmmer_search_task(file_id):
    """
        Runs an HMMER search on a user-uploaded FASTA file and processes the results.

        This function performs the following steps:
        1. Runs a HMMER search across all profiles against the input sequences.
        2. Collects and organizes the HMMER hits by sequence.
        3. Exports the search results to a PDF file for download.
        4. Prepares the search results in JSON format for API response.

        Args:
            file_id (str): Unique identifier for the uploaded FASTA file (without extension).

        Returns:
            Response: A Flask `jsonify` object containing the organized HMMER hits,
                      ready for API consumption.
        """

    hmmer_hits = run_hmmer_workflow(file_id)

    results_by_sequence = collect_results_by_sequence([hmmer_hits])

    save_pdf(file_id, results_by_sequence)

    return jsonify_hits(results_by_sequence)


def run_hmmer_workflow(file_id):
    """
        1. Loads HMM profiles from a predefined directory.
        2. Locates the input FASTA file based on the provided file ID.
        3. Runs a HMMER search across all profiles against the input sequences.
    Args:
        file_id (str): Unique identifier for the uploaded FASTA file (without extension).

    Returns:
        The compiled search results in a dictionary with the pfam accession numbers as keys and lists of HmmerSearchResult objects as values
    """
    hmm_file_location = os.path.join(current_app.config['HMMER_PROFILE_FOLDER'])
    repository = HmmProfileRepository(hmm_file_location)

    seq_file_location = os.path.join(current_app.config['UPLOADED_USER_DATA_FOLDER'], file_id + ".fasta")

    return run_hmmer_search_for_all_profiles(repository, seq_file_location)
