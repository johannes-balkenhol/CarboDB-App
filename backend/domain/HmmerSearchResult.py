import dataclasses

@dataclasses.dataclass
class HmmerSearchResult:
    def __init__(self,sequence_id, pfam_accession, e_value, alignment):
        self.sequence_id = sequence_id
        self.pfam_accession = pfam_accession
        self.e_value = e_value
        self.alignment = alignment