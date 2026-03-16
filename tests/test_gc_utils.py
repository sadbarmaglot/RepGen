"""Тесты для GCSClient."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.fixture
def gcs_client():
    """GCSClient с замоканным storage backend."""
    with patch("common.gc_utils.storage_client") as mock_storage:
        mock_bucket = MagicMock()
        mock_storage.bucket.return_value = mock_bucket

        from common.gc_utils import GCSClient

        client = GCSClient("test-bucket")
        client._bucket = mock_bucket
        yield client, mock_bucket


class TestUploadBytes:

    @pytest.mark.asyncio
    async def test_uploads_and_returns_filename(self, gcs_client):
        client, mock_bucket = gcs_client

        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob

        result = await client.upload_bytes(b"hello", "test.txt", "text/plain")

        assert result == "test.txt"
        mock_bucket.blob.assert_called_once_with("test.txt")
        assert mock_blob.content_type == "text/plain"
        mock_blob.upload_from_string.assert_called_once_with(
            b"hello", content_type="text/plain"
        )


class TestDownload:

    @pytest.mark.asyncio
    async def test_downloads_existing_file(self, gcs_client):
        client, mock_bucket = gcs_client

        mock_blob = MagicMock()
        mock_blob.exists.return_value = True
        mock_blob.download_as_bytes.return_value = b"pdf-content"
        mock_blob.content_type = "application/pdf"
        mock_bucket.blob.return_value = mock_blob

        data, mime = await client.download("report.pdf")

        assert data == b"pdf-content"
        assert mime == "application/pdf"

    @pytest.mark.asyncio
    async def test_raises_on_missing_file(self, gcs_client):
        client, mock_bucket = gcs_client

        mock_blob = MagicMock()
        mock_blob.exists.return_value = False
        mock_bucket.blob.return_value = mock_blob

        with pytest.raises(FileNotFoundError):
            await client.download("nonexistent.pdf")


class TestDelete:

    @pytest.mark.asyncio
    async def test_deletes_existing_file(self, gcs_client):
        client, mock_bucket = gcs_client

        mock_blob = MagicMock()
        mock_blob.exists.return_value = True
        mock_bucket.blob.return_value = mock_blob

        with patch("common.gc_utils.redis_service") as mock_redis:
            mock_redis.clear_signed_url = AsyncMock()
            result = await client.delete("old.jpg")

        assert result is True
        mock_blob.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_false_for_missing(self, gcs_client):
        client, mock_bucket = gcs_client

        mock_blob = MagicMock()
        mock_blob.exists.return_value = False
        mock_bucket.blob.return_value = mock_blob

        result = await client.delete("nope.jpg")

        assert result is False


class TestGetBlobSize:

    @pytest.mark.asyncio
    async def test_returns_size(self, gcs_client):
        client, mock_bucket = gcs_client

        mock_blob = MagicMock()
        mock_blob.size = 12345
        mock_bucket.blob.return_value = mock_blob

        size = await client.get_blob_size("file.pdf")

        assert size == 12345

    @pytest.mark.asyncio
    async def test_returns_none_on_error(self, gcs_client):
        client, mock_bucket = gcs_client

        mock_blob = MagicMock()
        mock_blob.reload.side_effect = Exception("not found")
        mock_bucket.blob.return_value = mock_blob

        size = await client.get_blob_size("missing.pdf")

        assert size is None
