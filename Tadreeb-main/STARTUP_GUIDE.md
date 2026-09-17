# Tadreeb Project - Complete Startup Guide

## ✅ Project Setup Complete

All dependencies have been installed successfully:
- **Frontend**: npm packages installed (React, Vite, Tailwind)
- **Backend**: Python packages installed (FastAPI, RAG Pipeline, etc.)
- **RAG Pipeline**: All components ready

---

## 🚀 Quick Start (2 Commands)

### Terminal 1: Start Backend API (Port 8000)
```bash
cd D:\project\Tadreeb-main\Tadreeb-main\Tadreeb-updated-tadreeb (1)\Tadreeb-updated-tadreeb\Tadreeb-main\06_app
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Terminal 2: Start Frontend App (Port 5173)
```bash
cd D:\project\Tadreeb-main\Tadreeb-main\Tadreeb-updated-tadreeb (1)\Tadreeb-updated-tadreeb\Tadreeb-main\Frontend
npm run dev
```

You should see:
```
  VITE v8.3.0  ready in XXX ms
  ➜  Local:   http://localhost:5173/
```

---

## 📱 Access Your Application

Once both servers are running, open your browser:

### **🌐 Frontend (Main App)**
👉 **http://localhost:5173/**

This is where you interact with the Tadreeb chat interface.

### **🔌 Backend API (Development)**
- **API Base**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs ← Interactive API testing
- **ReDoc**: http://localhost:8000/redoc

### **💻 Other Useful Endpoints**
- Health Check: `curl http://localhost:8000/health`
- Chat API: `POST http://localhost:8000/api/chat`

---

## 🏗️ Project Architecture

```
Tadreeb-main/
│
├── Frontend/                 # React + Vite app (Port 5173)
│   ├── src/
│   │   ├── components/      # React components (Chat, Sidebar, etc.)
│   │   ├── services/        # API integration
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
│
├── 06_app/                  # FastAPI backend (Port 8000)
│   ├── api.py              # Main API endpoints
│   └── main.py             # Server entry point
│
├── 05_generation/           # LLM Generation
│   ├── generate_answer.py  # RAG + LLM pipeline
│   ├── prompt_templates.py
│   └── ollama_client.py
│
├── 03_rag_pipeline/         # NEW RAG Pipeline (Complete)
│   ├── pdf_extractor.py    # PDF extraction + cleaning
│   ├── chunking.py         # Smart text chunking
│   ├── embeddings.py       # Multilingual embeddings
│   ├── retrieval.py        # FAISS vector search
│   ├── pipeline.py         # Main orchestration
│   ├── indexes/            # Saved FAISS indexes
│   └── requirements.txt    # RAG dependencies
│
└── 02_data/
    └── 01_raw/             # Sample PDFs for indexing
```

---

## 📊 RAG Pipeline (New Implementation)

The RAG pipeline I created includes:

### Components:
1. **PDF Extractor** (`pdf_extractor.py`)
   - PyMuPDF (primary) + PyPDF (fallback)
   - Automatic text cleaning

2. **Text Chunking** (`chunking.py`)
   - 900 character chunks with 150 char overlap
   - Sentence-aware (English + Arabic)

3. **Embeddings** (`embeddings.py`)
   - `paraphrase-multilingual-MiniLM-L12-v2` model
   - 384 dimensions, multilingual

4. **FAISS Retrieval** (`retrieval.py`)
   - Exact L2 distance search
   - Top-k retrieval with similarity scores

5. **Pipeline Orchestration** (`pipeline.py`)
   - End-to-end processing
   - Save/load functionality

### Usage:
```python
from pipeline import RAGPipeline

# Create and build index
pipeline = RAGPipeline()
pipeline.process_org_folder(Path("../02_data/01_raw/depi"))
pipeline.save_index(Path("./indexes/my_index"))

# Query later
pipeline = RAGPipeline.load_index(Path("./indexes/my_index"))
results = pipeline.retrieve("What are the requirements?", k=3)

for doc, score in results:
    print(f"Score: {score:.4f}, Text: {doc['text'][:100]}...")
```

---

## 🔄 API Integration

### Chat Endpoint
```
POST /api/chat
Content-Type: application/json

{
  "message": "What are the requirements?",
  "conversation_id": "optional-id"
}

Response:
{
  "answer": "The requirements are...",
  "sources": [
    {
      "id": "document-name-p1",
      "title": "Document Name",
      "url": "#",
      "organization": "ITI",
      "type": "document",
      "description": "صفحة 1"
    }
  ],
  "suggested_questions": []
}
```

### Health Check
```
GET /health

Response:
{
  "status": "ok"
}
```

---

## 🧪 Testing the RAG Pipeline

Run the end-to-end test:
```bash
cd 03_rag_pipeline
python end_to_end_test.py
```

This will:
1. Test all components
2. Build an index from sample PDFs
3. Test retrieval queries
4. Display statistics

---

## 🛠️ Troubleshooting

### Port Already in Use

**Frontend (5173):**
```bash
cd Frontend
npm run dev -- --port 5174
```

**Backend (8000):**
Edit `06_app/main.py` and change:
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # Change 8000 to 8001
```

### Missing Dependencies

**Python:**
```bash
pip install fastapi uvicorn pydantic pymupdf PyPDF sentence-transformers faiss-cpu numpy pandas langdetect
```

**Node.js:**
```bash
cd Frontend
npm install
```

### Backend Not Responding

1. Check if it's running: `curl http://localhost:8000/health`
2. Check logs in the backend terminal
3. Ensure all Python packages are installed

### Frontend Not Loading

1. Check browser console (F12)
2. Check that backend is running (API calls should work)
3. Try clearing browser cache

---

## 📝 Development Tips

### Frontend Development
- Hot reload enabled (changes auto-reflect)
- Check `Frontend/src/services/chatApi.ts` for API integration
- Tailwind CSS for styling

### Backend Development
- Hot reload enabled with uvicorn
- API docs auto-generated at `/docs`
- Check `06_app/api.py` for endpoints

### RAG Pipeline Development
- Add new PDFs to `02_data/01_raw/*/official/`
- Rebuild index with `pipeline.py`
- Test with `test_components.py`

---

## 📞 Support

### Key Files for Customization

| File | Purpose | Edit For |
|------|---------|----------|
| `06_app/api.py` | API endpoints | Change API behavior |
| `05_generation/generate_answer.py` | RAG + LLM logic | Change answer generation |
| `03_rag_pipeline/pipeline.py` | RAG processing | Change indexing/retrieval |
| `Frontend/src/services/chatApi.ts` | API calls | Change frontend API integration |
| `Frontend/src/components/App.tsx` | Main layout | Change UI layout |

---

## ✨ Features

✅ Multilingual support (English + Arabic)
✅ Smart PDF extraction and cleaning
✅ Context-aware text chunking
✅ Fast semantic search with FAISS
✅ Real-time chat interface
✅ Source attribution
✅ Conversation history
✅ Mobile responsive design

---

## 🎯 Next Steps

1. ✅ Start both servers
2. ✅ Open http://localhost:5173
3. ✅ Ask questions in the chat
4. ✅ View sources for each answer
5. ✅ Explore API docs at http://localhost:8000/docs

**Happy coding! 🚀**
