#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 10:51:03 2024

@author: eva
"""

import pyhmmer
from dna_features_viewer import GraphicFeature, GraphicRecord
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import os


#Example data used link: https://www.ebi.ac.uk/metagenomics/api/v1/analyses/MGYA00383254/file/ERZ477576_FASTA_predicted_cds.faa.gz

def run_hmmer_workflow(hmm_file_location, seq_file_location, save_file_location):
    sequences, hits = run_hmmer_search(hmm_file_location, seq_file_location)
    basic_output_hmmer_results(hits)
    plot_hmmer_results(hits, sequences, save_file_location)


def run_hmmer_workflow_for_all_profiles(hmm_file_directory, seq_file_location, save_file_location):
    hmm_files = [os.path.join(hmm_file_directory, f) for f in os.listdir(hmm_file_directory) if f.endswith('.hmm')]
    best_hits = []
    for file in hmm_files:
        sequences, hits = run_hmmer_search(file, seq_file_location)
        if hits:
            best_hit = min(hits, key=lambda hit: hit.evalue)
            best_hits.append(best_hit)
            #basic_output_hmmer_results(best_hits)

    plot_hmmer_results(best_hits, sequences, save_file_location)

def run_hmmer_search(hmm_file_location, seq_file_location):
    with pyhmmer.plan7.HMMFile(hmm_file_location) as hmm_file:
        hmm = hmm_file.read()

    # Step 2: Perform HMMER search with carboxylase HMM

    with pyhmmer.easel.SequenceFile(seq_file_location, digital=True) as seq_file:
        sequences = seq_file.read_block()

    pipeline = pyhmmer.plan7.Pipeline(hmm.alphabet)
    hits = pipeline.search_hmm(hmm, sequences)
    return sequences, hits

def basic_output_hmmer_results(hits):
    # Show alignment on a basic level in the command line
    for hit in hits:
        print(f"Target: {hit.name.decode()}, E-value: {hit.evalue}, Alignment: {hit.domains[0].alignment}")

def plot_hmmer_results(hits, sequences, save_file_location):
    # Dynamically set figure height based on the number of hits
    fig_height = max(6, len(hits) * 1.5)  # 1.5 inches per hit, minimum height of 6 inches
    fig = plt.figure(figsize=(12, fig_height))

    # Use GridSpec for better control over subplot spacing
    gs = GridSpec(len(hits), 1, figure=fig, hspace=0.5)  # hspace controls vertical space between plots

    # create an index to retrieve sequences by name
    seq_index = {seq.name: seq for seq in sequences}

    for i, hit in enumerate(hits):
        ax = fig.add_subplot(gs[i])

        # add one feature per domain, with unique colors and labels
        features = [
            GraphicFeature(
                start=d.alignment.target_from - 1,
                end=d.alignment.target_to,
                color="#ffcccc" if j % 2 == 0 else "#ccffcc",  # alternate colors for visibility
                label=f"Domain {j + 1}"
            )
            for j, d in enumerate(hit.domains)
        ]
        length = len(seq_index[hit.name])
        desc = seq_index[hit.name].description.decode()

        # render the feature records with appropriate length
        record = GraphicRecord(sequence_length=length, features=features)
        record.plot(ax=ax)

        # Set a descriptive title for each subplot
        ax.set_title(f"{desc} | E-value: {hit.evalue:.2e}", fontsize=10)

    # Improve layout
    fig.tight_layout(pad=2.0)  # increase padding for better readability

    # Show the final figure
    plt.savefig(save_file_location+"/test.png")


