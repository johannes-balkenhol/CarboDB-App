import dataclasses

@dataclasses.dataclass
class HmmProfile:
    def __init__(self, pfam_accession, content):
        self.pfam_accession = pfam_accession
        self.content = content