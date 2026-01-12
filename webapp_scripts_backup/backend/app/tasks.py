"""
Scheduled Tasks for CarboxyPred
"""

import os
import time
import logging
from pathlib import Path
from flask import current_app

logger = logging.getLogger(__name__)


def scheduled_cleanup_task():
    """
    Clean up old uploaded files
    Runs periodically based on USER_DATA_CLEANUP_INTERVAL config
    """
    try:
        upload_folder = current_app.config.get('UPLOADED_USER_DATA_FOLDER', '/tmp/uploads')
        prosite_folder = current_app.config.get('PROSITE_SCAN_OUTPUT_FOLDER', '/tmp/prosite')
        max_age_hours = 24  # Files older than this will be deleted
        
        max_age_seconds = max_age_hours * 3600
        current_time = time.time()
        
        cleaned_count = 0
        
        for folder in [upload_folder, prosite_folder]:
            folder_path = Path(folder)
            if not folder_path.exists():
                continue
            
            for file_path in folder_path.glob('*'):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        try:
                            file_path.unlink()
                            cleaned_count += 1
                            logger.info(f"Cleaned up old file: {file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to delete {file_path}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"Cleanup task completed: {cleaned_count} files removed")
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
