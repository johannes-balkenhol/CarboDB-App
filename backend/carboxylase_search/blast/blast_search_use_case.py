from backend.carboxylase_search.blast.blast_search_utils import run_blastp


def run_blastp_workflow(seq_file_location, blast_db, output_file, num_threads, evalue, outfmt):
    run_blastp(seq_file_location, blast_db, output_file, num_threads, evalue, outfmt)

