"""
Flask Web Application for PDF Chatbot

Simple web UI for uploading PDFs and asking questions.
"""

import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data/pdfs'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Configuration
CHROMA_DB_DIR = "vector_db"
MODEL_NAME = "gpt-3.5-turbo"
NUM_RELEVANT_CHUNKS = 4

# Global variables for chain and vectorstore
rag_chain = None
retriever = None
vectorstore = None


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def format_docs(docs):
    """Format retrieved documents into a single string."""
    return "\n\n".join(doc.page_content for doc in docs)


def initialize_chain():
    """Initialize or reinitialize the RAG chain."""
    global rag_chain, retriever, vectorstore
    
    # Check if vector database exists
    if not os.path.exists(CHROMA_DB_DIR):
        return False, "No documents ingested yet. Please upload a PDF first."
    
    try:
        # Initialize embeddings
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
        
        # Check for OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            return False, "OpenAI API key not found. Please set it in .env file."
        
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
        prompt = ChatPromptTemplate.from_template(
            """You are a helpful assistant answering questions based on the provided context.

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
        
        return True, "System ready!"
    
    except Exception as e:
        return False, f"Error initializing system: {str(e)}"


def ingest_pdf(filepath):
    """Ingest a PDF file into the vector database."""
    try:
        # Load PDF
        loader = PyPDFLoader(filepath)
        documents = loader.load()
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documents)
        
        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Create or update vector store
        if os.path.exists(CHROMA_DB_DIR):
            # Add to existing database
            vectorstore = Chroma(
                persist_directory=CHROMA_DB_DIR,
                embedding_function=embeddings
            )
            vectorstore.add_documents(chunks)
        else:
            # Create new database
            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                persist_directory=CHROMA_DB_DIR
            )
        
        return True, f"Successfully ingested {len(chunks)} chunks from {os.path.basename(filepath)}"
    
    except Exception as e:
        return False, f"Error ingesting PDF: {str(e)}"


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle PDF file upload and ingestion."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Only PDF files are allowed'})
    
    try:
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)
        
        # Ingest PDF
        success, message = ingest_pdf(filepath)
        
        if success:
            # Reinitialize chain
            init_success, init_message = initialize_chain()
            if not init_success:
                return jsonify({'success': False, 'message': init_message})
            
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Upload error: {str(e)}'})


@app.route('/ask', methods=['POST'])
def ask_question():
    """Handle question answering requests."""
    data = request.get_json()
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({'success': False, 'message': 'No question provided'})
    
    # Initialize chain if not already done
    if rag_chain is None:
        success, message = initialize_chain()
        if not success:
            return jsonify({'success': False, 'message': message})
    
    try:
        # Get answer
        answer = rag_chain.invoke(question)
        
        # Get source documents
        source_docs = retriever.invoke(question)
        
        # Format sources
        sources = []
        for doc in source_docs:
            sources.append({
                'source': os.path.basename(doc.metadata.get('source', 'Unknown')),
                'page': doc.metadata.get('page', 0) + 1,
                'content': doc.page_content  # Full content, not truncated
            })
        
        return jsonify({
            'success': True,
            'answer': answer,
            'sources': sources
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/status', methods=['GET'])
def status():
    """Check system status."""
    has_db = os.path.exists(CHROMA_DB_DIR)
    has_api_key = bool(os.getenv("OPENAI_API_KEY"))
    
    return jsonify({
        'has_documents': has_db,
        'has_api_key': has_api_key,
        'ready': has_db and has_api_key
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 PDF CHATBOT WEB APPLICATION")
    print("="*60)
    print("\n📝 Starting Flask server...")
    print("\n🌐 Open your browser to: http://localhost:5000")
    print("\n💡 Press Ctrl+C to stop the server\n")
    
    app.run(debug=True, port=5000)
