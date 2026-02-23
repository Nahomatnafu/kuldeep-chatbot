# Collective Experiment Branch - Merge Plan

## 🎯 Project Goal
Merge the best features from all team members' RAG chatbot experiments into a unified `collective-experiment` branch with the new Figma-designed frontend.

---

## 📊 Current State Analysis

### **Existing Branches**
- `rag-experiment-nahom` - Fast response, embedded document approach
- `rag-experiment-jake` - Document upload feature (upload each time)
- `rag-experiment-dilasha` - Chroma DB persistence, sidebar, page references with clickable links
- `rag-experiment-dilasha-copy` - Backup branch
- `main` - Base branch (needs proper setup)

### **Frontend Assets**
- `Figma-Chatbot-Recreation-codebase/` - Next.js/TypeScript frontend based on client specifications

### **Key Features Identified (from rag_reflection.md)**

| Feature | Nahom | Jake | Dilasha |
|---------|-------|------|---------|
| Document Upload | ❌ (embedded) | ✅ (each time) | ✅ (persistent) |
| Chroma DB Persistence | ❌ | ❌ | ✅ |
| Sidebar for Uploaded Docs | ❌ | ❌ | ✅ |
| Delete Documents | ❌ | ❌ | ✅ |
| Page Number References | ❌ | ❌ | ✅ |
| Clickable References (opens PDF) | ❌ | ❌ | ✅ |
| Response Speed | ⚡ Fastest | 🟢 Fast | 🟡 Slightly slower |
| Accurate Answers | ✅ | ✅ | ✅ |
| Grounded Responses | ✅ | ⚠️ (sometimes external) | ✅ (strict) |

### **Best Features to Merge**
1. ✅ **Chroma DB with persistence** (Dilasha) - Documents stored after ingestion
2. ✅ **Document upload interface** (Jake/Dilasha) - Users can upload PDFs
3. ✅ **Sidebar with document list** (Dilasha) - View and manage uploaded documents
4. ✅ **Delete document functionality** (Dilasha) - Remove documents from database
5. ✅ **Page number references** (Dilasha) - Show which page info came from
6. ✅ **Clickable references** (Dilasha) - Click to open PDF at specific page
7. ✅ **Strict grounding** (Dilasha/Nahom) - Only answer from retrieved context
8. ✅ **Speed optimization** (Nahom) - Fast response times
9. ✅ **Figma frontend** (Team) - Professional UI matching client specs

---

## 📋 Phase-by-Phase Execution Plan

### **Phase 1: Branch Analysis & Documentation** ⏱️ 15 minutes

**Objective:** Examine each branch to understand implementation details

#### Tasks:
- [ ] **1.1** Checkout `rag-experiment-jake` branch
  ```bash
  git checkout -b rag-experiment-jake origin/rag-experiment-jake
  ```
- [ ] **1.2** Document Jake's implementation:
  - File structure
  - Document upload mechanism
  - API endpoints
  - Frontend components
  
- [ ] **1.3** Checkout `rag-experiment-dilasha` branch
  ```bash
  git checkout -b rag-experiment-dilasha origin/rag-experiment-dilasha
  ```
- [ ] **1.4** Document Dilasha's implementation:
  - Chroma DB setup and persistence
  - Sidebar component structure
  - Delete document functionality
  - Page reference implementation
  - Clickable PDF link mechanism
  
- [ ] **1.5** Review current branch (`rag-experiment-nahom`):
  - Speed optimization techniques
  - Grounding prompt structure
  - Response generation approach

#### Deliverable:
Create `BRANCH_ANALYSIS.md` with detailed notes on each implementation

---

### **Phase 2: Setup Proper Main Branch** ⏱️ 5 minutes

**Objective:** Ensure `main` branch has proper base structure

#### Tasks:
- [ ] **2.1** Checkout `main` branch
  ```bash
  git checkout main
  ```
- [ ] **2.2** Verify/create essential files:
  - `.gitignore` - Protect sensitive files and dependencies
  - `README.md` - Project overview and setup instructions
  - `requirements.txt` - Python dependencies
  - `.env.example` - Environment variable template

- [ ] **2.3** Commit and push if changes made
  ```bash
  git add .
  git commit -m "Setup proper main branch structure"
  git push origin main
  ```

#### Deliverable:
Clean `main` branch ready to serve as base for collective experiment

---

### **Phase 3: Create `collective-experiment` Branch** ⏱️ 10 minutes

**Objective:** Create new branch with base project structure

#### Tasks:
- [ ] **3.1** Create and checkout new branch from `main`
  ```bash
  git checkout main
  git checkout -b collective-experiment
  ```

