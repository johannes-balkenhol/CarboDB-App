import pyhmmer


def read_hmm_profile(file_path):
    """
    Args:
        file_path: path to the HMM

    Returns:
        The read HMM.

    """
    with pyhmmer.plan7.HMMFile(file_path) as hmm_file:
        hmm = hmm_file.read()
    return hmm


def run_hmmer_search(hmm_profile, seq_file_location):
    """
    Args:
        hmm_profile: HMM profile to use for the HMMER search
        seq_file_location: location of the sequence file

    Returns:
        Read in sequences and found hits
    """
    with pyhmmer.easel.SequenceFile(seq_file_location, digital=True) as seq_file:
        sequences = seq_file.read_block()

    pipeline = pyhmmer.plan7.Pipeline(hmm_profile.alphabet)
    hits = pipeline.search_hmm(hmm_profile, sequences)
    return sequences, hits


def get_hmmer_hit_target_sequence(hit):
    """
    Args:
        hit: HMMER hit

    Returns:
        The sequence of the target sequence in the alignment.
    """
    return hit.domains[0].alignment.target_sequence


def get_hmmer_hit_identity_sequence(hit):
    """
    Args:
        hit: HMMER hit

    Returns:
        The identity sequence between the query and the target.
    """
    return hit.domains[0].alignment.identity_sequence


def save_hmmer_hits_to_txt(hits, save_file_location):
    """
    Args:
        hits: HMMER hits
        save_file_location: location to save a file to

    Returns:
        Saves the HMMER hits to an output file
    """
    with open(save_file_location, 'wb') as file_handle:
        hits.write(fh=file_handle, format='targets', header=True)