from unittest.mock import patch, MagicMock, mock_open
from backend.carboxylase_search.prosite_scan.prosite_scan_use_case import run_prosite_scan_for_all_patterns
from backend.carboxylase_search.prosite_scan.prosite_scan_use_case import parse_prosite_scan_output

@patch('backend.carboxylase_search.prosite_scan.prosite_scan_use_case.parse_prosite_scan_output')
@patch('backend.carboxylase_search.prosite_scan.prosite_scan_use_case.run_ps_scan_with_custom_profile')
def test_run_prosite_scan_workflow_for_all_patterns(mock_run_ps_scan, mock_parse_output):

    fake_repository = MagicMock()
    fake_repository.get_all_patterns.return_value = ["PATTERN1", "PATTERN2"]

    fake_result_1 = MagicMock()
    fake_result_2 = MagicMock()
    mock_parse_output.side_effect = [[fake_result_1], [fake_result_2]]

    base_dir = "/fake/base"
    seq_file = "/fake/sequences.fasta"
    output_dir = "/fake/output"


    result = run_prosite_scan_for_all_patterns(fake_repository, base_dir, seq_file, output_dir)


    assert "PATTERN1" in result
    assert "PATTERN2" in result
    assert result["PATTERN1"] == [fake_result_1]
    assert result["PATTERN2"] == [fake_result_2]

    fake_repository.get_all_patterns.assert_called_once()
    assert mock_run_ps_scan.call_count == 2
    assert mock_parse_output.call_count == 2


def test_parse_prosite_scan_output():
    fake_file_content = (
        ">SEQ123: PS00001 Some pattern name\n"
        "10 - 20  MKTLLTAL\n"
    )

    m = mock_open(read_data=fake_file_content)

    with patch('builtins.open', m):
        results = parse_prosite_scan_output("/fake/path/output.txt")

    assert len(results) == 1
    result = results[0]

    assert result.sequence_id == "SEQ123"
    assert result.prosite_accession == "PS00001"
    assert result.prosite_name == "Some pattern name"
    assert result.start_position == 10
    assert result.end_position == 20
    assert result.pattern_sequence == "MKTLLTAL"