"""Тесты для эндпоинтов /documents/*."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """TestClient с замоканной авторизацией через dependency_overrides."""
    from main import app
    from api.dependencies.auth_dependencies import get_current_user
    from api.models.entities import User

    mock_user = MagicMock(spec=User)
    mock_user.id = 1

    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestUploadDocument:

    def test_rejects_invalid_extension(self, client):
        resp = client.post(
            "/repgen/documents/upload",
            files={"file": ("report.txt", b"hello", "text/plain")},
        )
        assert resp.status_code == 400
        assert "Недопустимый формат" in resp.json()["detail"]

    def test_rejects_oversized_file(self, client):
        with patch(
            "api.routes.document_review.MAX_DOCUMENT_SIZE", 10
        ):
            resp = client.post(
                "/repgen/documents/upload",
                files={"file": ("report.docx", b"x" * 20, "application/octet-stream")},
            )
        assert resp.status_code == 400
        assert "слишком большой" in resp.json()["detail"]

    def test_successful_upload(self, client):
        with patch(
            "api.routes.document_review.documents_storage"
        ) as mock_storage:
            mock_storage.upload_bytes = AsyncMock(return_value="uuid.docx")

            resp = client.post(
                "/repgen/documents/upload",
                files={"file": ("report.docx", b"PK\x03\x04", "application/octet-stream")},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["document_name"].endswith(".docx")
        assert "wordprocessingml" in data["mime_type"]


class TestReviewDocument:

    def test_not_found(self, client):
        with patch(
            "api.routes.document_review.document_review_service"
        ) as mock_svc:
            mock_svc.review_document = AsyncMock(
                side_effect=FileNotFoundError("not found")
            )

            resp = client.post(
                "/repgen/documents/review",
                json={"document_name": "missing.docx"},
            )

        assert resp.status_code == 404

    def test_successful_review(self, client):
        with patch(
            "api.routes.document_review.document_review_service"
        ) as mock_svc:
            mock_svc.review_document = AsyncMock(
                return_value={
                    "document_name": "test.docx",
                    "extracted_text": "Текст отчёта",
                    "review_result": "🔴 КРИТ №1",
                }
            )

            resp = client.post(
                "/repgen/documents/review",
                json={"document_name": "test.docx", "prompt": "Проверь даты"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["review_result"] == "🔴 КРИТ №1"
        assert data["extracted_text"] == "Текст отчёта"
