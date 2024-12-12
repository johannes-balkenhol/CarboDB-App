import dataclasses

@dataclasses.dataclass
class HmmerSearchResult:
    def __init__(self, pfam_domain, e_value, alignment):
        self.pfam_domain = pfam_domain
        self.e_value = e_value
        self.alignment = alignment