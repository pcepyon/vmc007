"""
Ingestion Service - Orchestrates file upload processing.
Following plan.md Phase 3: Service Orchestration.

Responsibility:
- Coordinate file parsing → storage flow
- Manage background jobs with ThreadPoolExecutor
- Update job status and handle errors
"""

import uuid
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List
import pandas as pd

from data_ingestion.services.excel_parser import ExcelParser, ValidationError
from data_ingestion.infrastructure.repositories import (
    save_research_funding_data,
    save_student_data,
    save_publication_data,
    save_department_kpi_data
)
from data_ingestion.infrastructure.job_status_store import get_job_store

logger = logging.getLogger(__name__)

# Module-level ThreadPoolExecutor (MVP: single worker for sequential processing)
executor = ThreadPoolExecutor(max_workers=1)


FILE_TYPE_PARSERS = {
    'research_funding': (ExcelParser.parse_research_project_data, save_research_funding_data),
    'students': (ExcelParser.parse_student_roster, save_student_data),
    'publications': (ExcelParser.parse_publication_list, save_publication_data),
    'kpi': (ExcelParser.parse_department_kpi, save_department_kpi_data),
}


def submit_upload_job(files: Dict[str, str]) -> str:
    """
    Submit file upload job to background processing queue.

    Args:
        files: Dict of file_type -> file_path (e.g., {'research_funding': '/tmp/...csv'})

    Returns:
        job_id: UUID string for status tracking
    """
    job_id = str(uuid.uuid4())

    # Initialize job status
    job_store = get_job_store()
    job_info = job_store.create_job(job_id)
    # Note: Additional job metadata would be stored in a separate structure if needed

    # Submit to background thread
    executor.submit(process_upload, job_id, files)

    logger.info(f"Job {job_id} submitted for processing")
    return job_id


def process_upload(job_id: str, files: Dict[str, str]) -> None:
    """
    Process uploaded files in background thread.

    Following spec.md Section 3.5: File-level independent transactions for partial success.

    Args:
        job_id: Job UUID for status updates
        files: Dict of file_type -> file_path
    """
    try:
        total_files = len(files)
        completed_count = 0
        file_results = []

        for file_type, file_path in files.items():
            try:
                logger.info(f"Processing {file_type} from {file_path}")

                # Get parser and repository functions
                if file_type not in FILE_TYPE_PARSERS:
                    raise ValueError(f"Unknown file type: {file_type}")

                parser_func, repo_func = FILE_TYPE_PARSERS[file_type]

                # Parse CSV/Excel file
                df = pd.read_csv(file_path, encoding='utf-8')
                validated_df = parser_func(df)

                # Save to database (independent transaction per file)
                result = repo_func(validated_df, replace=True)

                # Update file status
                file_results.append({
                    'file_type': file_type,
                    'status': 'completed',
                    'rows_processed': len(df),
                    'rows_inserted': result['rows_inserted'],
                    'rows_skipped': result.get('rows_skipped', 0)
                })

                completed_count += 1

            except ValidationError as e:
                logger.error(f"Validation error for {file_type}: {e}")
                file_results.append({
                    'file_type': file_type,
                    'status': 'failed',
                    'error_message': str(e),
                    'error_code': 'ERR_SCHEMA_001'
                })
            except Exception as e:
                logger.exception(f"Unexpected error processing {file_type}: {e}")
                file_results.append({
                    'file_type': file_type,
                    'status': 'failed',
                    'error_message': str(e),
                    'error_code': 'ERR_PARSE_001'
                })

        # Determine overall job status
        failed_count = sum(1 for f in file_results if f['status'] == 'failed')

        if failed_count == 0:
            job_status = 'completed'
        elif failed_count == total_files:
            job_status = 'failed'
        else:
            job_status = 'partial_success'

        # Update final job status
        job_store = get_job_store()
        from data_ingestion.infrastructure.job_status_store import JobStatus
        status_enum = JobStatus.COMPLETED if job_status == 'completed' else JobStatus.FAILED
        job_store.update_status(job_id, status_enum)
        job_store.update_progress(job_id, 100, 100)

        logger.info(f"Job {job_id} finished with status: {job_status}")

    except Exception as e:
        logger.exception(f"Critical error in job {job_id}: {e}")
        job_store = get_job_store()
        from data_ingestion.infrastructure.job_status_store import JobStatus
        job_store.update_status(job_id, JobStatus.FAILED, str(e))
