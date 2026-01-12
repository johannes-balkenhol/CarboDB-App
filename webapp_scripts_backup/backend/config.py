"""
Configuration for CarboxyPred Flask Application
"""

import os


class BaseConfig:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'carboxypred-secret-key-change-in-production')
    DEBUG = os.environ.get('FLASK_DEBUG', '1') == '1'
    
    # File uploads
    UPLOADED_USER_DATA_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp/uploads')
    PROSITE_SCAN_OUTPUT_FOLDER = os.environ.get('PROSITE_FOLDER', '/tmp/prosite')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload
    
    # Database
    DATABASE_PATH = os.environ.get('DATABASE_PATH', '/app/database_files/carboxylase.db')
    
    # ML Models
    MODEL_DIR = os.environ.get('MODEL_DIR', '/srv/app/backend/ml_models')
    
    # Cleanup
    USER_DATA_CLEANUP_INTERVAL = 24  # hours
    
    # CORS
    CORS_ORIGINS = '*'


class ProductionConfig(BaseConfig):
    """Production configuration"""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Must be set in production


class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    DEBUG = True


class TestingConfig(BaseConfig):
    """Testing configuration"""
    TESTING = True
    DATABASE_PATH = ':memory:'
