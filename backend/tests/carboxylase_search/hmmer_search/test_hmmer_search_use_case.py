from unittest.mock import patch, MagicMock
from backend.carboxylase_search.hmmer_search.hmmer_search_use_case import run_hmmer_search_for_all_profiles


@patch('backend.carboxylase_search.hmmer_search.hmmer_search_use_case.run_hmmer_search')
def test_run_hmmer_workflow_for_all_profiles(mock_run_hmmer_search):
    fake_profile = MagicMock()
    fake_profile.content = b"fake HMM content"
    fake_profile.pfam_accession = "PF12345"

    fake_repository = MagicMock()
    fake_repository.get_all_profiles.return_value = [fake_profile]


    fake_hit = MagicMock()
    fake_hit.name.decode.return_value = "seq1"
    fake_hit.evalue = 1e-50
    fake_hit.domains = [MagicMock(alignment="FAKE_ALIGNMENT")]


    mock_run_hmmer_search.return_value = ([], [fake_hit])

    result = run_hmmer_search_for_all_profiles(fake_repository, "/fake/path/to/sequences.fasta")


    assert "PF12345" in result
    hits_list = result["PF12345"]
    assert len(hits_list) == 1
    hit_obj = hits_list[0]

    assert hit_obj.sequence_id == "seq1"
    assert hit_obj.pfam_accession == "PF12345"
    assert hit_obj.e_value == 1e-50
    assert hit_obj.alignment == "FAKE_ALIGNMENT"


    fake_repository.get_all_profiles.assert_called_once()
    mock_run_hmmer_search.assert_called_once_with(fake_profile.content, "/fake/path/to/sequences.fasta")