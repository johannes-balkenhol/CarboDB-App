import re
from backend.carboxylase_search.prosite_scan.prosite_scan_utils import run_ps_scan_with_custom_profile
from backend.domain.PrositeSearchResult import PrositeSearchResult
from backend.repository.PrositePatternRepository import PrositePatternRepository

base_dir_ = "/home/eva/PycharmProjects/Carboxylase_Server/"
seq_file_location_ = "/home/eva/PycharmProjects/Carboxylase_Server/backend/carboxylase_search/data_acquisition/out/PF00016_hits.fasta"
ps_scan_output_directory = "backend/carboxylase_search/prosite_scan/output"


def run_prosite_scan_workflow_for_all_patterns(repository, base_dir, seq_file_location, ps_scan_output_directory):
    """

    Args:
        repository: PrositePatternRepository that return the prosite patterns to screen for
        base_dir: base directory where the project resides as determined dynamically in main.py
        seq_file_location: location of the file containing the sequences

    Returns:
        The compiled search results in a dictionary with the prosite accession numbers as keys and lists of PrositeSearchResult objects as values

    """

    compiled_prosite_scan_results = {}
    patterns = repository.get_all_patterns()
    for pattern in patterns:
        run_ps_scan_with_custom_profile(base_dir, seq_file_location, pattern, ps_scan_output_directory, pattern)
        current_search_result = parse_prosite_scan_output(base_dir + ps_scan_output_directory + "/" + pattern)
        compiled_prosite_scan_results.update({pattern: current_search_result})

    return compiled_prosite_scan_results




def parse_prosite_scan_output(output_file_location):
    """

    Args:
        output_file_location: The file location where the prosite output resides

    Returns:
        A list of PrositeSearchResult object or an empty list
    """

    try:
        with open(output_file_location, "r") as file:
            lines = file.readlines()
        results = [(lines[i].strip(), lines[i + 1].strip()) for i in range(0, len(lines), 2)]
        prosite_search_results = []
        for result in results:

            #parse first part
            parts1 = result[0].split(":")
            sequence_id = parts1[0].strip()[1:]
            parts2 = parts1[1].strip().split(" ", 1)
            prosite_accession = parts2[0].strip()
            prosite_name = parts2[1].strip()

            #parse second part
            parts3 = re.split(r'\s{2}', result[1])
            parts4 = re.split(r'\s-\s', parts3[0])
            start_position = parts4[0]
            end_position = parts4[1]
            pattern_sequence = parts3[1].strip()

            current_search_result = PrositeSearchResult(sequence_id, prosite_accession, prosite_name, start_position, end_position, pattern_sequence)
            prosite_search_results.append(current_search_result)

        print(f"Contents successfully parsed from {output_file_location}")
        return prosite_search_results
    except Exception as e:
        print(f"An error occurred while parsing from file {output_file_location}: {e}")
        return []


repository = PrositePatternRepository()
run_prosite_scan_workflow_for_all_patterns(repository, base_dir_,seq_file_location_,ps_scan_output_directory)