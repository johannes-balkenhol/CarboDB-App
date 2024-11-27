import os
from backend.domain.HmmProfile import HmmProfile
from backend.carboxylase_search.hmmer.hmmer_search_utils import read_hmm_profile

class HmmProfileRepository:
    def __init__(self, source):
        self.source = source

    def get_all_profiles(self):
        hmm_files = [os.path.join(self.source, f) for f in os.listdir(self.source) if f.endswith('.hmm')]
        profiles = []
        for file_path in hmm_files:
               hmm = read_hmm_profile(file_path)
               profiles.append(HmmProfile(name=os.path.basename(file_path), content=hmm))
        return profiles