"""query helpers for a first RAG chatbot project."""

import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI


def get_embeddings() -> OpenAIEmbeddings:
    """Create embeddings model using your OpenAI API key."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment")

    return OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key)


def get_vectorstore(chroma_dir: str) -> Chroma:
    """Open existing Chroma vector database."""
    return Chroma(persist_directory=chroma_dir, embedding_function=get_embeddings())


def retrieve_context(question: str, chroma_dir: str, k: int = 4) -> Tuple[str, List[Dict[str, Any]]]:
    """Retrieve top-k chunks and return combined context + structured source refs."""
    vectorstore = get_vectorstore(chroma_dir)
    docs = vectorstore.similarity_search(question, k=k)

    context_parts = []
    sources: List[Dict[str, Any]] = []
    seen = set()
    for doc in docs:
        context_parts.append(doc.page_content)
        source_path = str(doc.metadata.get("source", "Unknown"))
        page_raw = doc.metadata.get("page")
        page = page_raw + 1 if isinstance(page_raw, int) else None
        key = (source_path, page)
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            {
                "source_path": source_path,
                "filename": Path(source_path).name,
                "page": page,
            }
        )

    context = "\n\n".join(context_parts)
    return context, sources


def generate_answer(question: str, context: str) -> str:
    """Generate final answer using OpenAI chat model."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment")

    client = OpenAI(api_key=api_key)
    prompt = (
        "You are a helpful assistant. Answer ONLY from the provided context.\n"
        "If the context is insufficient, say you do not have enough information.\n\n"
        f"Context:\n{context}\n\n"
        f"Question:\n{question}"
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or "I do not have enough information."


def is_insufficient_answer(answer: str) -> bool:
    """Return True when the answer states there is not enough information."""
    text = answer.strip().lower()
    patterns = [
        "i do not have enough information",
        "i don't have enough information",
        "not enough information",
        "insufficient information",
        "cannot answer based on the context",
        "can't answer based on the context",
    ]
    return any(pattern in text for pattern in patterns)


def ask_question(question: str, chroma_dir: str) -> Dict:
    """Minimal RAG query flow: retrieve context then generate answer."""
    context, sources = retrieve_context(question=question, chroma_dir=chroma_dir, k=4)
    answer = generate_answer(question=question, context=context)
    # If the model says there is not enough context, hide source references.
    if is_insufficient_answer(answer):
        return {"answer": answer, "sources": []}
    return {"answer": answer, "sources": sources}
