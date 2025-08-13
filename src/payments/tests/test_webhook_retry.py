"""Tests for webhook retry service."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from ..webhook_retry import (
    WebhookRetryService,
    WebhookRetryWorker,
    WebhookRetryConfig,
    WebhookStatus
)
from ..models import WebhookEvent


class TestWebhookRetryService:
    """Test webhook retry service functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def mock_webhook_processor(self):
        """Mock webhook processor function."""
        return AsyncMock(return_value=True)
    
    @pytest.fixture
    def retry_config(self):
        """Retry configuration for testing."""
        return WebhookRetryConfig(
            max_retries=3,
            initial_delay=0.1,
            max_delay=1.0,
            backoff_multiplier=2.0,
            jitter_factor=0.1
        )
    
    @pytest.fixture
    def retry_service(self, mock_db, retry_config, mock_webhook_processor):
        """Create webhook retry service instance."""
        return WebhookRetryService(
            db=mock_db,
            config=retry_config,
            webhook_processor=mock_webhook_processor
        )
    
    @pytest.fixture
    def sample_webhook(self):
        """Sample webhook event for testing."""
        return Mock(
            id=uuid4(),
            type="payment_intent.succeeded",
            payload='{"data": {"object": {"id": "pi_123"}}}',
            processing_status=WebhookStatus.FAILED.value,
            retry_count=0,
            next_retry_at=None,
            last_retry_at=None,
            error_message="Connection timeout"
        )
    
    @pytest.fixture
    def failed_webhooks(self):
        """Sample failed webhooks for testing."""
        return [
            Mock(
                id=uuid4(),
                type="payment_intent.succeeded",
                payload='{"data": {"object": {"id": "pi_123"}}}',
                processing_status=WebhookStatus.FAILED.value,
                retry_count=1,
                next_retry_at=datetime.utcnow() - timedelta(minutes=5)
            ),
            Mock(
                id=uuid4(),
                type="charge.succeeded",
                payload='{"data": {"object": {"id": "ch_123"}}}',
                processing_status=WebhookStatus.RETRYING.value,
                retry_count=2,
                next_retry_at=datetime.utcnow() - timedelta(minutes=2)
            )
        ]
    
    @pytest.mark.asyncio
    async def test_process_failed_webhooks_success(self, retry_service, mock_db, failed_webhooks):
        """Test successful processing of failed webhooks."""
        # Arrange
        mock_db.query.return_value.filter.return_value.all.return_value = failed_webhooks
        
        # Act
        await retry_service.process_failed_webhooks()
        
        # Assert
        assert retry_service.processing is False
        # Verify each webhook was processed
        for webhook in failed_webhooks:
            assert webhook.processing_status == WebhookStatus.SUCCESS.value
            assert webhook.processed_at is not None
            assert webhook.error_message is None
    
    @pytest.mark.asyncio
    async def test_process_failed_webhooks_already_processing(self, retry_service):
        """Test that processing doesn't start if already in progress."""
        # Arrange
        retry_service.processing = True
        
        # Act
        await retry_service.process_failed_webhooks()
        
        # Assert
        # Should not have started processing
        assert retry_service.processing is True
    
    @pytest.mark.asyncio
    async def test_retry_webhook_success(self, retry_service, sample_webhook, mock_db):
        """Test successful webhook retry."""
        # Arrange
        retry_service.webhook_processor = AsyncMock(return_value=True)
        
        # Act
        await retry_service._retry_webhook(sample_webhook)
        
        # Assert
        assert sample_webhook.processing_status == WebhookStatus.SUCCESS.value
        assert sample_webhook.processed_at is not None
        assert sample_webhook.error_message is None
        assert sample_webhook.retry_count == 1
        assert sample_webhook.last_retry_at is not None
        assert sample_webhook.next_retry_at is not None
        
        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_retry_webhook_failure(self, retry_service, sample_webhook, mock_db):
        """Test webhook retry failure."""
        # Arrange
        retry_service.webhook_processor = AsyncMock(return_value=False)
        
        # Act
        await retry_service._retry_webhook(sample_webhook)
        
        # Assert
        assert sample_webhook.processing_status == WebhookStatus.FAILED.value
        assert sample_webhook.retry_count == 1
        assert sample_webhook.last_retry_at is not None
        assert sample_webhook.next_retry_at is not None
        
        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_retry_webhook_max_retries_exceeded(self, retry_service, sample_webhook, mock_db):
        """Test webhook retry when max retries exceeded."""
        # Arrange
        retry_service.webhook_processor = AsyncMock(return_value=False)
        sample_webhook.retry_count = 3  # Max retries
        
        # Act
        await retry_service._retry_webhook(sample_webhook)
        
        # Assert
        assert sample_webhook.processing_status == WebhookStatus.DEAD_LETTER.value
        assert sample_webhook.error_message == "Max retries exceeded"
        
        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_retry_webhook_exception(self, retry_service, sample_webhook, mock_db):
        """Test webhook retry when exception occurs."""
        # Arrange
        retry_service.webhook_processor = AsyncMock(side_effect=Exception("Processor error"))
        
        # Act
        await retry_service._retry_webhook(sample_webhook)
        
        # Assert
        assert sample_webhook.processing_status == WebhookStatus.FAILED.value
        assert sample_webhook.error_message == "Processor error"
        
        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_default_webhook_processing_payment_success(self, retry_service, sample_webhook):
        """Test default webhook processing for payment success."""
        # Arrange
        sample_webhook.type = "payment_intent.succeeded"
        
        # Act
        result = await retry_service._default_webhook_processing(sample_webhook)
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_default_webhook_processing_payment_failure(self, retry_service, sample_webhook):
        """Test default webhook processing for payment failure."""
        # Arrange
        sample_webhook.type = "payment_intent.failed"
        
        # Act
        result = await retry_service._default_webhook_processing(sample_webhook)
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_default_webhook_processing_subscription_created(self, retry_service, sample_webhook):
        """Test default webhook processing for subscription created."""
        # Arrange
        sample_webhook.type = "subscription.created"
        
        # Act
        result = await retry_service._default_webhook_processing(sample_webhook)
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_default_webhook_processing_invalid_payload(self, retry_service, sample_webhook):
        """Test default webhook processing with invalid payload."""
        # Arrange
        sample_webhook.payload = '{"error": "invalid"}'
        
        # Act
        result = await retry_service._default_webhook_processing(sample_webhook)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_default_webhook_processing_unknown_type(self, retry_service, sample_webhook):
        """Test default webhook processing for unknown event type."""
        # Arrange
        sample_webhook.type = "unknown.event.type"
        
        # Act
        result = await retry_service._default_webhook_processing(sample_webhook)
        
        # Assert
        assert result is True  # Should mark as successful for unhandled types
    
    def test_calculate_retry_delay(self, retry_service):
        """Test retry delay calculation with exponential backoff."""
        # Test first retry
        delay1 = retry_service._calculate_retry_delay(1)
        assert delay1 >= 0.09  # 0.1 - jitter
        assert delay1 <= 0.11  # 0.1 + jitter
        
        # Test second retry
        delay2 = retry_service._calculate_retry_delay(2)
        assert delay2 >= 0.18  # 0.2 - jitter
        assert delay2 <= 0.22  # 0.2 + jitter
        
        # Test third retry
        delay3 = retry_service._calculate_retry_delay(3)
        assert delay3 >= 0.36  # 0.4 - jitter
        assert delay3 <= 0.44  # 0.4 + jitter
        
        # Test max delay limit
        delay_max = retry_service._calculate_retry_delay(10)
        assert delay_max <= retry_service.config.max_delay
    
    def test_get_dead_letter_queue(self, retry_service, mock_db):
        """Test retrieving webhooks from dead letter queue."""
        # Arrange
        dead_letter_webhooks = [Mock(), Mock()]
        mock_db.query.return_value.filter.return_value.all.return_value = dead_letter_webhooks
        
        # Act
        result = retry_service.get_dead_letter_queue()
        
        # Assert
        assert result == dead_letter_webhooks
        mock_db.query.assert_called_once()
    
    def test_retry_dead_letter_webhook_success(self, retry_service, mock_db):
        """Test successful retry of dead letter webhook."""
        # Arrange
        webhook_id = uuid4()
        webhook = Mock(
            id=webhook_id,
            processing_status=WebhookStatus.DEAD_LETTER.value
        )
        mock_db.query.return_value.filter.return_value.first.return_value = webhook
        
        # Act
        result = retry_service.retry_dead_letter_webhook(webhook_id)
        
        # Assert
        assert result is True
        assert webhook.processing_status == WebhookStatus.PENDING.value
        assert webhook.retry_count == 0
        assert webhook.next_retry_at is not None
        assert webhook.error_message is None
        
        mock_db.commit.assert_called_once()
    
    def test_retry_dead_letter_webhook_not_found(self, retry_service, mock_db):
        """Test retry of non-existent dead letter webhook."""
        # Arrange
        webhook_id = uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = retry_service.retry_dead_letter_webhook(webhook_id)
        
        # Assert
        assert result is False
    
    def test_retry_dead_letter_webhook_wrong_status(self, retry_service, mock_db):
        """Test retry of webhook not in dead letter queue."""
        # Arrange
        webhook_id = uuid4()
        webhook = Mock(
            id=webhook_id,
            processing_status=WebhookStatus.FAILED.value
        )
        mock_db.query.return_value.filter.return_value.first.return_value = webhook
        
        # Act
        result = retry_service.retry_dead_letter_webhook(webhook_id)
        
        # Assert
        assert result is False
    
    def test_get_retry_stats(self, retry_service, mock_db):
        """Test retrieval of retry statistics."""
        # Arrange
        # Mock counts for different statuses
        total_count = Mock()
        total_count.count.return_value = 100
        
        pending_count = Mock()
        pending_count.count.return_value = 10
        
        failed_count = Mock()
        failed_count.count.return_value = 20
        
        retrying_count = Mock()
        retrying_count.count.return_value = 5
        
        successful_count = Mock()
        successful_count.count.return_value = 60
        
        dead_letter_count = Mock()
        dead_letter_count.count.return_value = 5
        
        # Chain the mock queries
        mock_db.query.return_value.filter.return_value = total_count
        mock_db.query.return_value.filter.return_value.filter.return_value = pending_count
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value = failed_count
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value = retrying_count
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value = successful_count
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value = dead_letter_count
        
        # Act
        result = retry_service.get_retry_stats()
        
        # Assert
        assert result["total"] == 100
        assert result["pending"] == 10
        assert result["failed"] == 20
        assert result["retrying"] == 5
        assert result["successful"] == 60
        assert result["dead_letter"] == 5
        assert result["success_rate"] == 60.0  # 60/100 * 100
    
    def test_cleanup_old_webhooks(self, retry_service, mock_db):
        """Test cleanup of old webhook events."""
        # Arrange
        mock_db.query.return_value.filter.return_value.filter.return_value.delete.return_value = 25
        
        # Act
        retry_service.cleanup_old_webhooks(days_to_keep=90)
        
        # Assert
        mock_db.commit.assert_called_once()
    
    def test_cleanup_old_webhooks_exception(self, retry_service, mock_db):
        """Test cleanup of old webhooks when exception occurs."""
        # Arrange
        mock_db.commit.side_effect = Exception("Database error")
        
        # Act
        retry_service.cleanup_old_webhooks(days_to_keep=90)
        
        # Assert
        mock_db.rollback.assert_called_once()


