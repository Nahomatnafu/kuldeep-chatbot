"""
Query Script for RAG Q&A System

Command-line interface to ask questions about ingested PDFs.
"""

import os
from dotenv import load_dotenv

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Load environment variables
load_dotenv()

# Configuration
CHROMA_DB_DIR = "vector_db"
MODEL_NAME = "gpt-3.5-turbo"
NUM_RELEVANT_CHUNKS = 4


def format_docs(docs):
    """Format retrieved documents into a single string."""
    return "\n\n".join(doc.page_content for doc in docs)


def load_qa_chain():
    """
    Load the vector store and create a QA chain using LCEL (LangChain Expression Language).
    
    Returns:
        QA chain ready to answer questions and vectorstore
    """
    print("🔍 Loading vector database...")
    
    # Check if vector database exists
    if not os.path.exists(CHROMA_DB_DIR):
        raise FileNotFoundError(
            f"Vector database not found at {CHROMA_DB_DIR}/. "
            "Please run 'python src/ingest.py' first to ingest PDFs."
        )
    
    # Initialize embeddings (same model used for ingestion)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Load vector store
    vectorstore = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embeddings
    )
    
    print(f"✓ Loaded vector database with {vectorstore._collection.count()} chunks\n")
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not found.")
        print("   You can still test retrieval, but won't get AI-generated answers.")
        print("   Set your API key in .env file to use OpenAI for responses.\n")
        return None, vectorstore
    
    # Initialize LLM
    llm = ChatOpenAI(
        model_name=MODEL_NAME,
        temperature=0,
    )
    
    # Create retriever
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": NUM_RELEVANT_CHUNKS}
    )
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_template("""You are a helpful assistant answering questions based on the provided context.

Use ONLY the information from the context below to answer the question.
If the answer is not in the context, say "I don't have enough information to answer that question."

Context:
{context}

Question: {question}

Answer:""")
    
    # Create chain using LCEL
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    print("✓ QA system ready!\n")
    
    return rag_chain, retriever, vectorstore


def show_sources(source_docs):
    """Display source documents with metadata."""
    print("\n📚 Sources:")
    print("=" * 60)
    for i, doc in enumerate(source_docs, 1):
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "?")
        snippet = doc.page_content[:200].replace("\n", " ")
        if len(doc.page_content) > 200:
            snippet += "..."
        
        print(f"\n[{i}] {os.path.basename(source)} (Page {page + 1})")
        print(f"    {snippet}")
    print("=" * 60)


def retrieval_only_mode(vectorstore, question):
    """Test retrieval without using OpenAI API."""
    print("\n🔍 Running in retrieval-only mode (no AI generation)")
    print("=" * 60)
    
    # Retrieve relevant documents
    docs = vectorstore.similarity_search(question, k=NUM_RELEVANT_CHUNKS)
    
    print(f"\nFound {len(docs)} relevant chunks:")
    show_sources(docs)


def ask_question(rag_chain, retriever, vectorstore, question):
    """
    Ask a question and get an answer with sources.
    
    Args:
        rag_chain: The RAG chain (or None if API key not available)
        retriever: The retriever for getting source documents
        vectorstore: The vector store for retrieval (fallback)
        question: Question to ask
    """
    print("\n💬 Question:")
    print(f"   {question}")
    
    # Get source documents
    if retriever:
        source_docs = retriever.invoke(question)
    else:
        source_docs = vectorstore.similarity_search(question, k=NUM_RELEVANT_CHUNKS)
    
    if rag_chain is None:
        # No API key - just show retrieval results
        print("\n🔍 Running in retrieval-only mode (no AI generation)")
        print("=" * 60)
        print(f"\nFound {len(source_docs)} relevant chunks:")
        show_sources(source_docs)
        return
    
    # Run the query
    print("\n🤔 Thinking...")
    answer = rag_chain.invoke(question)
    
    # Display answer
    print("\n✅ Answer:")
    print("=" * 60)
    print(answer)
    print("=" * 60)
    
    # Display sources
    show_sources(source_docs)


def main():
    """Main interactive loop."""
    print("=" * 60)
    print("🤖 PDF Q&A CHATBOT")
    print("=" * 60)
    print()
    
    try:
        # Load QA chain
        result = load_qa_chain()
        
        if result[0] is None:
            # No API key - retrieval only mode
            rag_chain = None
            retriever = None
            vectorstore = result[1]
        else:
            # Full mode with AI
            rag_chain, retriever, vectorstore = result
        
        # Interactive mode
        print("💡 Ask questions about your PDF documents.")
        print("   Type 'quit' or 'exit' to end the session.\n")
        
        while True:
            # Get question from user
            question = input("\n❓ Your question: ").strip()
            
            # Check for exit
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            # Skip empty questions
            if not question:
                continue
            
            # Process question
            ask_question(rag_chain, retriever, vectorstore, question)
    
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 To get started:")
        print("   1. Add PDF files to data/pdfs/")
        print("   2. Run: python src/ingest.py")
        print("   3. Then run this script again")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
