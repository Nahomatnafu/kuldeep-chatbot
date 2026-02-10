"""
Query Interface: Question → Retrieval → Answer

This script:
1. Takes a question from the user
2. Retrieves relevant chunks from Chroma
3. Sends to OpenAI with context
4. Returns the answer
"""

import os
import sys
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Load environment variables
load_dotenv()

# Configuration
CHROMA_DB_DIR = "chroma_db"
MODEL_NAME = "gpt-3.5-turbo"  # Fast and cheap for learning
NUM_RELEVANT_CHUNKS = 6  # How many chunks to retrieve (increased for better coverage)


def load_vector_store():
    """Load the existing Chroma vector store."""
    print("📂 Loading vector database...")

    if not os.path.exists(CHROMA_DB_DIR):
        print(f"\n❌ Error: Vector database not found at {CHROMA_DB_DIR}/")
        print("Please run 'python src/ingest.py' first to create the database.")
        sys.exit(1)

    # Initialize the same embeddings model used during ingestion
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

    # Load the persisted vector store
    vectorstore = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embeddings
    )

    print(f"✅ Loaded vector database from {CHROMA_DB_DIR}/")
    return vectorstore


def create_qa_chain(vectorstore):
    """Create a question-answering chain."""
    print("🔗 Setting up QA chain...")

    # Initialize the LLM
    llm = ChatOpenAI(
        model_name=MODEL_NAME,
        temperature=0,  # 0 = deterministic, factual answers
    )

    # Create a custom prompt template with STRICT grounding rules
    prompt_template = """You are a careful research assistant. Your ONLY job is to extract and summarize information from the provided context.

STRICT GROUNDING RULES (DO NOT VIOLATE):
1. Answer ONLY from the retrieved context below - do NOT add facts not present in it
2. Every claim in your answer MUST be traceable to a specific chunk below
3. If the context is insufficient or doesn't contain the answer → say "The provided context does not contain enough information to answer this question."
4. Do NOT infer, extrapolate, or fill gaps with general knowledge
5. For lists (models, methods, etc.) → ONLY list what is explicitly named in the context
6. If the question is broad but context is limited → acknowledge the limitation: "Based on the provided context, the following [X] are mentioned..."
7. Your answer should read like a summary of the chunks below, NOT like an essay

Retrieved Context:
{context}

Question: {question}

Answer (extract/summarize ONLY from context above):"""

    PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    # Create the retrieval QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",  # "stuff" = put all retrieved docs into prompt
        retriever=vectorstore.as_retriever(
            search_kwargs={"k": NUM_RELEVANT_CHUNKS}
        ),
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )

    print(f"✅ QA chain ready (using {MODEL_NAME})")
    return qa_chain


def ask_question(qa_chain, question):
    """Ask a question and get an answer."""
    print(f"\n❓ Question: {question}")
    print("\n🔍 Retrieving relevant information...")

    # Run the query
    result = qa_chain.invoke({"query": question})

    answer = result["result"]
    source_docs = result["source_documents"]

    # Show retrieved chunks FIRST (for transparency and debugging)
    print(f"\n📚 Retrieved Context ({len(source_docs)} chunks):")
    print("-" * 60)
    for i, doc in enumerate(source_docs, 1):
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "?")
        # Show first 200 chars of the chunk
        snippet = doc.page_content[:200].replace("\n", " ")
        if len(doc.page_content) > 200:
            snippet += "..."

        print(f"\n[{i}] {os.path.basename(source)} (page {page + 1})")
        print(f"    \"{snippet}\"")

    print("\n" + "-" * 60)
    print(f"\n💡 Answer:\n{answer}")

    return answer


def interactive_mode(qa_chain):
    """Run in interactive mode - keep asking questions."""
    print("\n" + "=" * 60)
    print("🤖 INTERACTIVE Q&A MODE")
    print("=" * 60)
    print("Ask questions about AI-generated music detection!")
    print("Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            question = input("Your question: ").strip()

            if question.lower() in ["quit", "exit", "q"]:
                print("\n👋 Goodbye!")
                break

            if not question:
                print("Please enter a question.\n")
                continue

            ask_question(qa_chain, question)
            print("\n" + "-" * 60 + "\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def main():
    """Main query interface."""
    print("=" * 60)
    print("🚀 RAG QUERY INTERFACE")
    print("=" * 60)

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file with your API key.")
        sys.exit(1)

    try:
        # Load the vector store
        vectorstore = load_vector_store()

        # Create the QA chain
        qa_chain = create_qa_chain(vectorstore)

        # Check if a question was provided as command line argument
        if len(sys.argv) > 1:
            # Single question mode
            question = " ".join(sys.argv[1:])
            ask_question(qa_chain, question)
        else:
            # Interactive mode
            interactive_mode(qa_chain)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()

