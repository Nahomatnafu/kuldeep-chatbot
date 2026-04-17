"""
RAG Evaluation Battery — Automated test suite for Kuldeep Chatbot
=================================================================
Sends typed test questions to the running Flask /chat endpoint and
logs the responses for evaluation.

Categories:
  1. Single-doc factual      — answer lives in exactly one doc
  2. Multi-doc synthesis     — answer requires info across docs
  3. Ambiguous / scope       — question maps to multiple docs, system should clarify or handle
  4. Off-topic / guardrail   — should be blocked gracefully
  5. Follow-up / conversational — tests memory across turns
  6. Out-of-scope factual    — factual but NOT in any uploaded doc
  7. Edge cases              — empty, very long, special chars

Run: python tests/rag_eval_battery.py
Requires: Flask backend running on localhost:5000
"""

import json
import time
import requests
from datetime import datetime

CHAT_URL = "http://localhost:5000/chat"
CLEAR_URL = "http://localhost:5000/api/clear"

def send(message: str, session_id: str = "eval_session") -> dict:
    """Send a message to /chat and return the full JSON response."""
    r = requests.post(CHAT_URL, json={"message": message, "session_id": session_id}, timeout=120)
    return r.json()

def clear_session(session_id: str = "eval_session"):
    requests.post(CLEAR_URL, json={"session_id": session_id}, timeout=10)

# ── Test definitions ──────────────────────────────────────────────────────────
TESTS = [
    # ── 1. Single-doc factual ─────────────────────────────────────────────────
    {
        "id": "S1",
        "category": "single-doc",
        "question": "What are the main steps for calibrating equipment according to the SOP?",
        "expected_source": "sop_maintenance_and_calibration_of_equipment",
        "notes": "Should pull from the SOP calibration doc specifically",
    },
    {
        "id": "S2",
        "category": "single-doc",
        "question": "What is the safe food temperature for hot holding according to the FDA Food Code?",
        "expected_source": "fda_food_code_2019",
        "notes": "Should cite FDA doc, answer is 135°F / 57°C",
    },
    {
        "id": "S3",
        "category": "single-doc",
        "question": "What CNC tool compensation methods are described in the Autodesk CNC book?",
        "expected_source": "autodesk_cncbook",
        "notes": "Single-doc retrieval from CNC book",
    },
    {
        "id": "S4",
        "category": "single-doc",
        "question": "What server error codes indicate a hardware failure?",
        "expected_source": "server_installation-guide-error-codes",
        "notes": "Should only pull from the server error codes doc",
    },
    {
        "id": "S5",
        "category": "single-doc",
        "question": "What are the GMP audit categories for a manufacturing facility?",
        "expected_source": "gmp_audit_standard",
        "notes": "Should pull from GMP audit doc",
    },

    # ── 2. Multi-doc synthesis ────────────────────────────────────────────────
    {
        "id": "M1",
        "category": "multi-doc",
        "question": "Compare the lean manufacturing principles across all documents that discuss lean concepts.",
        "expected_source": "multiple (boeing_lean + lean_manufacturing + possibly modern_manufacturing)",
        "notes": "Explicit multi-doc with 'across all' trigger phrase",
    },
    {
        "id": "M2",
        "category": "multi-doc",
        "question": "Summarize all maintenance procedures mentioned across the uploaded documents.",
        "expected_source": "multiple (c4isr_maintenance + sop_maintenance + maintenance_and_operation)",
        "notes": "'across all' + 'summarize all' triggers broad intent",
    },
    {
        "id": "M3",
        "category": "multi-doc",
        "question": "What do all the documents say about safety procedures?",
        "expected_source": "multiple docs",
        "notes": "'all documents' trigger phrase",
    },

    # ── 3. Ambiguous / scope detection ────────────────────────────────────────
    {
        "id": "A1",
        "category": "ambiguous",
        "question": "What is the maintenance schedule?",
        "expected_source": "could be c4isr, sop_maintenance, or maintenance_and_operation",
        "notes": "Generic question matching multiple docs — should clarify or handle intelligently",
    },
    {
        "id": "A2",
        "category": "ambiguous",
        "question": "What are the manufacturing processes?",
        "expected_source": "could be manufacturing_processes, modern_manufacturing, processes_definitions",
        "notes": "Very broad — multiple docs cover this",
    },
    {
        "id": "A3",
        "category": "ambiguous",
        "question": "How do I operate the machine?",
        "expected_source": "could be basic_machine_tool, CNC, maintenance_and_operation",
        "notes": "Vague — should clarify which machine/doc",
    },

    # ── 4. Off-topic / guardrail ──────────────────────────────────────────────
    {
        "id": "O1",
        "category": "off-topic",
        "question": "What is the capital of France?",
        "expected_source": "none — should be blocked",
        "notes": "General knowledge, not in any doc",
    },
    {
        "id": "O2",
        "category": "off-topic",
        "question": "Tell me a joke about manufacturing.",
        "expected_source": "none — should be blocked or deflected",
        "notes": "Social / entertainment request",
    },
    {
        "id": "O3",
        "category": "off-topic",
        "question": "What is my name?",
        "expected_source": "none — guard should catch this",
        "notes": "Personal identity question",
    },

    # ── 5. Follow-up / conversational ─────────────────────────────────────────
    {
        "id": "F1",
        "category": "follow-up",
        "question": "What types of CNC machines are discussed in the CNC book?",
        "expected_source": "autodesk_cncbook",
        "notes": "First turn — establishes topic",
        "follow_up": "Tell me more about the first type mentioned.",
    },
    {
        "id": "F2",
        "category": "follow-up",
        "question": "What does the FDA Food Code say about employee hygiene?",
        "expected_source": "fda_food_code_2019",
        "notes": "First turn",
        "follow_up": "What are the specific handwashing requirements?",
    },

    # ── 6. Out-of-scope factual ───────────────────────────────────────────────
    {
        "id": "X1",
        "category": "out-of-scope",
        "question": "What is the OSHA regulation for fall protection in construction?",
        "expected_source": "none — should say docs don't contain this",
        "notes": "Plausible manufacturing question but not in any doc",
    },
    {
        "id": "X2",
        "category": "out-of-scope",
        "question": "What is the torque specification for a Ford F-150 lug nut?",
        "expected_source": "none — should say docs don't contain this",
        "notes": "Specific factual Q not in any doc — tests hallucination resistance",
    },

    # ── 7. Edge cases ─────────────────────────────────────────────────────────
    {
        "id": "E1",
        "category": "edge-case",
        "question": "CNC",
        "expected_source": "autodesk_cncbook or clarification",
        "notes": "Single keyword — how does system handle it?",
    },
    {
        "id": "E2",
        "category": "edge-case",
        "question": "What is the difference between turning and milling and drilling and boring and grinding?",
        "expected_source": "manufacturing docs",
        "notes": "Long compound question — tests chunk retrieval breadth",
    },
]


