import os

from flask import current_app, jsonify

from backend.carboxylase_search.export_as_pdf import export_hits_to_pdf
from backend.carboxylase_search.hmmer.hmmer_search_use_case import run_hmmer_workflow_for_all_profiles
from backend.carboxylase_search.run_all_searches import collect_results_by_sequence
from backend.repository.HmmProfileRepository import HmmProfileRepository


def hmmer_search_task(file_id):
    """
        Runs an HMMER search on a user-uploaded FASTA file and processes the results.

        This function performs the following steps:
        1. Loads HMM profiles from a predefined directory.
        2. Locates the input FASTA file based on the provided file ID.
        3. Runs a HMMER search across all profiles against the input sequences.
        4. Collects and organizes the HMMER hits by sequence.
        5. Exports the search results to a PDF file for download.
        6. Prepares the search results in JSON format for API response.

        Args:
            file_id (str): Unique identifier for the uploaded FASTA file (without extension).

        Returns:
            Response: A Flask `jsonify` object containing the organized HMMER hits,
                      ready for API consumption.
        """
    hmm_file_location = os.path.join(current_app.config['HMMER_PROFILE_FOLDER'])
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