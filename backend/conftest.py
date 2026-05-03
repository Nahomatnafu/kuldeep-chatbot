"""
conftest.py
===========
Mocks out all heavy third-party dependencies (LangChain, OpenAI, ChromaDB)
before app.py is imported, so pytest's import hook never triggers their
bytecode compilation. This keeps unit tests fast and AV-safe.
"""
import sys
from unittest.mock import MagicMock
from dataclasses import dataclass, field

_MOCKED = [
    "langchain_openai",
    "langchain_openai.embeddings",
    "langchain_community",
    "langchain_community.vectorstores",
    "langchain_community.document_loaders",
    "langchain_community.document_loaders.pdf",
    "langchain",
    "langchain.prompts",
    "langchain.memory",
    "langchain_text_splitters",
    "langchain_core",
    "langchain_core.documents",
    "langsmith",
    "opentelemetry",
    "chromadb",
    "chromadb.utils",
    "chromadb.utils.embedding_functions",
]

for _mod in _MOCKED:
    sys.modules.setdefault(_mod, MagicMock())

# Provide specific named symbols the app imports directly
from unittest.mock import MagicMock as _M

sys.modules["langchain_openai"].OpenAIEmbeddings = _M
sys.modules["langchain_openai"].ChatOpenAI = _M
sys.modules["langchain_community.document_loaders"].PyPDFLoader = _M
sys.modules["langchain.prompts"].PromptTemplate = _M
sys.modules["langchain.memory"].ConversationBufferMemory = _M
sys.modules["chromadb.utils.embedding_functions"].OpenAIEmbeddingFunction = _M


@dataclass
class _Document:
    page_content: str
    metadata: dict = field(default_factory=dict)


class _RecursiveCharacterTextSplitter:
    def __init__(self, chunk_size=1000, chunk_overlap=200, **_kwargs):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_documents(self, docs):
        chunks = []
        step = max(1, self.chunk_size - self.chunk_overlap)
        for doc in docs:
            text = doc.page_content or ""
            if not text:
                continue
            for start in range(0, len(text), step):
                chunk_text = text[start:start + self.chunk_size]
                if chunk_text:
                    chunks.append(_Document(page_content=chunk_text, metadata=dict(doc.metadata)))
                if start + self.chunk_size >= len(text):
                    break
        return chunks


sys.modules["langchain_core.documents"].Document = _Document
sys.modules["langchain_text_splitters"].RecursiveCharacterTextSplitter = _RecursiveCharacterTextSplitter

