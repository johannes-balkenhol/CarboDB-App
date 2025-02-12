from backend.carboxylase_search.prosite_scan.prosite_scan_utils import run_ps_scan_wit_custom_profile
from backend.repository.PrositePatternRepository import PrositePatternRepository

base_dir_ = "/home/eva/PycharmProjects/Carboxylase_Server/"
seq_file_location_ = "/home/eva/PycharmProjects/Carboxylase_Server/backend/carboxylase_search/data_acquisition/out/PF00016_hits.fasta"


def run_prosite_scan_workflow_for_all_patterns(repository, base_dir, seq_file_location):
    patterns = repository.get_all_patterns()
    for pattern in patterns:
        output_file_name = pattern
        run_ps_scan_wit_custom_profile(base_dir, seq_file_location, pattern, output_file_name)






repository = PrositePatternRepository()
run_prosite_scan_workflow_for_all_patterns(repository, base_dir_, seq_file_location_)