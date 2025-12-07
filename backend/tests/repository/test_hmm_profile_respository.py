import os
import pytest
from unittest.mock import patch

from backend.repository.HmmProfileRepository import HmmProfileRepository
from backend.domain.HmmProfile import HmmProfile


@pytest.fixture
def mock_hmm_files(tmp_path):
    file_names = ['PF00001.hmm', 'PF00002.hmm', 'PF00003.hmm']
    for name in file_names:
        (tmp_path / name).write_text("Dummy HMM content")
    return tmp_path, file_names

@patch('backend.repository.HmmProfileRepository.read_hmm_profile')
def test_get_all_profiles(mock_read_hmm_profile, mock_hmm_files):
    tmp_path, file_names = mock_hmm_files
    mock_read_hmm_profile.side_effect = lambda path: f"Content of {os.path.basename(path)}"

    repository = HmmProfileRepository(source=str(tmp_path))
    profiles = repository.get_all_profiles()

    expected = {name[:-4]: f"Content of {name}" for name in file_names}

    assert len(profiles) == 3
    for profile in profiles:
        assert isinstance(profile, HmmProfile), "Result should be an HmmProfile"
        assert profile.pfam_accession in expected, "Returned pfam_accession do not match the expected accession"
        assert profile.content == expected[profile.pfam_accession], "Returned profile content do not match the expected content"
