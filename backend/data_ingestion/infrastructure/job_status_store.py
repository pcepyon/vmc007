"""
In-memory job status store with thread-safe implementation.
Following test-plan.md P0 requirement: threading.Lock() for concurrency safety.

This is a MVP simplification - avoids Redis/database for job tracking.
"""

import threading
from typing import Dict, Optional
from datetime import datetime
from enum import Enum


class JobStatus(Enum):
    """Job processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobInfo:
    """Job information data structure."""

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status = JobStatus.PENDING
        self.progress = 0
        self.total = 0
        self.error_message: Optional[str] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


class JobStatusStore:
    """
    Thread-safe in-memory store for job status tracking.

    P0 CRITICAL: All state access/modification must be protected by lock
    to prevent race conditions in concurrent processing.
    """

    def __init__(self):
        self._store: Dict[str, JobInfo] = {}
        self._lock = threading.Lock()  # P0: Thread-safety guarantee

    def create_job(self, job_id: str) -> JobInfo:
        """
        Create a new job entry.

        Args:
            job_id: Unique job identifier

        Returns:
            JobInfo instance
        """
        with self._lock:  # Critical section
            if job_id in self._store:
                raise ValueError(f"Job {job_id} already exists")

            job_info = JobInfo(job_id)
            self._store[job_id] = job_info
            return job_info

    def get_job(self, job_id: str) -> Optional[JobInfo]:
        """
        Retrieve job information.

        Args:
            job_id: Job identifier

        Returns:
            JobInfo if exists, None otherwise
        """
        with self._lock:  # Critical section
            return self._store.get(job_id)

    def update_status(self, job_id: str, status: JobStatus, error_message: Optional[str] = None) -> None:
        """
        Update job status.

        Args:
            job_id: Job identifier
            status: New status
            error_message: Optional error message for failed jobs
        """
        with self._lock:  # Critical section
            job_info = self._store.get(job_id)
            if not job_info:
                raise ValueError(f"Job {job_id} not found")

            job_info.status = status
            job_info.updated_at = datetime.now()
            if error_message:
                job_info.error_message = error_message

    def update_progress(self, job_id: str, progress: int, total: int) -> None:
        """
        Update job progress.

        Args:
            job_id: Job identifier
            progress: Current progress count
            total: Total items to process
        """
        with self._lock:  # Critical section
            job_info = self._store.get(job_id)
            if not job_info:
                raise ValueError(f"Job {job_id} not found")

            job_info.progress = progress
            job_info.total = total
            job_info.updated_at = datetime.now()

    def increment_progress(self, job_id: str) -> int:
        """
        Atomically increment job progress by 1.

        Args:
            job_id: Job identifier

        Returns:
            Updated progress value
        """
        with self._lock:  # Critical section
            job_info = self._store.get(job_id)
            if not job_info:
                raise ValueError(f"Job {job_id} not found")

            job_info.progress += 1
            job_info.updated_at = datetime.now()
            return job_info.progress

    def delete_job(self, job_id: str) -> None:
        """
        Delete job from store.

        Args:
            job_id: Job identifier
        """
        with self._lock:  # Critical section
            if job_id in self._store:
                del self._store[job_id]

    def clear_all(self) -> None:
        """Clear all jobs from store (for testing purposes)."""
        with self._lock:  # Critical section
            self._store.clear()


# Global singleton instance for MVP
_job_store_instance: Optional[JobStatusStore] = None


def get_job_store() -> JobStatusStore:
    """Get the global job store instance."""
    global _job_store_instance
    if _job_store_instance is None:
        _job_store_instance = JobStatusStore()
    return _job_store_instance
