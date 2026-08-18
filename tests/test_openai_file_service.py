from io import BytesIO
from types import SimpleNamespace

import pytest

import app.services.openai_file_service as file_service


def upload_file(
    filename: str,
    content: bytes = b"fake pdf content",
):
    return SimpleNamespace(
        filename=filename,
        file=BytesIO(content),
    )


def test_rejects_non_pdf_file():
    upload = upload_file(
        filename="instruction.txt",
    )

    with pytest.raises(
        ValueError,
        match="must be a PDF",
    ):
        file_service.upload_instruction_pdf(
            upload
        )


def test_upload_returns_openai_file_id(
    monkeypatch,
):
    upload = upload_file(
        filename="instruction.pdf",
    )

    def fake_create(**kwargs):
        return SimpleNamespace(
            id="file_123",
        )

    monkeypatch.setattr(
        file_service.client.files,
        "create",
        fake_create,
    )

    result = (
        file_service.upload_instruction_pdf(
            upload
        )
    )

    assert result == "file_123"


def test_upload_sends_pdf_content(
    monkeypatch,
):
    content = b"%PDF-test-content"

    upload = upload_file(
        filename="instruction.pdf",
        content=content,
    )

    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)

        uploaded_file = kwargs["file"]

        assert uploaded_file.read() == content

        return SimpleNamespace(
            id="file_123",
        )

    monkeypatch.setattr(
        file_service.client.files,
        "create",
        fake_create,
    )

    file_service.upload_instruction_pdf(
        upload
    )

    assert captured["purpose"] == (
        "user_data"
    )


def test_upload_sets_expiration(
    monkeypatch,
):
    upload = upload_file(
        filename="instruction.pdf",
    )

    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)

        return SimpleNamespace(
            id="file_123",
        )

    monkeypatch.setattr(
        file_service.client.files,
        "create",
        fake_create,
    )

    file_service.upload_instruction_pdf(
        upload
    )

    assert captured["expires_after"] == {
        "anchor": "created_at",
        "seconds": 3600,
    }


def test_filename_defaults_to_instruction_pdf(
    monkeypatch,
):
    upload = upload_file(
        filename="instruction.pdf",
    )

    upload.filename = None

    monkeypatch.setattr(
        file_service.client.files,
        "create",
        lambda **kwargs: SimpleNamespace(
            id="file_123",
        ),
    )

    result = (
        file_service.upload_instruction_pdf(
            upload
        )
    )

    assert result == "file_123"


def test_delete_openai_file(
    monkeypatch,
):
    captured = {}

    def fake_delete(file_id):
        captured["file_id"] = file_id

    monkeypatch.setattr(
        file_service.client.files,
        "delete",
        fake_delete,
    )

    file_service.delete_openai_file(
        "file_123"
    )

    assert captured["file_id"] == (
        "file_123"
    )


def test_delete_openai_file_ignores_errors(
    monkeypatch,
):
    def fake_delete(file_id):
        raise RuntimeError(
            "OpenAI unavailable"
        )

    monkeypatch.setattr(
        file_service.client.files,
        "delete",
        fake_delete,
    )

    file_service.delete_openai_file(
        "file_123"
    )