from collections import defaultdict

from backend.carboxylase_search.prosite_scan.prosite_scan_use_case import run_prosite_scan_workflow_for_all_patterns
from backend.repository.HmmProfileRepository import HmmProfileRepository
from backend.carboxylase_search.hmmer.hmmer_search_use_case import run_hmmer_workflow_for_all_profiles
from backend.repository.PrositePatternRepository import PrositePatternRepository
from backend.carboxylase_search import export_as_pdf

seq_file_location = "/home/eva/PycharmProjects/Carboxylase_Server/backend/carboxylase_search/data_acquisition/out/ERZ477576_FASTA_CDS.fasta"
hmm_file_location = "/home/eva/PycharmProjects/Carboxylase_Server/resources/carboxylases/hmmers2"
pdf_save_location = "uploaded_user_data/search_results.pdf"

repository = HmmProfileRepository(hmm_file_location)
dict1 = run_hmmer_workflow_for_all_profiles(repository, seq_file_location)


base_dir_ = "/home/eva/PycharmProjects/Carboxylase_Server/"
ps_scan_output_directory = "backend/carboxylase_search/prosite_scan/output"

repository = PrositePatternRepository()
dict2 = run_prosite_scan_workflow_for_all_patterns(repository, base_dir_,seq_file_location,ps_scan_output_directory)

def collect_results_by_sequence(dict_list):
    """
    Args:
        dict_list: list of dictionaries returned by the different searches

    Returns:
        dictionary with sequence ids as keys and the corresponding found search results as lists
    """
    results_by_sequence = defaultdict(lambda: defaultdict(list))

    for dictionary in dict_list:
        for search_result_list in dictionary.values():
            for search_result in search_result_list:
                results_by_sequence[search_result.sequence_id][search_result.type].append(search_result)

    return results_by_sequence




dict_list_test = [dict1, dict2]
merged_dict = collect_results_by_sequence(dict_list_test)
export_as_pdf.export_hits_to_pdf(merged_dict, pdf_save_location)