def run_battery():
    results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"\n{'='*70}")
    print(f"  RAG EVALUATION BATTERY — {datetime.now().isoformat()}")
    print(f"  {len(TESTS)} test questions across {len(set(t['category'] for t in TESTS))} categories")
    print(f"{'='*70}\n")

    for test in TESTS:
        clear_session()
        time.sleep(0.5)  # small delay to avoid rate limiting

        print(f"[{test['id']}] ({test['category']}) {test['question'][:60]}...")
        start = time.time()

        try:
            resp = send(test["question"])
            elapsed = time.time() - start
            reply = resp.get("reply", "")
            sources = resp.get("metadata", {}).get("sources", [])
            clarification = resp.get("metadata", {}).get("clarification")

            result = {
                "id": test["id"],
                "category": test["category"],
                "question": test["question"],
                "expected_source": test["expected_source"],
                "notes": test["notes"],
                "reply": reply,
                "sources": sources,
                "clarification": clarification,
                "response_time_s": round(elapsed, 2),
                "source_files": list(set(s.get("file", "") for s in sources)),
                "error": None,
            }

            # Follow-up questions
            if "follow_up" in test:
                time.sleep(0.5)
                print(f"  └─ Follow-up: {test['follow_up'][:50]}...")
                fu_start = time.time()
                fu_resp = send(test["follow_up"])
                fu_elapsed = time.time() - fu_start
                result["follow_up_question"] = test["follow_up"]
                result["follow_up_reply"] = fu_resp.get("reply", "")
                result["follow_up_sources"] = fu_resp.get("metadata", {}).get("sources", [])
                result["follow_up_time_s"] = round(fu_elapsed, 2)
                result["follow_up_source_files"] = list(set(s.get("file", "") for s in fu_resp.get("metadata", {}).get("sources", [])))

            results.append(result)
            print(f"     → {elapsed:.1f}s | Sources: {result['source_files'][:3]}")
            if reply:
                print(f"     → {reply[:120]}...")

        except Exception as e:
            results.append({
                "id": test["id"],
                "category": test["category"],
                "question": test["question"],
                "error": str(e),
            })
            print(f"     → ERROR: {e}")

        print()

    # Save raw results
    out_path = f"tests/rag_eval_results_{timestamp}.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_path}")

    return results


if __name__ == "__main__":
    run_battery()
