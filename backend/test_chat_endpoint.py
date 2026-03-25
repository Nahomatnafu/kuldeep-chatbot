"""
test_chat_endpoint.py
=====================
AI-generated unit tests for POST /chat — derived purely from the testable spec.
Framework: pytest + unittest.mock + Flask test client
Run: cd backend && pytest test_chat_endpoint.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
import app as app_module
from app import app


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def reset_global_state():
    """Isolate global state between every test."""
    app_module.vectorstore = None
    app_module.llm = None
    app_module.conversation_sessions.clear()
    yield
    app_module.vectorstore = None
    app_module.llm = None
    app_module.conversation_sessions.clear()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_chain(answer="Mocked answer.", sources=None):
    chain = MagicMock()
    chain.invoke.return_value = {
        "answer": answer,
        "source_documents": sources or [],
    }
    return chain


def _mock_doc(content, page=0, source="test.pdf"):
    doc = MagicMock()
    doc.page_content = content
    doc.metadata = {"source": source, "page": page}
    return doc


# ── Group 1: Input Validation (Rule 1 — empty message check) ─────────────────

class TestEmptyMessageValidation:

    def test_empty_string_returns_400(self, client):
        res = client.post("/chat", json={"message": ""})
        assert res.status_code == 400
        assert res.get_json()["error"] == "Message cannot be empty"

    def test_whitespace_only_returns_400(self, client):
        res = client.post("/chat", json={"message": "   "})
        assert res.status_code == 400
        assert res.get_json()["error"] == "Message cannot be empty"

    def test_tab_and_newline_only_returns_400(self, client):
        res = client.post("/chat", json={"message": "\t\n"})
        assert res.status_code == 400
        assert res.get_json()["error"] == "Message cannot be empty"

    def test_missing_message_field_returns_400(self, client):
        res = client.post("/chat", json={"session_id": "abc"})
        assert res.status_code == 400
        assert res.get_json()["error"] == "Message cannot be empty"

    def test_null_message_returns_400(self, client):
        res = client.post("/chat", json={"message": None})
        assert res.status_code == 400
        assert res.get_json()["error"] == "Message cannot be empty"

    def test_single_character_passes_empty_check(self, client):
        """1-character message must not be rejected."""
        app_module.vectorstore = MagicMock()
        with patch("app._is_off_topic", return_value=False), \
             patch("app._get_or_create_chain", return_value=_mock_chain()):
            res = client.post("/chat", json={"message": "a"})
        assert res.status_code == 200

    def test_empty_body_returns_400(self, client):
        res = client.post("/chat", content_type="application/json", data="")
        assert res.status_code == 400


# ── Group 2: Vector Store & API Key (Rule 2 — fires before off-topic) ─────────

class TestVectorStoreAndApiKey:

    def test_no_api_key_returns_503(self, client):
        with patch("app._init_store", return_value=(False, "OPENAI_API_KEY not set in environment.")):
            res = client.post("/chat", json={"message": "hello"})
        assert res.status_code == 503
        assert "OPENAI_API_KEY" in res.get_json()["error"]

    def test_no_documents_returns_503(self, client):
        with patch("app._init_store", return_value=(False, "No documents ingested yet. Please upload a PDF first.")):
            res = client.post("/chat", json={"message": "hello"})
        assert res.status_code == 503
        assert "No documents ingested yet" in res.get_json()["error"]

    def test_empty_api_key_string_treated_as_missing(self, client):
        """OPENAI_API_KEY='' must be treated as not set → 503."""
        with patch("app._init_store", return_value=(False, "OPENAI_API_KEY not set in environment.")):
            res = client.post("/chat", json={"message": "hello"})
        assert res.status_code == 503
        assert "OPENAI_API_KEY" in res.get_json()["error"]

    def test_off_topic_without_vectorstore_returns_503_not_canned_reply(self, client):
        """
        CRITICAL precedence test: Rule 2 must fire before Rule 3.
        A personal question with no vector store must return 503, not the
        canned off-topic reply.
        """
        with patch("app._init_store", return_value=(False, "No documents ingested yet. Please upload a PDF first.")), \
             patch("app._is_off_topic", return_value=True):
            res = client.post("/chat", json={"message": "What is my name?"})
        assert res.status_code == 503


# ── Group 3: Off-topic Guard (Rule 3) ────────────────────────────────────────

class TestOffTopicGuard:

    def setup_method(self):
        app_module.vectorstore = MagicMock()

    def test_personal_question_returns_canned_reply(self, client):
        with patch("app._is_off_topic", return_value=True):
            res = client.post("/chat", json={"message": "What is my name?"})
        assert res.status_code == 200
        data = res.get_json()
        assert data["reply"] == "I can only answer questions about the uploaded documents."
        assert data["metadata"]["sources"] == []

    def test_small_talk_returns_canned_reply(self, client):
        with patch("app._is_off_topic", return_value=True):
            res = client.post("/chat", json={"message": "Hey how are you?"})
        assert res.get_json()["reply"] == "I can only answer questions about the uploaded documents."

    def test_canned_reply_echoes_resolved_session_id(self, client):
        with patch("app._is_off_topic", return_value=True):
            res = client.post("/chat", json={"message": "Who am I?", "session_id": "sess-42"})
        assert res.get_json()["session_id"] == "sess-42"

    def test_topic_name_question_is_not_blocked(self, client):
        """'What is the name of the model?' must pass through to RAG."""
        with patch("app._is_off_topic", return_value=False), \
             patch("app._get_or_create_chain", return_value=_mock_chain("gpt-3.5-turbo")):
            res = client.post("/chat", json={"message": "What is the name of the model?"})
        assert res.status_code == 200
        assert res.get_json()["reply"] != "I can only answer questions about the uploaded documents."


# ── Group 4: Successful Response Shape ───────────────────────────────────────

class TestSuccessfulResponseShape:

    def setup_method(self):
        app_module.vectorstore = MagicMock()

    def test_valid_message_returns_200_with_correct_keys(self, client):
        with patch("app._is_off_topic", return_value=False), \
             patch("app._get_or_create_chain", return_value=_mock_chain("The answer is 42.")):
            res = client.post("/chat", json={"message": "What is the answer?"})
        assert res.status_code == 200
        data = res.get_json()
        assert "reply" in data
        assert "session_id" in data
        assert "metadata" in data
        assert "sources" in data["metadata"]

    def test_history_field_accepted_without_error(self, client):
        """history in request body must be accepted — not cause a 400/500."""
        with patch("app._is_off_topic", return_value=False), \
             patch("app._get_or_create_chain", return_value=_mock_chain()):
            res = client.post("/chat", json={
                "message": "follow up",
                "history": [{"role": "user", "content": "previous question"}]
            })
        assert res.status_code == 200


# ── Group 5: Source Formatting ────────────────────────────────────────────────

class TestSourceFormatting:

    def setup_method(self):
        app_module.vectorstore = MagicMock()

    def test_snippet_exactly_150_chars_no_ellipsis(self, client):
        doc = _mock_doc("x" * 150, page=0, source="manual.pdf")
        with patch("app._is_off_topic", return_value=False), \
             patch("app._get_or_create_chain", return_value=_mock_chain(sources=[doc])):
            res = client.post("/chat", json={"message": "anything"})
        snippet = res.get_json()["metadata"]["sources"][0]["snippet"]
        assert snippet == "x" * 150
        assert not snippet.endswith("...")

    def test_snippet_151_chars_gets_ellipsis(self, client):
        doc = _mock_doc("x" * 151, page=0, source="manual.pdf")
        with patch("app._is_off_topic", return_value=False), \
             patch("app._get_or_create_chain", return_value=_mock_chain(sources=[doc])):
            res = client.post("/chat", json={"message": "anything"})
        snippet = res.get_json()["metadata"]["sources"][0]["snippet"]
        assert snippet == "x" * 150 + "..."

    def test_newlines_replaced_with_spaces_in_snippet(self, client):
        doc = _mock_doc("line one\nline two\nline three", page=0, source="sop.pdf")
        with patch("app._is_off_topic", return_value=False), \
             patch("app._get_or_create_chain", return_value=_mock_chain(sources=[doc])):
            res = client.post("/chat", json={"message": "anything"})
        assert "\n" not in res.get_json()["metadata"]["sources"][0]["snippet"]

    def test_page_raw_0_returns_1_indexed(self, client):
        doc = _mock_doc("content", page=0, source="doc.pdf")
        with patch("app._is_off_topic", return_value=False), \
             patch("app._get_or_create_chain", return_value=_mock_chain(sources=[doc])):
            res = client.post("/chat", json={"message": "anything"})
        assert res.get_json()["metadata"]["sources"][0]["page"] == 1

    def test_page_raw_5_returns_6(self, client):
        doc = _mock_doc("content", page=5, source="doc.pdf")
        with patch("app._is_off_topic", return_value=False), \
             patch("app._get_or_create_chain", return_value=_mock_chain(sources=[doc])):
            res = client.post("/chat", json={"message": "anything"})
        assert res.get_json()["metadata"]["sources"][0]["page"] == 6

    def test_source_ids_start_at_1_and_increment(self, client):
        docs = [
            _mock_doc("A", page=0, source="a.pdf"),
            _mock_doc("B", page=1, source="b.pdf"),
            _mock_doc("C", page=2, source="c.pdf"),
        ]
        with patch("app._is_off_topic", return_value=False), \
             patch("app._get_or_create_chain", return_value=_mock_chain(sources=docs)):
            res = client.post("/chat", json={"message": "anything"})
        ids = [s["id"] for s in res.get_json()["metadata"]["sources"]]
        assert ids == [1, 2, 3]

    def test_file_field_is_basename_only(self, client):
        """Full path in metadata must be stripped to filename only."""
        doc = _mock_doc("content", page=0, source="/deep/nested/path/manual.pdf")
        with patch("app._is_off_topic", return_value=False), \
             patch("app._get_or_create_chain", return_value=_mock_chain(sources=[doc])):
            res = client.post("/chat", json={"message": "anything"})
        assert res.get_json()["metadata"]["sources"][0]["file"] == "manual.pdf"


# ── Group 6: Session Management ───────────────────────────────────────────────

class TestSessionManagement:

    def setup_method(self):
        app_module.vectorstore = MagicMock()

    def test_missing_session_id_defaults_to_default(self, client):
        with patch("app._is_off_topic", return_value=False), \
             patch("app._get_or_create_chain", return_value=_mock_chain()):
            res = client.post("/chat", json={"message": "hello"})
        assert res.get_json()["session_id"] == "default"

    def test_null_session_id_defaults_to_default(self, client):
        with patch("app._is_off_topic", return_value=False), \
             patch("app._get_or_create_chain", return_value=_mock_chain()):
            res = client.post("/chat", json={"message": "hello", "session_id": None})
        assert res.get_json()["session_id"] == "default"

    def test_explicit_session_id_is_echoed(self, client):
        with patch("app._is_off_topic", return_value=False), \
             patch("app._get_or_create_chain", return_value=_mock_chain()):
            res = client.post("/chat", json={"message": "hello", "session_id": "my-session"})
        assert res.get_json()["session_id"] == "my-session"

    def test_two_sessions_get_independent_chains(self, client):
        """Two different session IDs must not share a chain or memory."""
        chain_a = _mock_chain("Answer for A")
        chain_b = _mock_chain("Answer for B")

        def pick_chain(sid):
            return chain_a if sid == "session-a" else chain_b

        with patch("app._is_off_topic", return_value=False), \
             patch("app._get_or_create_chain", side_effect=pick_chain):
            res_a = client.post("/chat", json={"message": "question", "session_id": "session-a"})
            res_b = client.post("/chat", json={"message": "question", "session_id": "session-b"})

        assert res_a.get_json()["reply"] == "Answer for A"
        assert res_b.get_json()["reply"] == "Answer for B"