class TestWebhookRetryWorker:
    """Test webhook retry worker functionality."""
    
    @pytest.fixture
    def mock_retry_service(self):
        """Mock webhook retry service."""
        return Mock()
    
    @pytest.fixture
    def worker(self, mock_retry_service):
        """Create webhook retry worker instance."""
        return WebhookRetryWorker(
            retry_service=mock_retry_service,
            poll_interval=0.1,
            max_concurrent=3
        )
    
    @pytest.mark.asyncio
    async def test_worker_start_stop(self, worker):
        """Test worker start and stop functionality."""
        # Arrange
        worker.running = False
        
        # Act - Start worker
        start_task = asyncio.create_task(worker.start())
        
        # Wait a bit for worker to start
        await asyncio.sleep(0.05)
        
        # Assert
        assert worker.running is True
        
        # Act - Stop worker
        worker.stop()
        
        # Wait for worker to stop
        await asyncio.sleep(0.05)
        
        # Clean up
        if not start_task.done():
            start_task.cancel()
            try:
                await start_task
            except asyncio.CancelledError:
                pass
        
        # Assert
        assert worker.running is False
    
    @pytest.mark.asyncio
    async def test_worker_already_running(self, worker):
        """Test worker behavior when already running."""
        # Arrange
        worker.running = True
        
        # Act
        await worker.start()
        
        # Assert
        # Should not have started again
        assert worker.running is True
    
    @pytest.mark.asyncio
    async def test_process_webhook_batch(self, worker, mock_retry_service):
        """Test processing webhook batch concurrently."""
        # Arrange
        webhooks = [Mock(), Mock(), Mock()]
        
        # Act
        await worker.process_webhook_batch(webhooks)
        
        # Assert
        # Verify that each webhook was processed
        assert mock_retry_service._retry_webhook.call_count == 3
    
    @pytest.mark.asyncio
    async def test_process_webhook_batch_with_semaphore(self, worker, mock_retry_service):
        """Test that webhook batch processing respects concurrency limits."""
        # Arrange
        webhooks = [Mock() for _ in range(5)]  # More than max_concurrent
        
        # Act
        await worker.process_webhook_batch(webhooks)
        
        # Assert
        # All webhooks should be processed
        assert mock_retry_service._retry_webhook.call_count == 5
    
    @pytest.mark.asyncio
    async def test_worker_cancellation(self, worker):
        """Test worker cancellation handling."""
        # Arrange
        worker.running = False
        
        # Act
        start_task = asyncio.create_task(worker.start())
        
        # Wait a bit for worker to start
        await asyncio.sleep(0.05)
        
        # Cancel the worker
        start_task.cancel()
        
        # Wait for cancellation
        try:
            await start_task
        except asyncio.CancelledError:
            pass
        
        # Assert
        assert worker.running is False
    
    def test_worker_stop_cancels_tasks(self, worker):
        """Test that worker stop cancels running tasks."""
        # Arrange
        mock_task = Mock()
        mock_task.done.return_value = False
        worker.tasks = [mock_task]
        
        # Act
        worker.stop()
        
        # Assert
        mock_task.cancel.assert_called_once()
