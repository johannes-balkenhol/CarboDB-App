#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 10:51:03 2024

@author: eva
"""
from backend.carboxylase_search.hmmer_search.hmmer_search_utils import run_hmmer_search
from backend.domain.HmmerSearchResult import HmmerSearchResult


def run_hmmer_workflow_for_all_profiles(repository, seq_file_location):
    """

    Args:
        repository: HmmProfileRepository that return the file paths of the Hmm Profiles to search for
        seq_file_location: Location of the file containing the input sequences

    Returns:
        The compiled search results in a dictionary with the pfam accession numbers as keys and lists of HmmerSearchResult objects as values
    """
    hmm_profiles = repository.get_all_profiles()
    compiled_hmmer_search_results = {}

    for profile in hmm_profiles:
        sequences, hits = run_hmmer_search(profile.content, seq_file_location)
        if hits:
            current_hits = []
            for hit in hits:
                current_hits.append(HmmerSearchResult(sequence_id=hit.name.decode(), pfam_accession=profile.pfam_accession, e_value=hit.evalue, alignment=hit.domains[0].alignment))
            compiled_hmmer_search_results.update({profile.pfam_accession: current_hits})

    return compiled_hmmer_search_results


def basic_output_hmmer_results(hits):
    # Show alignment on a basic level in the command line
    for hit in hits:
        print(f"Target: {hit.name.decode()}, E-value: {hit.evalue}, Alignment: {hit.domains[0].alignment}")

