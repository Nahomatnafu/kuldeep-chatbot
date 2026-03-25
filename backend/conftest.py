"""
conftest.py
===========
Mocks out all heavy third-party dependencies (LangChain, OpenAI, FAISS)
before app.py is imported, so pytest's import hook never triggers their
bytecode compilation. This keeps unit tests fast and AV-safe.
"""
import sys
from unittest.mock import MagicMock

_MOCKED = [
    "langchain_openai",
    "langchain_openai.embeddings",
    "langchain_community",
    "langchain_community.vectorstores",
    "langchain_community.vectorstores.faiss",
    "langchain_community.document_loaders",
    "langchain_community.document_loaders.pdf",
    "langchain",
    "langchain.chains",
    "langchain.prompts",
    "langchain.memory",
    "langchain_text_splitters",
    "langsmith",
    "opentelemetry",
    "faiss",
]

for _mod in _MOCKED:
    sys.modules.setdefault(_mod, MagicMock())

# Provide specific named symbols the app imports directly
from unittest.mock import MagicMock as _M

sys.modules["langchain_openai"].OpenAIEmbeddings = _M
sys.modules["langchain_openai"].ChatOpenAI = _M
sys.modules["langchain_community.vectorstores"].FAISS = _M
sys.modules["langchain_community.document_loaders"].PyPDFLoader = _M
sys.modules["langchain.chains"].ConversationalRetrievalChain = _M
sys.modules["langchain.prompts"].PromptTemplate = _M
sys.modules["langchain.memory"].ConversationBufferMemory = _M
sys.modules["langchain_text_splitters"].RecursiveCharacterTextSplitter = _M

