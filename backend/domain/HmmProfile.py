import dataclasses

@dataclasses.dataclass
class HmmProfile:
    def __init__(self, name, content):
        self.name = name
        self.content = content