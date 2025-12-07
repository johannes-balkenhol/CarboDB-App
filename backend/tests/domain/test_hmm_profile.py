from unittest.mock import MagicMock
from backend.domain.HmmProfile import HmmProfile



def test_initialization():
    mock_content = MagicMock(name="AlignmentMock")
    profile = HmmProfile(
        pfam_accession="PF00001",
        content=mock_content
    )

    assert profile.pfam_accession == "PF00001"
    assert profile.content == mock_content
