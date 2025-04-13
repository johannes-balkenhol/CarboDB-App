import dataclasses
from pyhmmer.plan7 import Alignment


@dataclasses.dataclass
class HmmerSearchResult:
    sequence_id: str
    pfam_accession: str
    e_value: float
    alignment: Alignment
    type: str = "Pfam hits"

    def to_dict(self):
        return {
            "sequence_id": self.sequence_id,
            "pfam_accession": self.pfam_accession,
            "e_value": self.e_value,
        }