"""
Flask Web Application for RAG Chatbot

Simple web interface for the AI music detection Q&A system.
"""

import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Load environment variables
load_dotenv()

# Configuration
CHROMA_DB_DIR = "chroma_db"
MODEL_NAME = "gpt-3.5-turbo"
NUM_RELEVANT_CHUNKS = 6

app = Flask(__name__)

# Global variables for the QA chain (loaded once at startup)
qa_chain = None
vectorstore = None


def initialize_qa_chain():
    """Initialize the QA chain at startup."""
    global qa_chain, vectorstore
    
    print("🔧 Initializing QA system...")
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not found in environment variables.")
    
    # Check if vector database exists
    if not os.path.exists(CHROMA_DB_DIR):
        raise FileNotFoundError(
            f"Vector database not found at {CHROMA_DB_DIR}/. "
            "Please run 'python src/ingest.py' first."
        )
    
    # Load vector store
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    vectorstore = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embeddings
    )
    
    # Initialize LLM
    llm = ChatOpenAI(
        model_name=MODEL_NAME,
        temperature=0,
    )
    
    # Create prompt template
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
    
    # Create QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(
            search_kwargs={"k": NUM_RELEVANT_CHUNKS}
        ),
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )
    
    print("✅ QA system ready!")


@app.route('/')
def index():
    """Serve the main chat interface."""
    return render_template('index.html')


@app.route('/api/ask', methods=['POST'])
def ask():
    """Handle question from the frontend."""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Question cannot be empty'}), 400
        
        # Run the query
        result = qa_chain.invoke({"query": question})
        
        answer = result["result"]
        source_docs = result["source_documents"]
        
        # Format sources
        sources = []
        for i, doc in enumerate(source_docs, 1):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "?")
            snippet = doc.page_content[:150].replace("\n", " ")
            if len(doc.page_content) > 150:
                snippet += "..."
            
            sources.append({
                "id": i,
                "file": os.path.basename(source),
                "page": page + 1,
                "snippet": snippet
            })
        
        return jsonify({
            'answer': answer,
            'sources': sources
        })
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'qa_chain_loaded': qa_chain is not None
    })


if __name__ == '__main__':
    # Initialize QA chain before starting the server
    initialize_qa_chain()
    
    # Run the Flask app
    print("\n" + "=" * 60)
    print("🚀 RAG Chatbot Web Interface")
    print("=" * 60)
    print("📂 Open your browser and go to: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

