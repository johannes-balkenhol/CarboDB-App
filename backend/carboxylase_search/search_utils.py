import os

from flask import current_app
from collections import defaultdict

from backend.carboxylase_search.export_as_pdf import export_hits_to_pdf


def save_pdf(file_id, results_by_sequence):
    filename_pdf = f"{file_id}.pdf"
    file_path_pdf = os.path.join(current_app.config['UPLOADED_USER_DATA_FOLDER'], filename_pdf)
    export_hits_to_pdf(results_by_sequence, file_path_pdf)


def jsonify_hits(results_by_sequence):
    json_ready_hits = {
        outer_key: {
            inner_key: [hit.to_dict() for hit in inner_value]
            for inner_key, inner_value in outer_value.items()
        }
        for outer_key, outer_value in results_by_sequence.items()
    }
    return json_ready_hits


def collect_results_by_sequence(dict_list):
    """
    Args:
       dict_list: list of dictionaries returned by the different searches

    Returns:
        A dictionary with sequence ids as keys and the corresponding search results as lists.
    """
    results_by_sequence = defaultdict(lambda: defaultdict(list))

    for dictionary in dict_list:
        for search_result_list in dictionary.values():
            for search_result in search_result_list:
                results_by_sequence[search_result.sequence_id][search_result.type].append(search_result)

    return results_by_sequence