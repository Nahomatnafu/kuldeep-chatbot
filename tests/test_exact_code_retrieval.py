from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import app as app_module  # noqa: E402
from langchain_core.documents import Document  # noqa: E402


class FakeCollection:
    def __init__(self, docs: list[Document]) -> None:
        self.docs = docs

    def count(self) -> int:
        return len(self.docs)

    def get(self, **_kwargs) -> dict:
        return {
            "documents": [doc.page_content for doc in self.docs],
            "metadatas": [doc.metadata for doc in self.docs],
        }


def _doc(text: str, source: str, chunk_index: int) -> Document:
    return Document(
        page_content=text,
        metadata={
            "source": source,
            "filename": Path(source).name,
            "chunk_index": chunk_index,
        },
    )


@pytest.fixture()
def exact_code_docs() -> list[Document]:
    return [
        _doc("36\nBasic machine tool page number only.", "knowledge_base/basic_machine_tool.pdf", 1),
        _doc(
            "18x43 The frequency measured on L1 is lower than the thresholds. "
            "Reselect country code and verify AC frequency and voltages on site.",
            "knowledge_base/server_installation-guide-error-codes.pdf",
            2,
        ),
        _doc(
            "18x60 Grid is down. When AC grid voltage returns the inverter will restart "
            "after the reconnection time. Consult with the grid operator if the problem persists.",
            "knowledge_base/server_installation-guide-error-codes.pdf",
            3,
        ),
        _doc(
            "18x6F Grid voltage is above the country limit. Verify the inverter country setting, "
            "verify AC grid voltage, use larger gauge AC wire if needed, and consult the grid operator.",
            "knowledge_base/server_installation-guide-error-codes.pdf",
            4,
        ),
        _doc("32x61 EVENT_TEMPRATURE_AC_LOCK listed in another error-code section.", "knowledge_base/server_installation-guide-error-codes.pdf", 5),
        _doc("E-100 Startup failed because the configuration file is missing.", "knowledge_base/server_installation-guide-error-codes.pdf", 6),
    ]


@pytest.fixture(autouse=True)
def reset_keyword_cache():
    app_module._keyword_corpus_cache.clear()
    yield
    app_module._keyword_corpus_cache.clear()


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("18x43", ["18x43"]),
        ("18x60", ["18x60"]),
        ("18x6f", ["18x6f"]),
        ("32x61", ["32x61"]),
        ("E-100", ["e-100"]),
        ("what does error code 18x6f mean?", ["18x6f"]),
        ("no identifier here", []),
    ],
)
def test_extract_code_tokens(query, expected):
    assert app_module._extract_code_tokens(query) == expected


@pytest.mark.parametrize(
    ("query", "expected_code"),
    [
        ("18x43", "18x43"),
        ("18x60", "18x60"),
        ("18x6f", "18x6f"),
        ("what does error code 18x6f mean?", "18x6f"),
        ("show troubleshooting for 18x60", "18x60"),
    ],
)
def test_exact_code_chunks_rank_before_vector_noise(monkeypatch, exact_code_docs, query, expected_code):
    monkeypatch.setattr(app_module, "collection", FakeCollection(exact_code_docs))
    monkeypatch.setattr(
        app_module,
        "_similarity_search_with_score",
        lambda *_args, **_kwargs: [(exact_code_docs[0], 0.01)],
    )

    hits = app_module._hybrid_search(query, k=3)

    assert hits
    assert expected_code.lower() in hits[0].page_content.lower()
    assert Path(hits[0].metadata["source"]).name == "server_installation-guide-error-codes.pdf"


def test_exact_identifier_search_returns_empty_for_missing_code(monkeypatch, exact_code_docs):
    monkeypatch.setattr(app_module, "collection", FakeCollection(exact_code_docs))

    assert app_module._exact_identifier_search("18x6A", k=3) == []
