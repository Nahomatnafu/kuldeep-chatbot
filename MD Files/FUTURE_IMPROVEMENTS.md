# Future Improvements — Kuldeep AI Chatbot (Next Semester Roadmap)

> This document outlines recommended improvements for the next team taking over this project.
> The next team will be merging this chatbot with a second team's implementation (FastAPI + Supabase)
> and selecting the best features from both to build a unified, production-ready system.

---

## 1. Vector Database — Explore Alternatives to ChromaDB

The current system uses **ChromaDB**, which runs locally. It works well for development but has limitations at scale. The next team should evaluate cloud-native alternatives:

| Database | Type | Why Consider It |
|---|---|---|
| **Pinecone** | Cloud-native, managed | No setup, scales to millions of vectors, enterprise-grade reliability, ideal for production |
| **Weaviate** | Open-source, hybrid search | Supports keyword + vector search combined (BM25 + embeddings), better recall on technical documents |
| **Supabase (pgvector)** | PostgreSQL extension | Team B already uses Supabase — merging both projects could unify the database layer into one platform |
| **Qdrant** | Open-source, cloud option | Strong filtering support, good for metadata-heavy document collections |

**Recommendation:** If Team B's Supabase infrastructure is solid, using **pgvector on Supabase** would simplify the merged architecture by eliminating a separate vector database entirely.

---

## 2. Cloud Deployment — Move Beyond Docker Desktop

Currently, running the chatbot requires the user to install Docker Desktop and run `docker-compose up` locally. This is fine for developers but not ideal for real client deployments.

### Better deployment options

| Platform | What it solves | Notes |
|---|---|---|
| **Render** | Deploy the Flask backend as a web service with zero Docker Desktop required | Free tier available, auto-deploys from GitHub, persistent disk for ChromaDB/documents |
| **Railway** | Simple container-based deployment | Similar to Render, great for student/small team projects |
| **Fly.io** | Global edge deployment | Good if latency matters for the client's location |
| **Vercel** | Next.js frontend only | Already optimized for Next.js — pair with Render for backend |
| **AWS ECS / Google Cloud Run** | Enterprise-grade container hosting | More complex to set up but production-ready and scalable |

### Ideal split for next team

```
Frontend  → Vercel (automatic Next.js deploys, free tier)
Backend   → Render (Docker container, persistent disk for documents)
Vector DB → Pinecone or Supabase pgvector (cloud-hosted, no local storage)
```

This removes the need for clients to install anything — they just open a URL in their browser.

---

## 3. Expanded Testing — RAGAS and Beyond

The current RAGAS regression suite has ~24 test cases. This is a solid foundation but needs to grow significantly for production confidence.

### What the next team should do

- **Scale to 100+ test cases** covering a broader range of manufacturing document topics — machine startup, safety procedures, quality control, equipment specs, emergency shutdowns
- **Fix context_recall ground truths** — current ground truths were written from general knowledge, not from the actual uploaded documents. Rewrite them verbatim from document text to get accurate scores (currently failing at 0.499, threshold is 0.60)
- **Add CI/CD automation** — set up GitHub Actions to run the regression suite automatically on every pull request so no merge degrades quality
- **Adversarial test cases** — add tests that intentionally ask questions not in any document to ensure the guard and grounding rules hold
- **Test with 50–100+ documents** — the current test suite was built with a small document set. Large document collections stress-test chunk retrieval, deduplication, and response coherence

### Example GitHub Actions workflow idea

```yaml
on: [pull_request]
jobs:
  ragas-regression:
    runs-on: ubuntu-latest
    steps:
      - Start Flask backend
      - Run: python tests/regression_test.py --no-fail
      - Post scores as PR comment
```

---

## 4. RAG Pipeline Improvements

The retrieval pipeline can be made significantly smarter:

- **Hybrid search (BM25 + vector)** — combine keyword matching with semantic search. Technical documents often use exact part numbers or procedure codes that pure vector search misses
- **Reranking** — after retrieving 12 chunks, use a cross-encoder model (e.g. Cohere Rerank) to re-score and reorder them by true relevance before sending to the LLM. This improves answer quality without increasing chunk count
- **Smarter chunking** — the current splitter uses fixed character counts (1000 chars, 200 overlap). Explore semantic chunking (split at meaningful boundaries like headings and paragraphs) for cleaner context
- **Query expansion** — before searching, generate 2–3 alternative phrasings of the question and search with all of them. Improves recall on ambiguous queries
- **Document summarization index** — for very large documents, maintain a short summary of each document and search summaries first to decide which documents to retrieve from

---

## 5. LLM and Model Improvements

- **Compare gpt-4o vs gpt-4o-mini** — the current model is gpt-4o-mini (fast, cheap). For manufacturing safety-critical answers, evaluate whether gpt-4o produces meaningfully better grounded responses
- **Streaming responses** — implement Server-Sent Events (SSE) so the answer streams token-by-token to the user instead of waiting for the full response. Improves perceived speed significantly
- **Model fallback** — if the primary model is unavailable, automatically fall back to a backup model
- **System prompt versioning** — track changes to the QA prompt and guard prompt in version control so regressions are traceable

---

## 6. Multi-User and Authentication

The current system has no user authentication — anyone with the URL can use it and all sessions share the same document store.

- **User authentication** — integrate Supabase Auth (Team B already uses Supabase) for login/logout with email or SSO
- **Per-user document isolation** — allow each user to upload their own private documents, separate from a shared company knowledge base
- **Role-based access** — operators see only their line's documents; managers see all documents
- **Persistent session history** — store conversation history in a database so users can revisit past conversations

---

## 7. Merging the Two Chatbot Projects

The core challenge for next semester is combining this implementation (Flask + ChromaDB) with Team B's implementation (FastAPI + Supabase). Recommended approach:

1. **Run a side-by-side comparison** — give both chatbots the same set of 20+ questions and score them with RAGAS. Let data decide which RAG pipeline performs better, not team preference
2. **Adopt the best backend framework** — FastAPI has native async support and auto-generated API docs (Swagger). Flask is simpler. Benchmark both under load before deciding
3. **Unify on Supabase** — Team B's Supabase infrastructure handles auth, database, and vector storage in one platform. Migrating ChromaDB vectors to pgvector would simplify the stack
4. **Keep the best frontend** — compare both UIs on usability. If one team's frontend is clearly better, use it as the base
5. **Preserve the RAGAS test suite** — this project's regression tests are a significant asset. Carry them forward into the merged system and expand them

---

## 8. Performance and Observability

- **Response time monitoring** — track how long each RAG pipeline step takes (embedding, retrieval, LLM call). Use this data to identify bottlenecks
- **Usage analytics** — log what questions users ask most often. Use this to validate that the document collection covers real user needs
- **Error tracking** — integrate Sentry or a similar tool to catch and alert on backend errors in production
- **Rate limiting** — add per-user API rate limits to prevent runaway OpenAI costs

---

## Summary Table

| Area | Current State | Recommended Next Step |
|---|---|---|
| Vector DB | ChromaDB (local) | Evaluate Supabase pgvector or Pinecone |
| Deployment | Docker Desktop (local) | Render (backend) + Vercel (frontend) |
| Testing | 24 RAGAS test cases | 100+ cases + GitHub Actions CI/CD |
| RAG pipeline | Vector search, 12 chunks | Add hybrid search + reranking |
| LLM | gpt-4o-mini | Benchmark gpt-4o, add streaming |
| Auth | None | Supabase Auth (leverage Team B's work) |
| Merger strategy | Separate projects | Side-by-side RAGAS comparison first |
