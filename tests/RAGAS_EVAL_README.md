# RAG Evaluation — Kuldeep Chatbot

Two files in the `tests/` folder implement automated quality evaluation for the chatbot's RAG pipeline:

| File | Purpose |
|---|---|
| `ragas_eval.py` | Core evaluation library — wraps Ragas, exposes simple functions |
| `regression_test.py` | Full regression pipeline — queries the live chatbot and scores it |

---

## How it works

The system uses [Ragas](https://docs.ragas.io/) to score chatbot outputs across four metrics. Ragas uses an LLM (gpt-4o-mini) to judge each response — it does **not** just compare strings.

### The four metrics

| Metric | What it measures | Needs ground truth? |
|---|---|---|
| **faithfulness** | Are all claims in the answer actually supported by the retrieved context? Catches hallucination. | No |
| **answer_relevancy** | Does the answer actually address the question asked? Catches off-topic responses. | No |
| **context_precision** | Are the retrieved chunks relevant and useful for the question? Measures retriever quality. | Yes |
| **context_recall** | Does the retrieved context cover the key facts in the reference answer? | Yes |

All scores are in the range **0.0 – 1.0**. Higher is better.

### How each metric is computed

**Faithfulness:**
1. Ragas breaks the chatbot's answer into individual atomic statements ("G41 is a CNC code", "hot food must be held at 135°F", etc.)
2. Each statement is checked against the retrieved context chunks
3. `faithfulness = supported statements / total statements`

**Answer relevancy:**
1. Ragas generates several possible questions that the answer could be responding to
2. Those generated questions are embedded and compared to the original question using cosine similarity
3. High similarity → the answer is on-topic

**Context precision:**
1. Each retrieved chunk is ranked by how useful it actually was for answering the question
2. Relevant chunks ranked higher = better precision

**Context recall:**
1. The ground truth answer is broken into statements
2. Each statement is checked against the context to see if it was retrievable
3. `context_recall = statements found in context / total statements`

---

## Requirements

```
OPENAI_API_KEY=<your key>   # in .env at the project root
```

```bash
pip install ragas langchain-openai
```

The Flask backend must be running on `http://localhost:5000` for the regression pipeline.

---

## Running the regression test

Start the backend first, then from the project root:

```bash
# Report scores — does NOT fail on threshold violations
python tests/regression_test.py --no-fail

# Full CI mode — exits with code 1 if any metric is below its threshold
python tests/regression_test.py

# Override specific thresholds
python tests/regression_test.py --faithfulness 0.80 --answer-relevancy 0.75
```

Results are saved to `tests/regression_results_<timestamp>.json` after every run.

### Default thresholds

| Metric | Threshold |
|---|---|
| faithfulness | 0.70 |
| answer_relevancy | 0.70 |
| context_precision | 0.60 |
| context_recall | 0.60 |

### Score history

#### Run 1 — 2026-04-22 | chatbot: gpt-3.5-turbo | Ragas judge: gpt-3.5-turbo

| Metric | Score | Notes |
|---|---|---|
| faithfulness | 0.796 | |
| answer_relevancy | 0.912 | |
| context_precision | 0.872 | Inflated — gpt-3.5-turbo judge was lenient |
| context_recall | 0.878 | Inflated — gpt-3.5-turbo judge was lenient |

#### Run 2 — 2026-04-24 | chatbot: gpt-4o-mini | Ragas judge: gpt-4o-mini (max_tokens=8192)

| Metric | Score | Notes |
|---|---|---|
| faithfulness | 0.876 | Improved — gpt-4o-mini stays closer to retrieved context |
| answer_relevancy | 0.971 | Improved |
| context_precision | 0.651 | Stricter judge; also affected by ground truth quality (see below) |
| context_recall | 0.499 | **FAIL** — stricter judge + ground truths not derived from actual document text |

**Why context_recall dropped:** gpt-4o-mini judges whether ground truth facts are *explicitly present* in the retrieved chunks, while gpt-3.5-turbo would infer or assume support from implied content. The current ground truths were written from general domain knowledge rather than from the actual text of the uploaded documents — so many facts are phrased differently from or not literally present in the chunks. This causes gpt-4o-mini to mark them as not supported.

The Run 2 scores are more trustworthy as a quality signal. The context_recall score in particular will only become reliable once ground truths are rewritten to match what the documents actually say. See the [Adding or editing test cases](#adding-or-editing-test-cases) section for guidance.

**Current baseline** (use Run 2 for regression comparisons going forward):

| Metric | Score | Threshold |
|---|---|---|
| faithfulness | 0.876 | 0.70 ✓ |
| answer_relevancy | 0.971 | 0.70 ✓ |
| context_precision | 0.651 | 0.60 ✓ |
| context_recall | 0.499 | 0.60 ✗ |

context_recall is expected to remain below threshold until ground truths are updated. Run with `--no-fail` until that work is done.

---

## Using `ragas_eval.py` directly

You can call the evaluation library on any arbitrary rows without the full regression pipeline:

```python
import sys
sys.path.insert(0, 'tests')
from ragas_eval import score_outputs, score_single, print_score_table

# Score a list of rows
rows = [
    {
        "question":     "What is the safe hot-holding temperature?",
        "answer":       "135°F (57°C) per the FDA Food Code.",
        "contexts":     ["TIME/TEMPERATURE CONTROL FOR SAFETY food shall be maintained at 57°C (135°F) or above."],
        "ground_truth": "The FDA Food Code requires food to be held at 135°F (57°C) or above.",
    }
]

scores = score_outputs(rows, include_retrieval_metrics=True)
print_score_table(scores)

# Or score a single response directly
scores = score_single(
    question="Who manages calibration?",
    answer="The lab quality manager.",
    contexts=["The lab/ITU quality manager reviews calibrations nearing expiration."],
)
print(scores)
```

### Row format

| Key | Type | Required | Notes |
|---|---|---|---|
| `question` | str | Always | The question sent to the chatbot |
| `answer` | str | Always | The chatbot's response |
| `contexts` | list[str] | Always | The retrieved text chunks |
| `ground_truth` | str | For retrieval metrics | A short reference answer (1–3 sentences of plain prose) |

---

## Adding or editing test cases

Edit the `REGRESSION_TESTS` list in `regression_test.py`. Each entry:

```python
{
    "id": "REG-15",
    "category": "food-safety",
    "question": "At what temperature must cold food be held?",
    "ground_truth": (
        "The FDA Food Code requires cold food to be held at 41°F (5°C) or below "
        "to prevent bacterial growth."
    ),
},
```

**Ground truth writing tips:**
- Write in plain prose, not bullet points
- Include the specific fact(s) the context must contain — be precise, not general
- Keep it short (1–3 sentences)
- Base it on what the actual document says, not general domain knowledge — wrong ground truths corrupt `context_recall` scores

---

## Implementation notes

- **LLM used for evaluation:** `gpt-4o-mini` (chosen for its 4096-token output limit, which prevents truncation errors when scoring verbose answers)
- **Embeddings:** `text-embedding-ada-002` via `LangchainEmbeddingsWrapper` (required by `AnswerRelevancy`)
- **Ragas version:** 0.4.x — import from `ragas.metrics` directly, **not** `ragas.metrics.collections` (different class hierarchy, not accepted by `evaluate()`)
- **Context truncation:** Each retrieved chunk is capped at 800 characters before being passed to Ragas, preventing token limit issues on very long chunks
- **REG-14 (hallucination guard):** Has no `ground_truth` — only faithfulness and answer_relevancy are scored. Tests that the system doesn't fabricate an answer for a topic not in any document.
