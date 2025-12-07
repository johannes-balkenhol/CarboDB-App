from unittest.mock import patch, MagicMock
from backend.carboxylase_search.hmmer_search.hmmer_search_task import hmmer_search_task


@patch('backend.carboxylase_search.hmmer_search.hmmer_search_task.run_hmmer_workflow')
@patch('backend.carboxylase_search.hmmer_search.hmmer_search_task.collect_results_by_sequence')
@patch('backend.carboxylase_search.hmmer_search.hmmer_search_task.save_pdf')
@patch('backend.carboxylase_search.hmmer_search.hmmer_search_task.jsonify_hits')
def test_hmmer_search_task(
    mock_jsonify_hits,
    mock_save_pdf,
    mock_collect_results,
    mock_run_hmmer_workflow,
    app
):

    fake_file_id = "fake123"
    fake_hmmer_hits = MagicMock()
    mock_run_hmmer_workflow.return_value = fake_hmmer_hits

    fake_results_by_sequence = {
        "seq1": {
            "profile1": [{"mocked_hit": 1}]
        }
    }
    mock_collect_results.return_value = fake_results_by_sequence

    # Prepare mock Flask response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.get_json.return_value = fake_results_by_sequence

    mock_jsonify_hits.return_value = mock_response

    app.config['HMMER_PROFILE_FOLDER'] = '/fake/hmmer/profiles'
    app.config['UPLOADED_USER_DATA_FOLDER'] = '/fake/uploads'


    with app.app_context():
        response = hmmer_search_task(fake_file_id)


    assert response.status_code == 200

    json_data = response.get_json()

    assert "seq1" in json_data
    assert "profile1" in json_data["seq1"]
    assert json_data["seq1"]["profile1"] == [{"mocked_hit": 1}]


    mock_run_hmmer_workflow.assert_called_once()
    mock_collect_results.assert_called_once()
    mock_save_pdf.assert_called_once()
    mock_jsonify_hits.assert_called_once()