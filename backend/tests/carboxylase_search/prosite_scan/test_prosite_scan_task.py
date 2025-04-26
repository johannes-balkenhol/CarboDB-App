from unittest.mock import patch, MagicMock
from backend.carboxylase_search.prosite_scan.prosite_scan_task import prosite_scan_task

@patch('backend.carboxylase_search.prosite_scan.prosite_scan_task.export_hits_to_pdf')
@patch('backend.carboxylase_search.prosite_scan.prosite_scan_task.collect_results_by_sequence')
@patch('backend.carboxylase_search.prosite_scan.prosite_scan_task.run_prosite_scan_workflow_for_all_patterns')
@patch('backend.carboxylase_search.prosite_scan.prosite_scan_task.PrositePatternRepository')
def test_prosite_scan_task(mock_repository, mock_run_scan, mock_collect_results, mock_export_pdf, app):
    file_id = "testfile123"

    app.config['UPLOADED_USER_DATA_FOLDER'] = "/fake/uploads"
    app.config['BASE_DIR'] = "/fake/base"
    app.config['PROSITE_SCAN_OUTPUT_FOLDER'] = "/fake/prosite/output"

    fake_prosite_hits = {"PATTERN1": [MagicMock()]}
    mock_run_scan.return_value = fake_prosite_hits

    fake_collected_results = {
        "seq1": {
            "PATTERN1": [MagicMock(to_dict=lambda: {"mock_key": "mock_value"})]
        }
    }
    mock_collect_results.return_value = fake_collected_results

    with app.app_context():
        response = prosite_scan_task(file_id)

    assert response.status_code == 200
    json_data = response.get_json()

    assert "seq1" in json_data
    assert "PATTERN1" in json_data["seq1"]
    assert isinstance(json_data["seq1"]["PATTERN1"], list)
    assert json_data["seq1"]["PATTERN1"][0] == {"mock_key": "mock_value"}


    mock_repository.assert_called_once()
    mock_run_scan.assert_called_once()
    mock_collect_results.assert_called_once()
    mock_export_pdf.assert_called_once()