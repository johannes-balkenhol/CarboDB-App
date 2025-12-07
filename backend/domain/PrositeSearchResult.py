import dataclasses

@dataclasses.dataclass
class PrositeSearchResult:
    sequence_id: str
    prosite_accession: str
    prosite_name: str
    start_position: int
    end_position: int
    pattern_sequence: str
    type: str = "Prosite hits"

    def to_dict(self):
        return {
            "sequence_id": self.sequence_id,
            "prosite_accession": self.prosite_accession,
            "prosite_name": self.prosite_name,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "pattern_sequence": self.pattern_sequence,
            "type": self.type
        }