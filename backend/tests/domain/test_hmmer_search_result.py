from unittest.mock import MagicMock
from backend.domain.HmmerSearchResult import HmmerSearchResult


def test_initialization():
    mock_alignment = MagicMock(name="AlignmentMock")
    result = HmmerSearchResult(
        sequence_id="seq1",
        pfam_accession="PF00001",
        e_value=1e-5,
        alignment=mock_alignment
    )

    assert result.sequence_id == "seq1"
    assert result.pfam_accession == "PF00001"
    assert result.e_value == 1e-5
    assert result.alignment == mock_alignment
    assert result.type == "Pfam hits"

def test_to_dict():
    mock_alignment = MagicMock(name="AlignmentMock")
    result = HmmerSearchResult(
        sequence_id="seq2",
        pfam_accession="PF00002",
        e_value=2e-6,
        alignment=mock_alignment
    )

    expected = {
        "sequence_id": "seq2",
        "pfam_accession": "PF00002",
        "e_value": 2e-6,
    }
    assert result.to_dict() == expected