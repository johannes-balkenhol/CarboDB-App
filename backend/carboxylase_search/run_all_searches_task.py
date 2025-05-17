from backend.carboxylase_search.hmmer_search.hmmer_search_task import run_hmmer_workflow
from backend.carboxylase_search.prosite_scan.prosite_scan_task import run_prosite_workflow
from backend.carboxylase_search.search_utils import collect_results_by_sequence, save_pdf, jsonify_hits


def combined_search_task(file_id):
    """
    Runs both HMMER search and PROSITE scan on a user-uploaded FASTA file, processes the results,
    and returns them in JSON format.

    Steps:
    1. Run hmmer und prosite workflow
    2. Collect and merge results by sequence.
    3. Save the merged results to a PDF.
    4. Return JSON-formatted response of the combined hits.

    Args:
        file_id (str): Unique identifier for the uploaded FASTA file.

    Returns:
        Response: A Flask `jsonify` object containing the combined HMMER and PROSITE hits.
    """
    hmmer_hits = run_hmmer_workflow(file_id)

    prosite_hits = run_prosite_workflow(file_id)

    results_by_sequence = collect_results_by_sequence([hmmer_hits, prosite_hits])

    save_pdf(file_id, results_by_sequence)

    return jsonify_hits(results_by_sequence)