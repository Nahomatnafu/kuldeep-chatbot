"""
Ragas Evaluation Utilities — Kuldeep RAG Chatbot
=================================================
Evaluates RAG pipeline outputs with four Ragas metrics:

  faithfulness        – Is every claim in the answer grounded in the retrieved context?
  answer_relevancy    – Is the answer actually relevant to the question asked?
  context_precision   – Are the retrieved chunks relevant / useful for the question?
  context_recall      – Does the retrieved context cover what the reference answer says?

faithfulness + answer_relevancy require only (question, answer, contexts).
context_precision + context_recall additionally require a ground_truth reference answer.

Compatible with Ragas 0.4.x (EvaluationDataset / SingleTurnSample + llm_factory API).

Usage
-----
from tests.ragas_eval import score_outputs, print_score_table

rows = [
    {
        "question":     "What is the safe hot-holding temperature?",
        "answer":       "135°F / 57°C per the FDA Food Code.",
        "contexts":     ["TIME/TEMPERATURE CONTROL FOR SAFETY food shall be maintained at 57°C (135°F) ..."],
        "ground_truth": "The safe hot-holding temperature is 135°F (57°C).",
    }
]

scores = score_outputs(rows, include_retrieval_metrics=True)
print_score_table(scores)
"""

from __future__ import annotations

import os
from typing import Optional

# Load .env from the project root (one level above tests/)
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

try:
    import ragas  # noqa: F401
except ImportError as exc:
    raise ImportError(
        "ragas is not installed.\n"
        "Activate your venv and run:  pip install ragas\n"
        f"Original error: {exc}"
    ) from exc

from ragas import evaluate
from ragas.dataset_schema import SingleTurnSample, EvaluationDataset
# Import from ragas.metrics (not ragas.metrics.collections) — the .collections
# variants are a different class hierarchy not derived from ragas.metrics.base.Metric
# and are rejected by evaluate().  The ragas.metrics path is what works with evaluate().
import warnings as _warnings
with _warnings.catch_warnings():
    _warnings.simplefilter("ignore", DeprecationWarning)
    from ragas.metrics import (  # type: ignore
        Faithfulness,
        AnswerRelevancy,
        ContextPrecision,
        ContextRecall,
    )

# ── LLM + Embeddings factory ──────────────────────────────────────────────────

def _build_llm_and_embeddings():
    """
    Build the Ragas-native LLM and embeddings objects required by Ragas 0.4.x.
    Metrics in ragas.metrics.collections require InstructorLLM (via llm_factory),
    NOT LangchainLLMWrapper.
    """
    import openai
    from ragas.llms import llm_factory

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Add it to your .env file or environment."
        )

    client = openai.OpenAI(api_key=api_key)
    # max_tokens=8192 overrides Ragas's default starting limit of 1024 tokens.
    # Without this, Ragas retries at 1024→2048→3072 tokens and still fails on
    # verbose answers that generate 20+ faithfulness statements (e.g. FDA handwashing,
    # CNC G-code list).  8192 is well within gpt-4o-mini's 16K output limit.
    llm = llm_factory("gpt-4o-mini", client=client, max_tokens=8192)

    # AnswerRelevancy (ragas.metrics._answer_relevance) is a LangChain-style metric
    # and calls embeddings.embed_query() — so we must provide a LangchainEmbeddingsWrapper,
    # NOT ragas.embeddings.OpenAIEmbeddings (which lacks embed_query).
    from langchain_openai import OpenAIEmbeddings as LCOpenAIEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper
    embeddings = LangchainEmbeddingsWrapper(
        LCOpenAIEmbeddings(model="text-embedding-ada-002", api_key=api_key)
    )

    return llm, embeddings


