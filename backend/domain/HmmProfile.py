import dataclasses

@dataclasses.dataclass
class HmmProfile:
    pfam_accession: str
    content: object
