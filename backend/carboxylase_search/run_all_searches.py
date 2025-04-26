import os.path
from collections import defaultdict


from backend.carboxylase_search.prosite_scan.prosite_scan_use_case import run_prosite_scan_workflow_for_all_patterns
from backend.repository.HmmProfileRepository import HmmProfileRepository
from backend.carboxylase_search.hmmer.hmmer_search_use_case import run_hmmer_workflow_for_all_profiles
from backend.repository.PrositePatternRepository import PrositePatternRepository
from backend.carboxylase_search import export_as_pdf


seq_file_location = "/home/eva/PycharmProjects/Carboxylase_Server/backend/carboxylase_search/data_acquisition/out/PF00016_hits.fasta"

base_dir="/home/eva/PycharmProjects/Carboxylase_Server/"
base_dir_backend="/home/eva/PycharmProjects/Carboxylase_Server/backend/"

hmm_file_location = os.path.join(base_dir, "resources/carboxylases/hmm_profiles")
pdf_save_location = os.path.join(base_dir_backend, "uploaded_user_data/test.pdf")
seq_id_save_location = os.path.join(base_dir_backend, "uploaded_user_data/test.txt")
ps_scan_output_directory = "backend/carboxylase_search/prosite_scan/output"



def run_all_searches():
    repository = HmmProfileRepository(hmm_file_location)
    dict1 = run_hmmer_workflow_for_all_profiles(repository, seq_file_location)

    repository = PrositePatternRepository()
    dict2 = run_prosite_scan_workflow_for_all_patterns(repository, base_dir, seq_file_location, ps_scan_output_directory)

    dict_list_test = [dict1, dict2]
    merged_dict = collect_results_by_sequence(dict_list_test)
    required_searches = ["Pfam hits", "Prosite hits"]
    write_sequence_ids_with_all_hits(merged_dict, required_searches, seq_id_save_location)
    write_sequence_ids(merged_dict, seq_id_save_location)
    export_as_pdf.export_hits_to_pdf(merged_dict, pdf_save_location)


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

def get_sequence_ids(results_by_sequence):
    return list(results_by_sequence.keys())

def write_sequence_ids(results_by_sequence, file_path):
    with open(file_path, 'w') as f:
        for seq_id in results_by_sequence:
            f.write(f"{seq_id}\n")


def write_sequence_ids_with_all_hits(results_by_sequence, required_types, file_path):
    """
    Writes sequence IDs to a file only if they have hits for all required search types.

    Args:
        results_by_sequence: dict from collect_results_by_sequence
        required_types: list of expected search types (e.g., ["blast", "hmm", "pfam"])
        file_path: path to output file
    """
    with open(file_path, 'w') as f:
        for seq_id, type_dict in results_by_sequence.items():
            if all(search_type in type_dict and type_dict[search_type] for search_type in required_types):
                f.write(f"{seq_id}\n")