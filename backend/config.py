import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))[:-7]
BASE_DIR_BACKEND = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    BASE_DIR = BASE_DIR
    USER_DATA_TIME_TO_LIVE = 3600  # 1 hour
    USER_DATA_CLEANUP_INTERVAL = 24  # hours
    UPLOADED_USER_DATA_FOLDER = "/tmp/uploads"
    UPLOADED_USER_DATA_FOLDER_PATH = "/tmp/uploads"
    HMMER_PROFILE_FOLDER = os.path.join(BASE_DIR, "resources/carboxylases/hmm_profiles")
    PROSITE_SCAN_OUTPUT_FOLDER = os.path.join(BASE_DIR_BACKEND, "carboxylase_search/prosite_scan/output")
    ALLOWED_FILE_EXTENSIONS = {'.fasta'}
    MAX_CONTENT_LENGTH_STRING = "16 MB"