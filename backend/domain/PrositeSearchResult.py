import dataclasses

@dataclasses.dataclass
class PrositeSearchResult:
    def __init__(self, sequence_id, prosite_accession, prosite_name, start_position, end_position, pattern_sequence):
        self.sequence_id = sequence_id
        self.prosite_accession = prosite_accession
        self.prosite_name = prosite_name
        self.start_position = start_position
        self.end_position = end_position
        self.pattern_sequence = pattern_sequence