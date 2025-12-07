import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from backend.carboxylase_search.validate_user_input.validate_fasta_task import validate_fasta_task

@pytest.fixture
def app():
    app = Flask(__name__)
    return app

@pytest.fixture
def fake_file():
    file = MagicMock()
    file.filename = 'test.fasta'
    file.save = MagicMock()
    return file


@patch('backend.carboxylase_search.validate_user_input.validate_fasta_task.is_valid_fasta')
@patch('backend.carboxylase_search.validate_user_input.validate_fasta_task.os.path.getsize')
@patch('backend.carboxylase_search.validate_user_input.validate_fasta_task.os.remove')
def test_validate_fasta_task(mock_remove, mock_getsize, mock_is_valid_fasta, fake_file, app):
    mock_getsize.return_value = 123
    mock_is_valid_fasta.return_value = True

    allowed_extensions = ['.fasta']
    uploaded_folder = '/some/path'

    with app.app_context():
        response = validate_fasta_task(fake_file, allowed_extensions, uploaded_folder)

    assert response.status_code == 200
    json_data = response.get_json()

    assert json_data['is_valid'] is True
    assert 'file_id' in json_data
    fake_file.save.assert_called_once()
    mock_remove.assert_not_called()


def test_validate_fasta_no_file(app):
    allowed_extensions = ['.fasta']
    uploaded_folder = '/some/path'

    with app.app_context():
        response_tuple = validate_fasta_task(None, allowed_extensions, uploaded_folder)

    response, status_code = response_tuple

    assert status_code == 400
    assert response.get_json()['error'] == "No file provided"


@patch('backend.carboxylase_search.validate_user_input.validate_fasta_task.os.remove')
def test_validate_fasta_invalid_file_extension(fake_file, app):
    fake_file.filename = 'bad_file.txt'
    allowed_extensions = ['.fasta']
    uploaded_folder = '/some/path'

    with app.app_context():
        response_tuple = validate_fasta_task(fake_file, allowed_extensions, uploaded_folder)

    response, status_code = response_tuple

    assert status_code == 400
    assert "Invalid file extension" in response.json['error']


@patch('backend.carboxylase_search.validate_user_input.validate_fasta_task.os.path.getsize')
@patch('backend.carboxylase_search.validate_user_input.validate_fasta_task.os.remove')
def test_validate_fasta_empty_file(mock_remove, mock_getsize, fake_file, app):
    mock_getsize.return_value = 0

    allowed_extensions = ['.fasta']
    uploaded_folder = '/some/path'

    with app.app_context():
        response_tuple = validate_fasta_task(fake_file, allowed_extensions, uploaded_folder)

    response, status_code = response_tuple

    assert status_code == 400
    assert response.json['error'] == "Input is empty"
    mock_remove.assert_called_once()


@patch('backend.carboxylase_search.validate_user_input.validate_fasta_task.os.remove')
def test_validate_fasta_exception(mock_remove, fake_file, app):
    allowed_extensions = ['.fasta']
    uploaded_folder = '/some/path'

    # Make file.save() raise an exception
    fake_file.save.side_effect = Exception("Save failed")

    with app.app_context():
        response_tuple = validate_fasta_task(fake_file, allowed_extensions, uploaded_folder)

    response, status_code = response_tuple

    assert status_code == 500

    json_data = response.get_json()
    assert json_data['error'] == "File upload and validation failed"
    assert "Save failed" in json_data['details']
    mock_remove.assert_not_called()