- [ ] **3.2** Setup base directory structure:
  ```
  collective-experiment/
  ├── backend/              # Flask API (Python)
  │   ├── src/
  │   │   ├── __init__.py
  │   │   ├── app.py       # Main Flask app
  │   │   ├── ingest.py    # Document ingestion
  │   │   ├── retrieval.py # RAG retrieval logic
  │   │   └── utils.py     # Helper functions
  │   ├── chroma_db/       # Chroma vector database
  │   ├── uploads/         # Temporary PDF uploads
  │   ├── requirements.txt
  │   └── .env.example
  ├── frontend/            # Next.js app (from Figma)
  │   ├── src/
  │   │   ├── app/
  │   │   ├── components/
  │   │   └── lib/
  │   ├── public/
  │   ├── package.json
  │   └── next.config.js
  ├── docs/                # Documentation
  │   ├── BRANCH_ANALYSIS.md
  │   └── API.md
  ├── .gitignore
  └── README.md
  ```

- [ ] **3.3** Create base `.gitignore`:
  ```gitignore
  # Python
  __pycache__/
  *.py[cod]
  venv/
  .env

  # Chroma DB
  backend/chroma_db/

  # Uploads
  backend/uploads/*.pdf

  # Node
  frontend/node_modules/
  frontend/.next/
  frontend/out/

  # IDE
  .vscode/
  .idea/
  ```

- [ ] **3.4** Initial commit
  ```bash
  git add .
  git commit -m "Initial structure for collective-experiment branch"
  git push -u origin collective-experiment
  ```

#### Deliverable:
`collective-experiment` branch with clean structure ready for feature integration

---

### **Phase 4: Integrate Backend Features** ⏱️ 45 minutes

**Objective:** Merge best backend features from all branches

#### **4.1 Setup Chroma DB with Persistence** (from Dilasha)

- [ ] **4.1.1** Copy Chroma DB configuration from Dilasha's branch
- [ ] **4.1.2** Implement persistent storage in `backend/src/app.py`:
  ```python
  # Initialize Chroma with persistence
  CHROMA_DB_PATH = "./chroma_db"
  vectorstore = Chroma(
      persist_directory=CHROMA_DB_PATH,
      embedding_function=embeddings
  )
  ```
- [ ] **4.1.3** Create collection management functions:
  - `create_collection(doc_name)`
  - `list_collections()`
  - `delete_collection(doc_name)`

#### **4.2 Document Upload API** (from Jake/Dilasha)

- [ ] **4.2.1** Create upload endpoint in `backend/src/app.py`:
  ```python
  @app.route('/api/upload', methods=['POST'])
  def upload_document():
      # Handle PDF upload
      # Save to uploads/ folder
      # Ingest into Chroma DB
      # Return document metadata
  ```

- [ ] **4.2.2** Implement document ingestion in `backend/src/ingest.py`:
  ```python
  def ingest_pdf(file_path, doc_name):
      # Load PDF
      # Chunk text (1000 chars, 200 overlap)
      # Create embeddings
      # Store in Chroma with metadata
  ```

#### **4.3 Document Management API** (from Dilasha)

- [ ] **4.3.1** Create list documents endpoint:
  ```python
  @app.route('/api/documents', methods=['GET'])
  def list_documents():
      # Return list of uploaded documents
  ```

- [ ] **4.3.2** Create delete document endpoint:
  ```python
  @app.route('/api/documents/<doc_id>', methods=['DELETE'])
  def delete_document(doc_id):
      # Remove from Chroma DB
      # Delete PDF file
  ```

#### **4.4 RAG Query with Page References** (from Dilasha)

- [ ] **4.4.1** Update retrieval to include page metadata:
  ```python
  # Store page numbers during ingestion
  metadata = {
      "source": doc_name,
      "page": page_number,
      "chunk_id": chunk_id
  }
  ```

- [ ] **4.4.2** Create query endpoint with references:
  ```python
  @app.route('/api/ask', methods=['POST'])
  def ask_question():
      # Retrieve relevant chunks
      # Generate answer
      # Return answer + page references
      # Format: {"answer": "...", "references": [{"page": 3, "doc": "file.pdf"}]}
  ```

#### **4.5 Strict Grounding Prompt** (from Nahom/Dilasha)

- [ ] **4.5.1** Implement strict grounding rules in prompt:
  ```python
  GROUNDING_PROMPT = """You are a careful research assistant.

  STRICT RULES:
  1. Answer ONLY from the provided context
  2. If context doesn't contain the answer, say "I don't have enough information"
  3. Do NOT use external knowledge
  4. Every claim must be traceable to the context

  Context: {context}
  Question: {question}
  Answer:"""
  ```

