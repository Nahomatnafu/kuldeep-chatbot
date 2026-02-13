"""
Test Question Set for RAG System Evaluation

This file contains test questions to evaluate:
1. Retrieval quality (are the right chunks retrieved?)
2. Answer groundedness (is the answer based on retrieved context?)
3. Answer completeness (does it fully answer the question?)
4. Conversational memory (does it remember previous context?)
"""

# Test cases for single-turn questions (no conversation history)
SINGLE_TURN_TESTS = [
    {
        "id": "ST-001",
        "question": "What is SpectTTTra?",
        "difficulty": "easy",
        "expected_topics": [
            "pre-trained model",
            "spectro-temporal",
            "AI music detection"
        ],
        "expected_sources": ["page 3", "page 4"],
        "notes": "Should retrieve chunks that define SpectTTTra"
    },
    {
        "id": "ST-002",
        "question": "What are the three SpectTTTra variants?",
        "difficulty": "easy",
        "expected_answer_contains": ["α", "β", "γ"],
        "expected_sources": ["page 3"],
        "notes": "Should list all three variants with their parameters"
    },
    {
        "id": "ST-003",
        "question": "What baseline models are used in the broadcast monitoring paper?",
        "difficulty": "easy",
        "expected_answer_contains": ["CNN", "SpectTTTra"],
        "expected_sources": ["page 4"],
        "notes": "Should mention CNN baseline and SpectTTTra models"
    },
    {
        "id": "ST-004",
        "question": "How do broadcast conditions affect AI music detection?",
        "difficulty": "medium",
        "expected_topics": [
            "speech masking",
            "SNR",
            "short duration",
            "performance drop"
        ],
        "expected_sources": ["page 3", "page 4"],
        "notes": "Should discuss challenges in broadcast scenarios"
    },
    {
        "id": "ST-005",
        "question": "What accuracy is mentioned for AI music detection?",
        "difficulty": "easy",
        "expected_answer_contains": ["99.8%"],
        "expected_sources": ["page 1"],
        "notes": "Should retrieve the specific accuracy number"
    },
    {
        "id": "ST-006",
        "question": "What is the SONICS dataset?",
        "difficulty": "medium",
        "expected_topics": ["dataset", "training", "AI music"],
        "notes": "Should explain what SONICS is used for"
    },
    {
        "id": "ST-007",
        "question": "What audio transformations are tested?",
        "difficulty": "medium",
        "expected_topics": ["transformations", "robustness", "testing"],
        "notes": "Should list various audio transformations mentioned"
    },
    {
        "id": "ST-008",
        "question": "What is the difference between SpectTTTra-α and SpectTTTra-γ?",
        "difficulty": "hard",
        "expected_topics": ["spectral patches", "temporal patches", "size"],
        "expected_sources": ["page 3"],
        "notes": "Should compare the patch sizes: α(f=1,t=3) vs γ(f=5,t=7)"
    },
]

# Test cases for conversational memory (multi-turn)
CONVERSATION_TESTS = [
    {
        "id": "CONV-001",
        "conversation": [
            {
                "turn": 1,
                "question": "What is SpectTTTra?",
                "expected_topics": ["pre-trained model", "spectro-temporal"]
            },
            {
                "turn": 2,
                "question": "What are its variants?",
                "expected_answer_contains": ["α", "β", "γ"],
                "notes": "Should understand 'its' refers to SpectTTTra from turn 1"
            },
            {
                "turn": 3,
                "question": "How do they differ?",
                "expected_topics": ["spectral patches", "temporal patches"],
                "notes": "Should understand 'they' refers to the variants from turn 2"
            }
        ],
        "difficulty": "medium",
        "notes": "Tests pronoun resolution across multiple turns"
    },
    {
        "id": "CONV-002",
        "conversation": [
            {
                "turn": 1,
                "question": "What baseline models are used?",
                "expected_answer_contains": ["CNN", "SpectTTTra"]
            },
            {
                "turn": 2,
                "question": "How do they perform under broadcast conditions?",
                "expected_topics": ["performance drop", "degradation"],
                "notes": "Should understand 'they' refers to the models from turn 1"
            }
        ],
        "difficulty": "medium",
        "notes": "Tests context retention for follow-up questions"
    },
    {
        "id": "CONV-003",
        "conversation": [
            {
                "turn": 1,
                "question": "What challenges are mentioned for broadcast monitoring?",
                "expected_topics": ["speech masking", "short duration"]
            },
            {
                "turn": 2,
                "question": "Which one has the biggest impact?",
                "expected_topics": ["performance", "impact"],
                "notes": "Should refer back to challenges from turn 1"
            }
        ],
        "difficulty": "hard",
        "notes": "Tests ability to compare information from previous turn"
    }
]

# Edge cases and failure modes
EDGE_CASE_TESTS = [
    {
        "id": "EDGE-001",
        "question": "What is the capital of France?",
        "expected_behavior": "refuse_to_answer",
        "expected_response_contains": ["does not contain", "information"],
        "notes": "Should refuse to answer questions outside the knowledge base"
    },
    {
        "id": "EDGE-002",
        "question": "List all the models mentioned in the papers.",
        "expected_behavior": "acknowledge_limitation",
        "expected_response_contains": ["Based on the provided context"],
        "notes": "Should acknowledge if context is limited for broad questions"
    }
]