def _make_metrics(include_retrieval: bool):
    """
    Instantiate and return the requested Ragas metric objects.
    Each metric receives the LLM (and embeddings) at construction time,
    which is required by Ragas 0.4.x — metrics are NOT re-usable across
    evaluate() calls, so we create fresh instances every time.
    """
    llm, embeddings = _build_llm_and_embeddings()

    metrics = [
        Faithfulness(llm=llm),
        AnswerRelevancy(llm=llm, embeddings=embeddings),
    ]

    if include_retrieval:
        metrics += [
            ContextPrecision(llm=llm),
            ContextRecall(llm=llm),
        ]

    return metrics


# ── Dataset builder ───────────────────────────────────────────────────────────

def _build_dataset(rows: list[dict]) -> EvaluationDataset:
    """
    Build a Ragas EvaluationDataset from a list of row dicts.

    Required keys: question, answer, contexts (list[str])
    Optional key:  ground_truth (str)
    """
    samples = [
        SingleTurnSample(
            user_input=r["question"],
            response=r["answer"],
            retrieved_contexts=r["contexts"],
            reference=r.get("ground_truth"),
        )
        for r in rows
    ]
    return EvaluationDataset(samples=samples)


# ── Public API ────────────────────────────────────────────────────────────────

def score_outputs(
    rows: list[dict],
    include_retrieval_metrics: bool = False,
) -> dict[str, float]:
    """
    Evaluate a list of RAG outputs with Ragas and return average scores.

    Args:
        rows:
            List of dicts with keys ``question``, ``answer``, ``contexts``
            (and optionally ``ground_truth``).
        include_retrieval_metrics:
            When True, also compute ``context_precision`` and ``context_recall``.
            Every row MUST supply a ``ground_truth`` string.

    Returns:
        Dict mapping metric name → average score (0.0 – 1.0).
    """
    if not rows:
        raise ValueError("rows list is empty.")

    if include_retrieval_metrics:
        missing = [i for i, r in enumerate(rows) if not r.get("ground_truth")]
        if missing:
            raise ValueError(
                f"include_retrieval_metrics=True but rows at indices {missing} "
                "are missing 'ground_truth'."
            )

    dataset = _build_dataset(rows)
    metrics = _make_metrics(include_retrieval=include_retrieval_metrics)

    result = evaluate(dataset=dataset, metrics=metrics)

    _KNOWN = {"faithfulness", "answer_relevancy", "context_precision", "context_recall"}
    scores: dict[str, float] = {}

    if hasattr(result, "to_pandas"):
        df = result.to_pandas()
        for col in df.columns:
            if col in _KNOWN:
                scores[col] = float(df[col].mean())
    elif hasattr(result, "__iter__"):
        for k, v in result.items():
            if k in _KNOWN:
                try:
                    scores[k] = float(v)
                except (TypeError, ValueError):
                    pass

    return scores


def score_single(
    question: str,
    answer: str,
    contexts: list[str],
    ground_truth: Optional[str] = None,
    include_retrieval_metrics: bool = False,
) -> dict[str, float]:
    """
    Convenience wrapper to score a single (question, answer, contexts) tuple.
    """
    row: dict = {"question": question, "answer": answer, "contexts": contexts}
    if ground_truth is not None:
        row["ground_truth"] = ground_truth
    return score_outputs([row], include_retrieval_metrics=include_retrieval_metrics)


def print_score_table(
    scores: dict[str, float],
    thresholds: Optional[dict[str, float]] = None,
    title: str = "Ragas Evaluation Scores",
) -> None:
    """
    Pretty-print a score table with optional pass/fail indicators.
    """
    width = 65
    print(f"\n{'─' * width}")
    print(f"  {title}")
    print(f"{'─' * width}")
    _ORDER = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    for metric in _ORDER:
        if metric not in scores:
            continue
        value = scores[metric]
        bar   = "█" * int(value * 20)
        if thresholds and metric in thresholds:
            passed = value >= thresholds[metric]
            status = "  PASS ✓" if passed else f"  FAIL ✗ (need ≥ {thresholds[metric]:.2f})"
        else:
            status = ""
        print(f"  {metric:<25} {value:.4f}  [{bar:<20}]{status}")
    print(f"{'─' * width}\n")