#### **4.6 Speed Optimization** (from Nahom)

- [ ] **4.6.1** Optimize chunk retrieval (k=6 most relevant)
- [ ] **4.6.2** Use efficient embedding model (text-embedding-ada-002)
- [ ] **4.6.3** Implement caching for repeated queries
- [ ] **4.6.4** Use streaming responses for faster perceived speed

#### Deliverable:
Fully functional Flask backend with all features integrated

---

### **Phase 5: Integrate Figma Frontend** ⏱️ 60 minutes

**Objective:** Restructure project to use Next.js frontend and connect to Flask backend

#### **5.1 Copy Figma Frontend**

- [ ] **5.1.1** Copy contents from `Figma-Chatbot-Recreation-codebase/src/` to `frontend/src/`
  ```bash
  cp -r Figma-Chatbot-Recreation-codebase/src/* frontend/src/
  ```

- [ ] **5.1.2** Setup Next.js configuration files:
  - `package.json` - Dependencies
  - `next.config.js` - Next.js config
  - `tsconfig.json` - TypeScript config
  - `tailwind.config.js` - Tailwind CSS config (if used)

#### **5.2 Update API Integration**

- [ ] **5.2.1** Update `frontend/src/lib/chatApi.ts` to connect to Flask backend:
  ```typescript
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

  export async function uploadDocument(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      body: formData,
    });
    return response.json();
  }

  export async function askQuestion(question: string, docId?: string) {
    const response = await fetch(`${API_BASE_URL}/api/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, doc_id: docId }),
    });
    return response.json();
  }

  export async function getDocuments() {
    const response = await fetch(`${API_BASE_URL}/api/documents`);
    return response.json();
  }

  export async function deleteDocument(docId: string) {
    const response = await fetch(`${API_BASE_URL}/api/documents/${docId}`, {
      method: 'DELETE',
    });
    return response.json();
  }
  ```

#### **5.3 Add Sidebar Component** (from Dilasha's design)

- [ ] **5.3.1** Create `frontend/src/components/DocumentSidebar.tsx`:
  ```typescript
  // Sidebar showing uploaded documents
  // - List all documents
  // - Highlight active document
  // - Delete button for each document
  // - Upload new document button
  ```

- [ ] **5.3.2** Integrate sidebar into main layout

#### **5.4 Add Page Reference Display** (from Dilasha's design)

- [ ] **5.4.1** Update `ChatBubble.tsx` to show page references:
  ```typescript
  interface Reference {
    page: number;
    doc: string;
    doc_id: string;
  }

  // Display references below answer
  // Make references clickable to open PDF at specific page
  ```

- [ ] **5.4.2** Implement PDF viewer with page navigation:
  ```typescript
  // Use react-pdf or similar library
  // Open PDF at specific page when reference clicked
  ```

#### **5.5 Setup CORS for Flask Backend**

- [ ] **5.5.1** Add CORS support in `backend/src/app.py`:
  ```python
  from flask_cors import CORS

  app = Flask(__name__)
  CORS(app, origins=['http://localhost:3000'])
  ```

- [ ] **5.5.2** Add `flask-cors` to `backend/requirements.txt`

#### **5.6 Environment Configuration**

- [ ] **5.6.1** Create `frontend/.env.local`:
  ```env
  NEXT_PUBLIC_API_URL=http://localhost:5000
  ```

- [ ] **5.6.2** Create `backend/.env`:
  ```env
  OPENAI_API_KEY=your_key_here
  FLASK_ENV=development
  FLASK_PORT=5000
  ```

#### Deliverable:
Fully integrated Next.js frontend connected to Flask backend with all UI components

---

### **Phase 6: Testing & Validation** ⏱️ 30 minutes

**Objective:** Ensure all features work correctly

#### **6.1 Backend Testing**

- [ ] **6.1.1** Test document upload:
  - Upload small PDF (10 pages)
  - Verify ingestion into Chroma DB
  - Check document appears in list

- [ ] **6.1.2** Test document query:
  - Ask question about uploaded document
  - Verify accurate answer
  - Check page references are correct

- [ ] **6.1.3** Test document deletion:
  - Delete document from sidebar
  - Verify removed from Chroma DB
  - Verify PDF file deleted

- [ ] **6.1.4** Test large document:
  - Upload 156-page document
  - Measure ingestion time
  - Test query response time
  - Verify accuracy

#### **6.2 Frontend Testing**

- [ ] **6.2.1** Test UI components:
  - Document upload interface
  - Sidebar display and interactions
  - Chat interface
  - Page reference display

- [ ] **6.2.2** Test clickable references:
  - Click page reference
  - Verify PDF opens at correct page

- [ ] **6.2.3** Test responsive design:
  - Desktop view
  - Tablet view
  - Mobile view

#### **6.3 Integration Testing**

- [ ] **6.3.1** Test full workflow:
  1. Upload document
  2. See it appear in sidebar
  3. Ask question
  4. Receive answer with references
  5. Click reference to view page
  6. Delete document

- [ ] **6.3.2** Test edge cases:
  - Upload invalid file type
  - Ask question with no documents uploaded
  - Ask question outside document scope
  - Upload duplicate document

#### **6.4 Performance Testing**

- [ ] **6.4.1** Measure response times:
  - Document upload time
  - Query response time
  - Compare with individual branches

- [ ] **6.4.2** Verify speed optimization:
  - Should be close to Nahom's speed
  - Acceptable trade-off for additional features

#### Deliverable:
Fully tested, production-ready chatbot with all features working

---

## 📝 Task Checklist Summary

### Phase 1: Branch Analysis ✅
- [ ] Analyze Jake's branch
- [ ] Analyze Dilasha's branch
- [ ] Review Nahom's branch
- [ ] Create BRANCH_ANALYSIS.md

### Phase 2: Setup Main ✅
- [ ] Verify main branch structure
- [ ] Add essential files
- [ ] Commit and push

### Phase 3: Create Collective Branch ✅
- [ ] Create collective-experiment branch
- [ ] Setup directory structure
- [ ] Create .gitignore
- [ ] Initial commit

### Phase 4: Backend Integration ✅
- [ ] Chroma DB persistence
- [ ] Document upload API
- [ ] Document management API
- [ ] RAG query with page references
- [ ] Strict grounding prompt
- [ ] Speed optimization

### Phase 5: Frontend Integration ✅
- [ ] Copy Figma frontend
- [ ] Update API integration
- [ ] Add sidebar component
- [ ] Add page reference display
- [ ] Setup CORS
- [ ] Environment configuration

### Phase 6: Testing ✅
- [ ] Backend testing
- [ ] Frontend testing
- [ ] Integration testing
- [ ] Performance testing

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 18+
- OpenAI API key
- Git

### Quick Start

1. **Clone and setup:**
   ```bash
   git clone <repo-url>
   cd kuldeep-chatbot
   git checkout collective-experiment
   ```

2. **Setup backend:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Add your OPENAI_API_KEY to .env
   python src/app.py
   ```

