"""
Flask Web Application for RAG Chatbot

Simple web interface for the AI music detection Q&A system.
"""

import os
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

# Load environment variables
load_dotenv()

# Configuration
CHROMA_DB_DIR = "chroma_db"
MODEL_NAME = "gpt-3.5-turbo"
NUM_RELEVANT_CHUNKS = 6

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Global variables for the QA chain (loaded once at startup)
qa_chain = None
vectorstore = None
llm = None  # Store LLM globally for creating new memory instances

# Store conversation memories per session
conversation_memories = {}


def initialize_qa_chain():
    """Initialize the QA chain at startup."""
    global qa_chain, vectorstore, llm

    print("🔧 Initializing QA system with conversational memory...")

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

    # Initialize LLM (store globally for creating memories)
    llm = ChatOpenAI(
        model_name=MODEL_NAME,
        temperature=0,
    )

    # Create custom prompt for conversational retrieval
    # Note: ConversationalRetrievalChain uses different template variables
    condense_question_prompt = PromptTemplate.from_template(
        """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question that includes relevant context from the conversation history.

Chat History:
{chat_history}

Follow Up Question: {question}

Standalone question:"""
    )

    qa_prompt_template = """You are a careful research assistant. Your ONLY job is to extract and summarize information from the provided context.

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

    QA_PROMPT = PromptTemplate(
        template=qa_prompt_template,
        input_variables=["context", "question"]
    )

    # Note: We'll create individual chains with memory per session
    # This is just a placeholder to indicate the system is ready
    qa_chain = "ready"  # Will be created per session

    print("✅ QA system ready with conversational memory support!")


@app.route('/')
def index():
    """Serve the main chat interface."""
    return render_template('index.html')


def get_or_create_conversation_chain(session_id):
    """Get or create a conversational chain for a session."""
    global conversation_memories

    if session_id not in conversation_memories:
        # Create new memory for this session
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )

        # Create custom prompt for conversational retrieval
        # This reformulates follow-up questions to include context from chat history
        condense_question_prompt = PromptTemplate.from_template(
            """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.

If the chat history is empty, just return the question as-is.
If there is chat history, incorporate relevant context to make the question standalone.

Chat History:
{chat_history}

Follow Up Question: {question}

Standalone question:"""
        )

        qa_prompt_template = """You are a careful research assistant. Your ONLY job is to extract and summarize information from the provided context.

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

        QA_PROMPT = PromptTemplate(
            template=qa_prompt_template,
            input_variables=["context", "question"]
        )

        # Create conversational retrieval chain
        chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vectorstore.as_retriever(
                search_kwargs={"k": NUM_RELEVANT_CHUNKS}
            ),
            memory=memory,
            return_source_documents=True,
            condense_question_prompt=condense_question_prompt,
            combine_docs_chain_kwargs={"prompt": QA_PROMPT}
        )

        conversation_memories[session_id] = {
            'chain': chain,
            'memory': memory
        }

    return conversation_memories[session_id]['chain']


@app.route('/api/ask', methods=['POST'])
def ask():
    """Handle question from the frontend."""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        session_id = data.get('session_id', 'default')

        if not question:
            return jsonify({'error': 'Question cannot be empty'}), 400

        # Get or create conversation chain for this session
        conversation_chain = get_or_create_conversation_chain(session_id)

        # Run the query with conversation history
        result = conversation_chain.invoke({"question": question})

        answer = result["answer"]
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
            'sources': sources,
            'session_id': session_id
        })

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/clear', methods=['POST'])
def clear_conversation():
    """Clear conversation history for a session."""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')

        if session_id in conversation_memories:
            del conversation_memories[session_id]
            return jsonify({
                'status': 'success',
                'message': 'Conversation history cleared'
            })
        else:
            return jsonify({
                'status': 'success',
                'message': 'No conversation history to clear'
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'qa_chain_loaded': qa_chain is not None,
        'active_sessions': len(conversation_memories)
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

