"""Тесты для DocumentReviewService — парсинг, reference docs, LLM review."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from api.services.document_review_service import DocumentReviewService


class TestParseDocx:

    def test_paragraphs_extracted(self, sample_docx_bytes):
        text = DocumentReviewService._parse_docx(sample_docx_bytes)
        assert "Заголовок отчёта" in text
        assert "ул. Ленина, д. 1" in text

    def test_tables_extracted(self, sample_docx_bytes):
        text = DocumentReviewService._parse_docx(sample_docx_bytes)
        assert "Этажность" in text
        assert "3" in text

    def test_empty_paragraphs_skipped(self, sample_docx_bytes):
        text = DocumentReviewService._parse_docx(sample_docx_bytes)
        lines = [l for l in text.split("\n") if l.strip()]
        # Не должно быть пустых строк
        assert all(line.strip() for line in lines)

    def test_empty_docx(self, empty_docx_bytes):
        text = DocumentReviewService._parse_docx(empty_docx_bytes)
        assert text.strip() == ""


class TestParsePdf:

    def test_text_extracted(self, sample_pdf_bytes):
        text = DocumentReviewService._parse_pdf(sample_pdf_bytes)
        assert "Technical Report" in text
        assert "Moscow" in text

    def test_empty_pdf(self):
        import pymupdf

        doc = pymupdf.open()
        doc.new_page()  # пустая страница
        pdf_bytes = doc.tobytes()
        doc.close()

        text = DocumentReviewService._parse_pdf(pdf_bytes)
        assert text.strip() == ""


class TestLoadReferenceTexts:

    def test_loads_txt_files(self, reference_docs_dir):
        service = DocumentReviewService()

        with patch(
            "api.services.document_review_service.REFERENCE_DOCS_DIR",
            reference_docs_dir,
        ):
            result = service._load_reference_texts()

        assert "ГОСТ 31937-2024" in result
        assert "СП 20.13330.2016" in result

    def test_caches_result(self, reference_docs_dir):
        service = DocumentReviewService()

        with patch(
            "api.services.document_review_service.REFERENCE_DOCS_DIR",
            reference_docs_dir,
        ):
            result1 = service._load_reference_texts()
            result2 = service._load_reference_texts()

        assert result1 is result2  # тот же объект — из кэша

    def test_missing_dir_returns_empty(self, tmp_path):
        service = DocumentReviewService()

        with patch(
            "api.services.document_review_service.REFERENCE_DOCS_DIR",
            tmp_path / "nonexistent",
        ):
            result = service._load_reference_texts()

        assert result == ""

    def test_empty_dir_returns_empty(self, tmp_path):
        empty_dir = tmp_path / "empty_refs"
        empty_dir.mkdir()
        service = DocumentReviewService()

        with patch(
            "api.services.document_review_service.REFERENCE_DOCS_DIR",
            empty_dir,
        ):
            result = service._load_reference_texts()

        assert result == ""


class TestReviewDocument:

    @pytest.mark.asyncio
    async def test_empty_document_skips_llm(self, empty_docx_bytes):
        service = DocumentReviewService()

        with patch.object(service, "parse_document", new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = "   "

            result = await service.review_document("test.docx")

        assert result["review_result"] == "Документ пуст или не содержит текста."
        assert result["extracted_text"] == ""

    @pytest.mark.asyncio
    async def test_calls_llm_for_non_empty(self):
        service = DocumentReviewService()

        with (
            patch.object(
                service, "parse_document", new_callable=AsyncMock
            ) as mock_parse,
            patch.object(
                service, "_run_llm_review", new_callable=AsyncMock
            ) as mock_llm,
        ):
            mock_parse.return_value = "Текст отчёта"
            mock_llm.return_value = "🔴 КРИТ №1\nГде: титульный лист"

            result = await service.review_document("report.docx")

        assert result["review_result"] == "🔴 КРИТ №1\nГде: титульный лист"
        assert result["extracted_text"] == "Текст отчёта"
        mock_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_passes_prompt_to_llm(self):
        service = DocumentReviewService()

        with (
            patch.object(
                service, "parse_document", new_callable=AsyncMock
            ) as mock_parse,
            patch.object(
                service, "_run_llm_review", new_callable=AsyncMock
            ) as mock_llm,
        ):
            mock_parse.return_value = "Текст"
            mock_llm.return_value = "Результат"

            await service.review_document("doc.docx", prompt="Проверь даты")

        mock_llm.assert_called_once_with("Текст", "Проверь даты")


class TestRunLlmReview:

    @pytest.mark.asyncio
    async def test_builds_correct_messages(self, reference_docs_dir):
        service = DocumentReviewService()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Замечаний нет"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        service._openai_client = mock_client

        with patch(
            "api.services.document_review_service.REFERENCE_DOCS_DIR",
            reference_docs_dir,
        ):
            service._reference_texts = None  # сбросить кэш
            result = await service._run_llm_review("Отчёт текст", "Доп. указания")

        assert result == "Замечаний нет"

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        user_msg = messages[1]["content"]

        assert "НОРМАТИВНЫЕ ДОКУМЕНТЫ" in user_msg
        assert "ГОСТ 31937-2024" in user_msg
        assert "Отчёт текст" in user_msg
        assert "Доп. указания" in user_msg

    @pytest.mark.asyncio
    async def test_no_reference_docs(self, tmp_path):
        service = DocumentReviewService()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Результат"
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 20

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        service._openai_client = mock_client

        with patch(
            "api.services.document_review_service.REFERENCE_DOCS_DIR",
            tmp_path / "nope",
        ):
            service._reference_texts = None
            result = await service._run_llm_review("Текст")

        assert result == "Результат"

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        user_msg = messages[1]["content"]

        assert "НОРМАТИВНЫЕ ДОКУМЕНТЫ" not in user_msg

    @pytest.mark.asyncio
    async def test_no_prompt(self, tmp_path):
        service = DocumentReviewService()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "OK"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        service._openai_client = mock_client

        with patch(
            "api.services.document_review_service.REFERENCE_DOCS_DIR",
            tmp_path / "nope",
        ):
            service._reference_texts = None
            result = await service._run_llm_review("Текст")

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        user_msg = messages[1]["content"]

        assert "ДОПОЛНИТЕЛЬНЫЕ УКАЗАНИЯ" not in user_msg