3. **Setup frontend:**
   ```bash
   cd frontend
   npm install
   cp .env.example .env.local
   npm run dev
   ```

4. **Access the app:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000

---

## 📚 Key Files Reference

### Backend
- `backend/src/app.py` - Main Flask application
- `backend/src/ingest.py` - Document ingestion logic
- `backend/src/retrieval.py` - RAG retrieval logic
- `backend/requirements.txt` - Python dependencies

### Frontend
- `frontend/src/app/page.tsx` - Main page
- `frontend/src/components/ChatPage.tsx` - Chat interface
- `frontend/src/components/DocumentSidebar.tsx` - Document sidebar
- `frontend/src/lib/chatApi.ts` - API integration

---

## 🎯 Success Criteria

The collective-experiment branch is complete when:

✅ Users can upload PDF documents
✅ Documents persist in Chroma DB
✅ Sidebar shows all uploaded documents
✅ Users can delete documents
✅ Chatbot answers questions accurately
✅ Answers include page number references
✅ References are clickable and open PDF at correct page
✅ Responses are fast (close to Nahom's speed)
✅ Answers are strictly grounded (no hallucination)
✅ Frontend matches Figma design
✅ All features work on 156-page documents

---

## 👥 Team Contributions

- **Nahom**: Speed optimization, strict grounding, embedded document approach
- **Jake**: Document upload feature, testing methodology
- **Dilasha**: Chroma DB persistence, sidebar, page references, clickable links
- **Team**: Figma frontend design and implementation

---

## 📞 Support

For questions or issues during implementation, refer to:
- `BRANCH_ANALYSIS.md` - Detailed analysis of each branch
- `rag_reflection.md` - Team observations and testing notes
- Individual branch READMEs

---

**Last Updated:** 2026-02-23
**Status:** Ready for implementation
**Estimated Total Time:** ~2.5 hours

