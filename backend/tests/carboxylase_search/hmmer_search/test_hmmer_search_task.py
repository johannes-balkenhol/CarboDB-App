from unittest.mock import patch, MagicMock
from backend.carboxylase_search.hmmer_search.hmmer_search_task import hmmer_search_task


@patch('backend.carboxylase_search.hmmer_search.hmmer_search_task.run_hmmer_workflow_for_all_profiles')
@patch('backend.carboxylase_search.hmmer_search.hmmer_search_task.collect_results_by_sequence')
@patch('backend.carboxylase_search.hmmer_search.hmmer_search_task.export_hits_to_pdf')
@patch('backend.carboxylase_search.hmmer_search.hmmer_search_task.HmmProfileRepository')
def test_hmmer_search_task(
    mock_hmm_repo,
    mock_export_hits_to_pdf,
    mock_collect_results,
    mock_run_hmmer_workflow,
    app
):

    fake_file_id = "fake123"
    fake_hmmer_hits = MagicMock()
    mock_run_hmmer_workflow.return_value = fake_hmmer_hits

    fake_results_by_sequence = {
        "seq1": {
            "profile1": [MagicMock(to_dict=lambda: {"mocked_hit": 1})]
        }
    }
    mock_collect_results.return_value = fake_results_by_sequence

    app.config['HMMER_PROFILE_FOLDER'] = '/fake/hmmer/profiles'
    app.config['UPLOADED_USER_DATA_FOLDER'] = '/fake/uploads'


    with app.app_context():
        response = hmmer_search_task(fake_file_id)


    assert response.status_code == 200

    json_data = response.get_json()

    assert "seq1" in json_data
    assert "profile1" in json_data["seq1"]
    assert json_data["seq1"]["profile1"] == [{"mocked_hit": 1}]


    mock_hmm_repo.assert_called_once_with('/fake/hmmer/profiles')
    mock_run_hmmer_workflow.assert_called_once()
    mock_collect_results.assert_called_once()
    mock_export_hits_to_pdf.assert_called_once()