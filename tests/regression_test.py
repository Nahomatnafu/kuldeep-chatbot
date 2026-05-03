"""
RAG Regression Test Pipeline — Kuldeep Chatbot
===============================================
Runs a curated set of predefined questions through the live Flask backend,
collects each answer and its retrieved context chunks, evaluates them with
Ragas, and **fails (exit code 1) if any metric drops below its threshold**.

Four Ragas metrics are measured:

  faithfulness        – answer stays grounded in retrieved context        (default threshold: 0.70)
  answer_relevancy    – answer addresses the question asked               (default threshold: 0.70)
  context_precision   – retrieved chunks are relevant to the question     (default threshold: 0.60)
  context_recall      – context covers the key facts in the ground truth  (default threshold: 0.60)

Usage
-----
  # Run from the project root with the Flask backend already running:
  python tests/regression_test.py

  # Informational run — report scores but do NOT fail on threshold violations:
  python tests/regression_test.py --no-fail

  # Override thresholds on the command line:
  python tests/regression_test.py --faithfulness 0.75 --answer-relevancy 0.80

Requirements
------------
  pip install ragas
  Flask backend running on http://localhost:5000

Adding or customising test cases
---------------------------------
Edit the REGRESSION_TESTS list below.  Each entry is a dict with:

  id           (str)  – unique identifier shown in the report
  category     (str)  – logical grouping label
  question     (str)  – the question sent to the chatbot
  ground_truth (str)  – the "ideal" answer text used for context_precision
                        and context_recall scoring.  Keep it factual and
                        specific; vague ground truths produce noisy scores.

Ground truth guidelines
-----------------------
  • Write in plain prose, not bullet points.
  • Include the key fact(s) you expect the RAG system to retrieve.
  • Keep it short (1–3 sentences).  Ragas uses it to judge what the
    *context* should contain, not to grade the exact wording of the answer.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Optional

import requests

# ── Backend endpoints ─────────────────────────────────────────────────────────

BACKEND_URL = os.getenv("CHATBOT_BACKEND_URL", "http://localhost:5000").rstrip("/")
CHAT_URL  = f"{BACKEND_URL}/chat"
CLEAR_URL = f"{BACKEND_URL}/api/clear"
RESULTS_DIR = os.path.join(os.path.dirname(__file__))

# ── Score thresholds (override via CLI args) ──────────────────────────────────

DEFAULT_THRESHOLDS: dict[str, float] = {
    "faithfulness":      0.70,
    "answer_relevancy":  0.70,
    "context_precision": 0.60,
    "context_recall":    0.60,
}

# ── Regression test cases ─────────────────────────────────────────────────────
# ground_truth is used only for context_precision and context_recall.
# All ground truths are copied directly from source documents (not AI-generated).

REGRESSION_TESTS: list[dict] = [

    # ── FDA Food Code ─────────────────────────────────────────────────────────
    {
        "id": "REG-01",
        "category": "food-safety",
        "question": "According to the FDA Food Code 2019, what hand drying provisions are required for food employees?",
        "ground_truth": (
            "The FDA Food Code requires provisions for hand drying so that employees will not "
            "dry their hands on their clothing or other unclean materials. "
            "Wet hands transfer bacteria more readily than dry hands, and the method of drying "
            "is a critical factor in reducing cross-contamination. "
            "Air knife technology has been found to be equivalent to existing heated-air hand "
            "drying devices, but may not accommodate drying of forearms or prosthetic devices, "
            "requiring an alternate drying means in those cases."
        ),
    },
    {
        "id": "REG-02",
        "category": "food-safety",
        "question": "According to the FDA Food Code 2019, what handwashing signage is required at food establishments?",
        "ground_truth": (
            "The FDA Food Code requires a sign or poster to be posted at handwashing sinks "
            "to remind food employees to wash their hands."
        ),
    },

    # ── Manufacturing Processes ───────────────────────────────────────────────
    {
        "id": "REG-03",
        "category": "manufacturing",
        "question": "In the Manufacturing Processes document, what are the three distinct zones of a fatigue fracture?",
        "ground_truth": (
            "The three distinct zones of a fatigue fracture are the point of crack initiation, "
            "the area of crack propagation during service, and the remaining area of "
            "cross-section showing signs of sudden breakage."
        ),
    },
    {
        "id": "REG-04",
        "category": "manufacturing",
        "question": "According to the Manufacturing Processes document, what is creep failure?",
        "ground_truth": (
            "Creep failure occurs when materials deform plastically at a very slow rate under "
            "steady loads, especially at high temperatures, leading to ultimate failure over time. "
            "This type of failure is common in components like stays in boilers and turbine blades."
        ),
    },
    {
        "id": "REG-05",
        "category": "manufacturing",
        "question": "According to the Manufacturing Processes document, what are some benefits of using alloy steel?",
        "ground_truth": (
            "Alloying in steels can lead to hardening by heat treatment, corrosion resistance, "
            "red hardness in cutting tools, increased strength and toughness, resistance to "
            "grain growth, and oxidation at high temperatures. "
            "The main alloying elements used in alloy steels are chromium, nickel, tungsten, "
            "molybdenum, vanadium, cobalt, manganese, and silicon. "
            "Alloy steels are available in various types, categorized into stainless steels, "
            "tool steel, and special steels. "
            "Nickel, chromium, and silicon are specific alloying elements used in nickel steels, "
            "chromium steels, and silicon steels respectively. "
            "Alloying elements can significantly improve the properties of cast iron and plain "
            "carbon steels. "
            "Alloy cast irons have higher strength, heat-resistance, and wear-resistance "
            "compared to plain cast iron."
        ),
    },
    {
        "id": "REG-06",
        "category": "manufacturing",
        "question": "According to the Manufacturing Processes document, what are the steps for heat treatment?",
        "ground_truth": (
            "Heat treatment of carbon steels involves three basic steps: heating the metal to a "
            "specific temperature, soaking it at that temperature for uniformity, and cooling it "
            "at a controlled rate in water, oil, or air. "
            "Carbon steels undergo four basic heat-treatment processes: annealing, normalizing, "
            "hardening, and tempering. "
            "Annealing softens the material and removes internal stresses based on the carbon "
            "content of the steel. "
            "Normalizing involves heating, soaking, and cooling the steel in still air to "
            "eliminate internal stresses and refine the grain structure. "
            "Hardening includes heating, soaking, and quenching the steel in water or oil to "
            "increase hardness, followed by tempering to reduce brittleness. "
            "Case hardening is used for low carbon steels by packing the workpiece in charcoal "
            "to introduce carbon into the surface."
        ),
    },

    # ── Machine Tool Operations ───────────────────────────────────────────────
    {
        "id": "REG-07",
        "category": "machining",
        "question": "According to the Basic Machine Tool Operations Aug 2017 document, what are the Machine Shop Rules?",
        "ground_truth": (
            "Students are not permitted to work without a Supervisor in the Machine Shop. "
            "Students must scan their I.D. card upon entering and display their printed label "
            "in a visible location. "
            "When working in the shop, two people must be present at all times. "
            "Buddy's are not to touch machinery controls. "
            "Safety glasses must be worn at all times; tinted or sunglasses are not permitted. "
            "No sandals or open-toe shoes are allowed; work boots or street shoes only. "
            "Do not wear loose clothing or jewelry; tie back long hair. "
            "Safety Data Sheets must be supplied on materials not listed in shop SDS book before "
            "work can begin. "
            "Dispose of waste according to the SDS sheets and posted signs. "
            "No part washing in the sinks; sinks are for hand washing only. "
            "Do not lay rags on lathe, mill or moving machinery. "
            "Do not enter the shop under the influence of drugs or alcohol. "
            "All metal scraps and cuttings are to be disposed of in the proper recycling drum. "
            "Only certified students are allowed to operate the equipment of which they are "
            "certified to use. "
            "Students should never talk on a cell phone while operating equipment. "
            "The Supervisor must check all machine setups before machine operation begins. "
            "No arguing or horseplay in the shop. "
            "No eating or drinking in the shop. "
            "Tools are not to be removed from building 538. "
            "Put tools back to where they belong. "
            "Clean off machines and/or tools after use."
        ),
    },
    {
        "id": "REG-08",
        "category": "machining",
        "question": "According to the Basic Machine Tool Operations Aug 2017 document, how do I clean a lathe?",
        "ground_truth": (
            "A lathe should be cleaned after each work period. "
            "Remove chips with a paint brush, not your hand, and wipe all painted surfaces "
            "with a soft cloth. "
            "Move the tailstock to the extreme right and wipe remaining oil, chips and dirt "
            "from machined surfaces; do not use compressed air as flying chips are dangerous. "
            "The lead screw can be cleaned by running the lathe at slow speed and feeding a "
            "piece of cord along the threads, but never wrap the cord around your hand."
        ),
    },
    {
        "id": "REG-09",
        "category": "cnc",
        "question": "In the Autodesk CNCbook, what roughing rule mentions grooves and other features?",
        "ground_truth": (
            "The roughing rules say to skip over grooves and other features that will be "
            "rough or finished with other tools and operations."
        ),
    },
    {
        "id": "REG-10",
        "category": "machining",
        "question": "In the Basic Machine Tool Operations Aug 2017 document, what does laying out mean and what tools are used? Explain in a simple way.",
        "ground_truth": (
            "Laying out is the term used to describe the locating and marking out of lines, "
            "circles, arcs and points for drilling holes. "
            "These lines and reference points on the metal show the machinist where to machine. "
            "The tools used for this work are known as layout tools."
        ),
    },

    # ── Boeing Lean Manufacturing ─────────────────────────────────────────────
    {
        "id": "REG-11",
        "category": "lean-manufacturing",
        "question": "In the Boeing Lean Manufacturing Studies, what is Value Stream?",
        "ground_truth": (
            "The Value Stream is the set of specific actions required to bring a specific "
            "product through three critical management tasks of any business: problem solving, "
            "information management, and physical transformation."
        ),
    },
    {
        "id": "REG-12",
        "category": "lean-manufacturing",
        "question": "In the Boeing Lean Manufacturing Studies, what resource productivity gains did Boeing achieve from the new shipping process?",
        "ground_truth": (
            "Multiple transfers, rail travel, and truck travel to the rail heads have been "
            "completely eliminated. "
            "Trucks no longer run empty from Kansas City to Tulsa because shipping by rail "
            "has been removed from the process. "
            "Eight days of travel and three days of receiving and inspection have been eliminated. "
            "Approximately $7,900 has been saved per shipset, or $396,000 in annual "
            "transportation costs. "
            "Floor grid inventory has been reduced by 25 percent. "
            "Each ship set uses 50 percent less transportation. "
            "Overall handling of materials has been reduced, yielding a reduction in forklift use. "
            "In response to Boeing's new shipping process, the floor grid component suppliers "
            "have adjusted their manufacturing schedules so that they do not produce and "
            "accumulate excess inventory at their production sites."
        ),
    },
    {
        "id": "REG-13",
        "category": "lean-manufacturing",
        "question": "According to Lean Manufacturing, what does monuments mean and give me two examples?",
        "ground_truth": (
            "Monuments are production processes or process steps that have large equipment "
            "and/or other physical or environmental regulatory constraints, are very difficult "
            "or costly to move, and can disrupt the flow sought through Lean. "
            "Examples include painting processes with large fixed paint booths or dipping tanks, "
            "and metal finishing processes with large tanks and/or fixed equipment."
        ),
    },

    # ── Maintenance & Calibration SOP ─────────────────────────────────────────
    {
        "id": "REG-15",
        "category": "calibration",
        "question": "According to the SOP Maintenance and Calibration of Equipment, what is the difference between preventive maintenance and corrective maintenance?",
        "ground_truth": (
            "Preventive maintenance consists of maintenance activities carried out periodically "
            "according to criteria defined by the official equipment maintainer. "
            "Corrective maintenance consists of maintenance activities performed on equipment "
            "when an incident is detected in its normal operation."
        ),
    },

    # ── CNC / Autodesk ────────────────────────────────────────────────────────
    {
        "id": "REG-16",
        "category": "cnc",
        "question": "According to the Autodesk CNCbook, what are the required clothes for working in the CNC shop?",
        "ground_truth": (
            "ANSI approved safety glasses must be worn at all times in the shop, not just "
            "when at the machine. "
            "Do not wear flip flops or sandals; leather shoes are best. "
            "Do not wear long sleeve shirts as these could get caught in equipment; wear "
            "short sleeves or T-shirts. "
            "Remove rings and watches when at the machine. "
            "Do not wear short pants; wear sturdy long pants like blue jeans or work pants. "
            "Long hair should be tied back or under a hat to prevent it being caught in the "
            "machine spindle. "
            "Never wear gloves as they can be caught in the machine; latex gloves are acceptable."
        ),
    },
    {
        "id": "REG-17",
        "category": "cnc",
        "question": "According to the Autodesk CNCbook, what is the difference between a subplate and an angle plate?",
        "ground_truth": (
            "A subplate is a ground aluminum plate that bolts to the top of the machine table "
            "and has threaded holes and bushings at regular intervals. "
            "An angle plate is a precision ground steel plate that allows the part to be set "
            "on its side, and can point in a direction parallel to either the X or Y axis."
        ),
    },
    {
        "id": "REG-18",
        "category": "manufacturing",
        "question": "According to Modern Manufacturing, what are the varieties of milling cutter tool constructions?",
        "ground_truth": (
            "Solid cutters are made from a single piece of HSS or carbide; cutters can be "
            "tipped with a harder material; teeth can be designed for specific cutting "
            "conditions; low initial cost. "
            "Inserted blade cutters are usually made from HSS, carbide, or cast alloy; "
            "individual blades can be replaced as they wear out, saving replacement cost; "
            "ideal for close-tolerance finishing. "
            "Indexable insert cutters use inserts made from carbide, coated carbide, ceramic, "
            "or ultrahard material such as diamond; each insert has one or more cutting edges; "
            "as inserts wear they are repositioned to expose new cutting surface or indexed to "
            "bring another cutting insert on line."
        ),
    },

    # ── Server / Error Codes ──────────────────────────────────────────────────
    {
        "id": "REG-19",
        "category": "server",
        "question": "In the server installation guide error codes document, what is error code 8x1A?",
        "ground_truth": (
            "Error code 8x1A indicates an AC Voltage Surge. "
            "If the fault persists, check the AC connection to the inverter, verify the "
            "inverter is set to the correct country, check with the grid operator if a large "
            "surge source or irregular load exists near the site, and verify that the output "
            "wire size matches the distance between the inverter and the grid connection."
        ),
    },

    # ── Modern Manufacturing (Laser / Welding) ────────────────────────────────
    {
        "id": "REG-20",
        "category": "manufacturing",
        "question": "According to Modern Manufacturing, what are the general processing guidelines for laser surface hardening?",
        "ground_truth": (
            "The range of usable power densities for laser surface hardening is 3200 W/in² "
            "(500 W/cm²) to 32,000 W/in² (5000 W/cm²) with beam dwell times from 0.1 to "
            "10 seconds; higher power levels would melt the surface. "
            "Alloys with high hardenability can be processed at low speed with low power "
            "density to produce relatively thick cases. "
            "Alloys with low hardenability should be processed at high speed with high power "
            "density; the result is a shallow case. "
            "Beam configuration can be rectangular, square, or round, and uniform energy "
            "density within the beam is very important. "
            "Maximum achievable surface temperature is proportional to the square root of the "
            "processing speed; thus doubling the beam power density requires the processing "
            "speed to be increased by a factor of four to maintain the equivalent maximum "
            "surface temperature. "
            "Smaller workpieces are not as effective a heat sink as larger workpieces, and "
            "hence self-quenching may have to be assisted by quenching media."
        ),
    },
    {
        "id": "REG-21",
        "category": "manufacturing",
        "question": "According to Modern Manufacturing, what is laser surface hardening?",
        "ground_truth": (
            "Laser surface hardening is used as an alternative to flame hardening and "
            "induction hardening of ferrous materials. "
            "The rapid heating rate achievable by the laser minimizes part distortion and "
            "can impart surface hardness to low-carbon steels. "
            "This process is used to harden selected areas of machine components such as "
            "gears, cylinders, bearings, and shafts, and the entire operation can be "
            "performed in air."
        ),
    },
    {
        "id": "REG-22",
        "category": "manufacturing",
        "question": "According to Modern Manufacturing, explain the key system components for laser surface hardening.",
        "ground_truth": (
            "The majority of industrial metalworking lasers are either solid-state Nd:YAG "
            "or carbon dioxide type; power output for YAG lasers is 50 to 500 W and carbon "
            "dioxide lasers are available up to 25 kW. "
            "The surface to be hardened is usually coated to improve its ability to absorb "
            "laser radiation; a typical coating is manganese phosphate, and paints containing "
            "graphite, silicon, and carbon are also used, increasing absorption to 80 to 90 percent. "
            "The output beam of the laser must be shaped and directed by an optical system to "
            "generate a laser spot of desired shape and size at the correct location on the "
            "workpiece surface; reflective optical components are used as they are sturdy and "
            "easily adapted to an industrial environment."
        ),
    },
    {
        "id": "REG-23",
        "category": "manufacturing",
        "question": "According to Modern Manufacturing, describe how bonding is achieved.",
        "ground_truth": (
            "Bonding is achieved in fusion welding by interposing a liquid of substantially "
            "similar composition as the base metal between the surfaces to be joined. "
            "The need for welding and joining is substantial since only monolithic parts can "
            "be made without joining."
        ),
    },
    {
        "id": "REG-24",
        "category": "manufacturing",
        "question": "According to Modern Manufacturing, can you give me an application or example of how bonding is achieved?",
        "ground_truth": (
            "In the fabrication of heavy structures, arc welding dominates other assembly "
            "processes because of the inherent flexibility and economy of welding."
        ),
    },

    {
        "id": "REG-25",
        "category": "revision-metadata",
        "question": "In the Basic Machine Tool Operation Guide, what revision is shown on the cover?",
        "ground_truth": (
            "The Basic Machine Tool Operation Guide cover shows Rev. A 8/2017."
        ),
    },
    {
        "id": "REG-26",
        "category": "revision-metadata",
        "question": "In the SOP Maintenance and Calibration of Equipment, what document code and version are shown?",
        "ground_truth": (
            "The SOP Maintenance and Calibration of Equipment shows PR_GENER_0005_04 "
            "Version 4.0."
        ),
    },
    {
        "id": "REG-27",
        "category": "exact-spec",
        "question": "According to Modern Manufacturing, what power density range and dwell time are used for laser surface hardening?",
        "ground_truth": (
            "The range of usable power densities for laser surface hardening is 3200 W/in2 "
            "(500 W/cm2) to 32,000 W/in2 (5000 W/cm2), with beam dwell times ranging "
            "from 0.1 to 10 seconds."
        ),
    },
    {
        "id": "REG-28",
        "category": "equipment-specific",
        "question": "According to Modern Manufacturing, what machine components are hardened by laser surface hardening?",
        "ground_truth": (
            "Laser surface hardening is used to harden selected areas of machine components, "
            "such as gears, cylinders, bearings, and shafts."
        ),
    },

    # ── Grounding / hallucination guard (no ground_truth — skipped from retrieval metrics) ──
    {
        "id": "REG-14",
        "category": "grounding",
        "question": "What is the torque specification for a Ford F-150 lug nut?",
        # No ground_truth: scores faithfulness + answer_relevancy only.
        # Tests that the system does NOT hallucinate an answer absent from the docs.
    },
]

# ── Behavioral test cases ─────────────────────────────────────────────────────
# These verify routing, guard, and clarification logic.
# Pass/fail is determined by assertions on the response shape — no Ragas scoring.
# Each entry has:
#   id          (str)  – unique identifier
#   description (str)  – what routing/behavioral path is being tested
#   question    (str)  – message sent to the chatbot
#   checks      (list) – assertion dicts; each has a "type" key and optional "value"
#
# Check types:
#   reply_contains   – reply.lower() contains value.lower()
#   reply_nonempty   – reply is non-empty
#   sources_empty    – sources list is empty
#   sources_nonempty – sources list has at least one entry
#   no_clarification – metadata has no "clarification" key
#   has_clarification – metadata has a "clarification" key

BEHAVIORAL_TESTS: list[dict] = [
    {
        "id": "BEH-01",
        "description": "Off-topic guard: entertainment request is blocked by fast-check",
        # "Tell me a joke" hits the whole-word fast-check on 'joke' deterministically,
        # without requiring an LLM call — making this a reliable, variance-free assertion.
        "question": "Tell me a joke",
        "checks": [
            {"type": "reply_contains", "value": "I can only answer questions about the uploaded documents"},
            {"type": "sources_empty"},
            {"type": "no_clarification"},
        ],
    },
    {
        "id": "BEH-02",
        "description": "Broad path: 'across all documents' phrase triggers multi-doc answer",
        "question": "Across all documents, what types of safety equipment or protective gear are mentioned?",
        "checks": [
            {"type": "reply_nonempty"},
            {"type": "sources_nonempty"},
            {"type": "no_clarification"},
        ],
    },
    {
        "id": "BEH-03",
        "description": "Ambiguous path: cross-cutting question triggers clarification flow",
        # "What safety gear do I need to wear?" matches multiple docs (CNC shop, machine
        # tool operations, etc.) competitively — confirmed to trigger clarification in the app.
        "question": "What safety gear do I need to wear?",
        "checks": [
            {"type": "has_clarification"},
            {"type": "sources_empty"},
        ],
    },
    {
        "id": "BEH-04",
        "description": "Pass path: specific single-doc question returns answer with sources",
        # The machine shop certification content appears only in the Basic Machine Tool
        # Operations doc, so this should resolve cleanly without triggering clarification.
        "question": "How do I get my machine shop student certification?",
        "checks": [
            {"type": "reply_nonempty"},
            {"type": "sources_nonempty"},
            {"type": "no_clarification"},
        ],
    },
]

# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _send(question: str, session_id: str = "regression_session") -> dict:
    """POST a question to /chat and return the parsed JSON response."""
    resp = requests.post(
        CHAT_URL,
        json={"message": question, "session_id": session_id},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def _clear_session(session_id: str = "regression_session") -> None:
    try:
        requests.post(CLEAR_URL, json={"session_id": session_id}, timeout=10)
    except requests.RequestException:
        pass  # best-effort


def _check_backend() -> tuple[bool, str]:
    """Return (reachable, message)."""
    try:
        r = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        return r.status_code == 200, r.text
    except requests.RequestException as exc:
        return False, str(exc)


# ── Output collection ─────────────────────────────────────────────────────────

def collect_rag_outputs(tests: list[dict], pause: float = 0.5) -> list[dict]:
    """
    Run each test question through the chatbot and collect:
      - the generated answer
      - the retrieved context chunks (``full_snippet`` or ``snippet`` per source)

    Returns a list of enriched dicts, one per test, adding:
        answer   (str)        – the chatbot's reply
        contexts (list[str])  – text of every retrieved chunk
        sources  (list[dict]) – raw source metadata from the API
        error    (str|None)   – exception message if the call failed
        response_time_s (float)
    """
    results: list[dict] = []

    for test in tests:
        session_id = f"regression_{test['id']}"
        _clear_session(session_id)
        time.sleep(pause)

        print(f"  [{test['id']}] {test['question'][:70]}...")
        t0 = time.time()
        row = dict(test)  # copy to avoid mutating the original

        try:
            resp     = _send(test["question"], session_id=session_id)
            elapsed  = time.time() - t0
            answer   = resp.get("reply", "")
            sources  = resp.get("metadata", {}).get("sources", [])

            # Use full_snippet when available; fall back to snippet.
            # No truncation — the Ragas LLM (gpt-4o-mini, max_tokens=8192) can
            # handle full-length chunks without hitting output token limits.
            contexts = [
                s.get("full_snippet") or s.get("snippet", "")
                for s in sources
                if s.get("full_snippet") or s.get("snippet")
            ]

            row.update({
                "answer":           answer,
                "contexts":         contexts,
                "sources":          sources,
                "response_time_s":  round(elapsed, 2),
                "error":            None,
            })
            print(f"       → {elapsed:.1f}s  |  {len(contexts)} context chunk(s) retrieved")

        except Exception as exc:
            elapsed = time.time() - t0
            row.update({
                "answer":           "",
                "contexts":         [],
                "sources":          [],
                "response_time_s":  round(elapsed, 2),
                "error":            str(exc),
            })
            print(f"       → ERROR: {exc}")

        results.append(row)
        print()

    return results


# ── Evaluation + reporting ────────────────────────────────────────────────────

def run_behavioral_tests(tests: list[dict], pause: float = 0.5) -> list[dict]:
    """
    Run behavioral assertion tests against the live backend.

    Each test sends a question and checks the response shape against a list of
    assertions.  No Ragas scoring is performed — pass/fail is determined purely
    by the structure of the backend's JSON response.

    Returns a list of result dicts, one per test, with keys:
        id          (str)   – test identifier
        description (str)   – what is being tested
        passed      (bool)  – True if all checks passed
        failures    (list)  – human-readable failure messages
        error       (str|None) – exception message if the HTTP call failed
    """
    results: list[dict] = []

    for test in tests:
        session_id = f"regression_{test['id']}"
        _clear_session(session_id)
        time.sleep(pause)

        print(f"  [{test['id']}] {test['description']}")
        t0 = time.time()
        result: dict = {
            "id":          test["id"],
            "description": test["description"],
            "passed":      True,
            "failures":    [],
            "error":       None,
        }

        try:
            resp          = _send(test["question"], session_id=session_id)
            elapsed       = time.time() - t0
            reply         = resp.get("reply", "")
            metadata      = resp.get("metadata", {})
            sources       = metadata.get("sources", [])
            clarification = metadata.get("clarification")

            failures: list[str] = []
            for check in test.get("checks", []):
                ctype = check["type"]
                if ctype == "reply_contains":
                    if check["value"].lower() not in reply.lower():
                        failures.append(
                            f"reply_contains: expected '{check['value']}' in reply; "
                            f"got: '{reply[:120]}'"
                        )
                elif ctype == "reply_nonempty":
                    if not reply.strip():
                        failures.append("reply_nonempty: reply was empty")
                elif ctype == "sources_empty":
                    if sources:
                        failures.append(
                            f"sources_empty: expected no sources, got {len(sources)}"
                        )
                elif ctype == "sources_nonempty":
                    if not sources:
                        failures.append(
                            "sources_nonempty: expected at least one source, got none"
                        )
                elif ctype == "no_clarification":
                    if clarification:
                        failures.append(
                            "no_clarification: unexpected clarification metadata in response"
                        )
                elif ctype == "has_clarification":
                    if not clarification:
                        failures.append(
                            "has_clarification: expected clarification metadata but none present"
                        )

            result["passed"]   = len(failures) == 0
            result["failures"] = failures
            status = "PASS" if result["passed"] else "FAIL"
            print(f"       → {elapsed:.1f}s  |  {status}")
            for msg in failures:
                print(f"         ✗ {msg}")

        except Exception as exc:
            result["passed"] = False
            result["error"]  = str(exc)
            print(f"       → ERROR: {exc}")

        results.append(result)
        print()

    return results


def _evaluate(
    collected: list[dict],
    thresholds: dict[str, float],
) -> tuple[dict[str, float], list[str]]:
    """
    Score the collected outputs with Ragas and return (scores, failures).

    Faithfulness + answer_relevancy are computed for every scoreable row.
    Context_precision + context_recall are computed only for rows that have
    a non-empty ``ground_truth`` value (rows without one, e.g. the hallucination
    guard test REG-14, are excluded from retrieval metric averaging).

    ``failures`` is a list of human-readable failure messages for metrics
    that fell below their threshold.
    """
    sys.path.insert(0, os.path.dirname(__file__))
    try:
        from ragas_eval import score_outputs, print_score_table  # type: ignore
    except ImportError as exc:
        print(f"\n[WARNING] Ragas evaluation unavailable: {exc}")
        return {}, [str(exc)]

    # Base filter: no errors, has an answer and at least one context chunk
    scoreable = [
        r for r in collected
        if not r.get("error") and r.get("answer") and r.get("contexts")
    ]

    if not scoreable:
        print(
            "\n[WARNING] No scoreable rows — all test questions either errored "
            "or returned no context chunks.  Skipping Ragas evaluation."
        )
        return {}, []

    skipped = len(collected) - len(scoreable)
    if skipped:
        print(f"\n[INFO] Skipping {skipped} row(s) with errors or empty contexts.")

    # Rows with ground_truth → eligible for all 4 metrics
    retrieval_rows = [r for r in scoreable if r.get("ground_truth")]
    grounding_only_rows = [r for r in scoreable if not r.get("ground_truth")]

    if grounding_only_rows:
        ids = [r["id"] for r in grounding_only_rows]
        print(f"[INFO] {len(grounding_only_rows)} row(s) have no ground_truth and will be "
              f"scored for faithfulness + answer_relevancy only: {ids}")

    all_scores: dict[str, float] = {}

    # Pass 1 — grounding metrics across ALL scoreable rows
    print(f"\nRunning grounding metrics (faithfulness, answer_relevancy) "
          f"on {len(scoreable)} row(s) ...")
    grounding_scores = score_outputs(scoreable, include_retrieval_metrics=False)
    all_scores.update(grounding_scores)

    # Pass 2 — retrieval metrics only for rows WITH ground_truth
    if retrieval_rows:
        print(f"Running retrieval metrics (context_precision, context_recall) "
              f"on {len(retrieval_rows)} row(s) ...\n")
        retrieval_scores = score_outputs(retrieval_rows, include_retrieval_metrics=True)
        # Keep only the retrieval-specific metrics from this pass
        for k in ("context_precision", "context_recall"):
            if k in retrieval_scores:
                all_scores[k] = retrieval_scores[k]
    else:
        print("[INFO] No rows with ground_truth — skipping retrieval metrics.")

    print_score_table(all_scores, thresholds=thresholds)

    failures = [
        f"{metric}: {score:.4f} < threshold {thresholds[metric]:.2f}"
        for metric, score in all_scores.items()
        if metric in thresholds and score < thresholds[metric]
    ]
    return all_scores, failures


def _save_results(collected: list[dict], scores: dict, timestamp: str) -> str:
    """Persist raw outputs + Ragas scores to a JSON file."""
    payload = {
        "timestamp":       timestamp,
        "ragas_scores":    scores,
        "test_results":    collected,
    }
    path = os.path.join(RESULTS_DIR, f"regression_results_{timestamp}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    return path


# ── Main entry point ──────────────────────────────────────────────────────────

def run_regression(thresholds: dict[str, float], no_fail: bool = False) -> int:
    """
    Full regression pipeline:
      1. Check that the backend is reachable.
      2. Send all REGRESSION_TESTS to /chat.
      3. Run BEHAVIORAL_TESTS (routing, guard, clarification assertions).
      4. Evaluate RAG outputs with Ragas.
      5. Print a summary report.
      6. Return exit code 0 (all pass) or 1 (at least one failure).

    If ``no_fail`` is True, always return 0 (informational run).
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    divider   = "=" * 65

    print(f"\n{divider}")
    print(f"  REGRESSION TEST PIPELINE  —  {datetime.now().isoformat()}")
    print(f"  {len(REGRESSION_TESTS)} RAG tests  |  {len(BEHAVIORAL_TESTS)} behavioral tests  |  4 Ragas metrics")
    print(f"  Thresholds: { {k: f'{v:.2f}' for k, v in thresholds.items()} }")
    print(f"{divider}\n")

    # 1 — Backend health check
    ok, msg = _check_backend()
    if not ok:
        print(
            f"[FATAL] Flask backend is not reachable at {CHAT_URL}\n"
            f"        Start it with:  cd backend && python run.py\n"
            f"        Error: {msg}"
        )
        return 1

    print(f"[OK] Backend reachable.\n")

    # 2 — Collect RAG outputs
    print("── Collecting answers from chatbot ──────────────────────────\n")
    collected = collect_rag_outputs(REGRESSION_TESTS)

    # 3 — Behavioral assertions (fast, no LLM judge)
    print("── Behavioral assertions ────────────────────────────────────\n")
    beh_results  = run_behavioral_tests(BEHAVIORAL_TESTS)
    beh_failures = [r for r in beh_results if not r["passed"]]

    # 4 — Ragas evaluation
    print("── Ragas scoring ────────────────────────────────────────────")
    scores, ragas_failures = _evaluate(collected, thresholds)

    # 5 — Persist
    path = _save_results(collected, scores, timestamp)
    print(f"Results saved → {path}")

    # 6 — Summary
    any_failure = bool(ragas_failures) or bool(beh_failures)
    print(f"\n{divider}")
    if not scores:
        print("  [SKIP] No Ragas scores computed — check errors above.")
        if beh_failures:
            print(f"  {len(beh_failures)} behavioral test(s) also failed:")
            for r in beh_failures:
                print(f"    • [{r['id']}] {r['description']}")
        return 1 if not no_fail else 0

    if any_failure:
        print("  RESULT: FAILED")
        if ragas_failures:
            print("  Ragas metrics below threshold:")
            for f in ragas_failures:
                print(f"    • {f}")
        if beh_failures:
            print("  Behavioral tests failed:")
            for r in beh_failures:
                print(f"    • [{r['id']}] {r['description']}")
                for msg in r["failures"]:
                    print(f"        ✗ {msg}")
    else:
        print("  RESULT: PASSED  — all Ragas metrics and behavioral tests passed.")
    print(f"{divider}\n")

    if any_failure and not no_fail:
        return 1
    return 0


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="RAG regression test pipeline using Ragas evaluation."
    )
    p.add_argument(
        "--no-fail",
        action="store_true",
        help="Report scores but always exit 0 (informational run).",
    )
    p.add_argument(
        "--faithfulness",
        type=float,
        default=DEFAULT_THRESHOLDS["faithfulness"],
        metavar="SCORE",
        help=f"Faithfulness threshold (default: {DEFAULT_THRESHOLDS['faithfulness']}).",
    )
    p.add_argument(
        "--answer-relevancy",
        type=float,
        default=DEFAULT_THRESHOLDS["answer_relevancy"],
        metavar="SCORE",
        help=f"Answer relevancy threshold (default: {DEFAULT_THRESHOLDS['answer_relevancy']}).",
    )
    p.add_argument(
        "--context-precision",
        type=float,
        default=DEFAULT_THRESHOLDS["context_precision"],
        metavar="SCORE",
        help=f"Context precision threshold (default: {DEFAULT_THRESHOLDS['context_precision']}).",
    )
    p.add_argument(
        "--context-recall",
        type=float,
        default=DEFAULT_THRESHOLDS["context_recall"],
        metavar="SCORE",
        help=f"Context recall threshold (default: {DEFAULT_THRESHOLDS['context_recall']}).",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    thresholds = {
        "faithfulness":      args.faithfulness,
        "answer_relevancy":  args.answer_relevancy,
        "context_precision": args.context_precision,
        "context_recall":    args.context_recall,
    }

    sys.exit(run_regression(thresholds=thresholds, no_fail=args.no_fail))
