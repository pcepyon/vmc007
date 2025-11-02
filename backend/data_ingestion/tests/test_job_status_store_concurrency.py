"""
P0 CRITICAL BLOCKER TEST: Thread-safe job status store validation.
Following test-plan.md: Prove threading.Lock() works correctly under concurrent access.

Test Requirement:
- 10+ threads simultaneously updating the same job_id
- Final count must match expected value exactly
- No race conditions or data corruption
"""

import pytest
import threading
import time
from data_ingestion.infrastructure.job_status_store import (
    JobStatusStore,
    JobStatus,
)


@pytest.mark.unit
class TestJobStatusStoreConcurrency:
    """P0 Blocker: Thread-safety validation."""

    def test_concurrent_increment_progress_is_thread_safe(self):
        """
        P0 TEST: Verify threading.Lock() prevents race conditions.

        Scenario:
        - 10 threads concurrently increment progress for the same job
        - Each thread increments 100 times
        - Expected final count: 1000 (10 threads × 100 increments)
        """
        # Arrange
        store = JobStatusStore()
        job_id = "concurrent-test-job"
        num_threads = 10
        increments_per_thread = 100
        expected_final_count = num_threads * increments_per_thread

        # Create job with known total
        store.create_job(job_id)
        store.update_progress(job_id, progress=0, total=expected_final_count)

        # Thread worker function
        def increment_worker():
            for _ in range(increments_per_thread):
                store.increment_progress(job_id)
                # Small delay to increase likelihood of race conditions
                # (if lock is not working)
                time.sleep(0.0001)

        # Act: Start 10 concurrent threads
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=increment_worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Assert: Final count must be exactly as expected
        job_info = store.get_job(job_id)
        assert job_info is not None, "Job should exist"
        assert job_info.progress == expected_final_count, \
            f"Race condition detected: expected {expected_final_count}, got {job_info.progress}"

    def test_concurrent_status_updates_are_thread_safe(self):
        """
        P0 TEST: Verify concurrent status updates don't cause corruption.

        Scenario:
        - Multiple threads try to update job status simultaneously
        - No exceptions should be raised
        - Final status should be one of the valid states
        """
        # Arrange
        store = JobStatusStore()
        job_id = "status-update-test"
        num_threads = 20
        store.create_job(job_id)

        statuses = [
            JobStatus.PROCESSING,
            JobStatus.COMPLETED,
            JobStatus.FAILED,
        ]

        exception_container = []

        # Thread worker function
        def update_status_worker(status):
            try:
                for _ in range(10):
                    store.update_status(job_id, status)
                    time.sleep(0.0001)
            except Exception as e:
                exception_container.append(e)

        # Act: Concurrent status updates
        threads = []
        for i in range(num_threads):
            status = statuses[i % len(statuses)]
            thread = threading.Thread(target=update_status_worker, args=(status,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Assert: No exceptions and valid final state
        assert len(exception_container) == 0, \
            f"Thread-safety violation: exceptions occurred: {exception_container}"

        job_info = store.get_job(job_id)
        assert job_info is not None
        assert job_info.status in statuses

    def test_concurrent_job_creation_prevents_duplicates(self):
        """
        P0 TEST: Verify thread-safe job creation prevents duplicate IDs.

        Scenario:
        - Multiple threads try to create the same job_id
        - Only one should succeed, others should raise ValueError
        """
        # Arrange
        store = JobStatusStore()
        job_id = "duplicate-test-job"
        num_threads = 10

        success_count = []
        error_count = []

        # Thread worker function
        def create_job_worker():
            try:
                store.create_job(job_id)
                success_count.append(1)
            except ValueError:
                error_count.append(1)

        # Act: Concurrent job creation attempts
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=create_job_worker)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Assert: Exactly one success, rest should fail
        assert len(success_count) == 1, \
            f"Expected 1 successful creation, got {len(success_count)}"
        assert len(error_count) == num_threads - 1, \
            f"Expected {num_threads - 1} errors, got {len(error_count)}"

    def test_concurrent_read_write_operations(self):
        """
        P0 TEST: Mixed read/write operations under concurrency.

        Scenario:
        - Some threads increment progress
        - Some threads read job status
        - No deadlocks or data corruption should occur
        """
        # Arrange
        store = JobStatusStore()
        job_id = "read-write-test"
        num_writer_threads = 5
        num_reader_threads = 5
        increments_per_writer = 50
        expected_final_count = num_writer_threads * increments_per_writer

        store.create_job(job_id)
        store.update_progress(job_id, progress=0, total=expected_final_count)

        exception_container = []

        # Writer function
        def writer_worker():
            try:
                for _ in range(increments_per_writer):
                    store.increment_progress(job_id)
                    time.sleep(0.0001)
            except Exception as e:
                exception_container.append(e)

        # Reader function
        def reader_worker():
            try:
                for _ in range(100):
                    job_info = store.get_job(job_id)
                    assert job_info is not None
                    # Validate progress is within expected range
                    assert 0 <= job_info.progress <= expected_final_count
                    time.sleep(0.0001)
            except Exception as e:
                exception_container.append(e)

        # Act: Start writers and readers concurrently
        threads = []

        for _ in range(num_writer_threads):
            thread = threading.Thread(target=writer_worker)
            threads.append(thread)
            thread.start()

        for _ in range(num_reader_threads):
            thread = threading.Thread(target=reader_worker)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Assert: No exceptions and correct final count
        assert len(exception_container) == 0, \
            f"Concurrency errors occurred: {exception_container}"

        job_info = store.get_job(job_id)
        assert job_info.progress == expected_final_count


@pytest.mark.unit
class TestJobStatusStoreBasicOperations:
    """Basic functionality tests (non-concurrent)."""

    def test_create_and_get_job(self):
        """Test basic job creation and retrieval."""
        # Arrange
        store = JobStatusStore()
        job_id = "test-job-1"

        # Act
        created_job = store.create_job(job_id)
        retrieved_job = store.get_job(job_id)

        # Assert
        assert created_job is not None
        assert retrieved_job is not None
        assert retrieved_job.job_id == job_id
        assert retrieved_job.status == JobStatus.PENDING

    def test_update_status(self):
        """Test status update functionality."""
        # Arrange
        store = JobStatusStore()
        job_id = "test-job-2"
        store.create_job(job_id)

        # Act
        store.update_status(job_id, JobStatus.PROCESSING)
        job_info = store.get_job(job_id)

        # Assert
        assert job_info.status == JobStatus.PROCESSING

    def test_update_progress(self):
        """Test progress update functionality."""
        # Arrange
        store = JobStatusStore()
        job_id = "test-job-3"
        store.create_job(job_id)

        # Act
        store.update_progress(job_id, progress=50, total=100)
        job_info = store.get_job(job_id)

        # Assert
        assert job_info.progress == 50
        assert job_info.total == 100

    def test_delete_job(self):
        """Test job deletion."""
        # Arrange
        store = JobStatusStore()
        job_id = "test-job-4"
        store.create_job(job_id)

        # Act
        store.delete_job(job_id)
        job_info = store.get_job(job_id)

        # Assert
        assert job_info is None
