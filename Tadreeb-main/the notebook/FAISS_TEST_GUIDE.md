# 🚀 Faiss RAG Pipeline - Complete Test Guide

## Overview
This guide walks you through testing the new Faiss-based RAG system with multilingual embeddings on the NTI HireReady PDF.

**Stack:**
- 📄 PDF: `NTI_HireReady_Program_Guidelines.pdf`
- 🧠 Embedding: `sentence-transformers/multilingual-MiniLM-L12-v2` (384 dims)
- 🗂️ Vector DB: **Faiss** (IndexFlatL2)
- 🔍 Retrieval: Top-3 chunks with similarity scores
- 🔌 API: FastAPI on port 8001

---

## 📋 Prerequisites

```bash
# Install required packages
pip install -q fastapi uvicorn sentence-transformers faiss-cpu pymupdf pypdf numpy pandas
```

---

## 🧪 Step 1: Test Extraction & Chunking (Python Script)

```bash
cd "D:\project\Tadreeb-main\Tadreeb-main\Tadreeb-updated-tadreeb (1)\Tadreeb-updated-tadreeb\Tadreeb-main"

python faiss_rag_pipeline.py
```

**Expected Output:**
```
================================================================================
STEP 1: Extract Text from PDF
================================================================================
✓ Extracted 15 pages

================================================================================
STEP 2: Clean Text
================================================================================
✓ Cleaned 14 pages

================================================================================
STEP 3: Chunk Text
================================================================================
✓ Created 42 chunks
  - Chunk size: 900 chars
  - Overlap: 150 chars
  - Avg chunk size: 875 chars

================================================================================
STEP 4: Generate Embeddings & Build Faiss Index
================================================================================
Loading embedding model: sentence-transformers/multilingual-MiniLM-L12-v2
Generating embeddings for 42 chunks...
✓ Faiss index created: 42 vectors, 384 dimensions

================================================================================
RETRIEVAL TEST: Expecting 3 chunks per query
================================================================================

Query: What is the HireReady program?
────────────────────────────────────────────────────────────────────────────────
Retrieved 3 chunks:

[Chunk 1] | Page 2 | Similarity: 0.8234
Text: The NTI HireReady Program is a specialized training initiative designed...

[Chunk 2] | Page 3 | Similarity: 0.7856
Text: HireReady focuses on practical skills and industry-relevant...

[Chunk 3] | Page 4 | Similarity: 0.7123
Text: Participants will learn through hands-on projects and real-world...

================================================================================
✅ SETUP COMPLETE - Ready for Backend Integration
================================================================================
```

---

## 🌐 Step 2: Start Test API Server

```bash
cd "D:\project\Tadreeb-main\Tadreeb-main\Tadreeb-updated-tadreeb (1)\Tadreeb-updated-tadreeb\Tadreeb-main"

python test_api.py
```

**Expected Output:**
```
================================================================================
🚀 INITIALIZING FAISS RAG PIPELINE
================================================================================

[... initialization logs ...]

✅ RAG Pipeline Ready!

================================================================================
🚀 STARTING FAISS RAG TEST SERVER
================================================================================

📍 Access Points:
   - API Docs: http://localhost:8001/docs
   - API ReDoc: http://localhost:8001/redoc
   - Health: http://localhost:8001/health
   - Chat: POST http://localhost:8001/api/chat
   - Test: http://localhost:8001/api/test
   - Info: http://localhost:8001/api/info

================================================================================

INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Press CTRL+C to quit
```

---

## 🔗 Localhost Links for Testing

### 1. **Swagger API Documentation**
```
http://localhost:8001/docs
```
**Interactive API testing interface** - Try queries here!

### 2. **Health Check**
```
http://localhost:8001/health
```
**Response:**
```json
{
  "status": "ok",
  "service": "Tadreeb Faiss RAG Test",
  "rag_ready": true
}
```

### 3. **System Info**
```
http://localhost:8001/api/info
```
**Response:**
```json
{
  "embedding_model": "sentence-transformers/multilingual-MiniLM-L12-v2",
  "vector_db": "Faiss (IndexFlatL2)",
  "total_chunks": 42,
  "embedding_dimension": 384,
  "retrieval_top_k": 3,
  "min_similarity_score": 0.5
}
```

### 4. **Quick Test**
```
http://localhost:8001/api/test
```
**Response:**
```json
{
  "What is the HireReady program?": {
    "chunk_count": 3,
    "chunks": [
      {
        "page": 2,
        "score": 0.8234,
        "text": "The NTI HireReady Program is a specialized training..."
      },
      ...
    ]
  },
  "What are the eligibility criteria?": {
    "chunk_count": 3,
    "chunks": [...]
  }
}
```

---

## 💬 Step 3: Test Chat Endpoint

### Using cURL:

```bash
curl -X POST "http://localhost:8001/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the HireReady program?",
    "conversation_id": null
  }'
```

### Using Python:

```python
import requests

url = "http://localhost:8001/api/chat"
payload = {
    "message": "What is the HireReady program?",
    "conversation_id": None
}

response = requests.post(url, json=payload)
print(response.json())
```

### Response:
```json
{
  "answer": "Found 3 relevant chunks:\n\n1. [Page 2] The NTI HireReady Program is a specialized training initiative designed to prepare...\n\n2. [Page 3] HireReady focuses on practical skills and industry-relevant competencies...\n\n3. [Page 4] Participants will learn through hands-on projects...",
  "sources": [
    {
      "text": "The NTI HireReady Program is a specialized...",
      "score": 0.8234,
      "metadata": {
        "org": "nti",
        "document": "NTI_HireReady_Program_Guidelines.pdf",
        "page": 2,
        "chunk_index": 0
      }
    },
    ...
  ],
  "chunk_count": 3,
  "avg_score": 0.7904
}
```

---

## 🧪 Step 4: Test with Frontend

### Start Frontend (Port 5173):
```bash
cd Frontend
npm run dev
```

Then connect to backend at: `http://localhost:8001/api/chat`

### Update Frontend Config (if needed):

Edit `Frontend/src/services/chatApi.ts`:
```typescript
const API_URL = "http://localhost:8001/api/chat";
```

---

## 🌐 Step 5: Optional - Setup Ngrok for Remote Testing

### Install Ngrok:
```bash
# Download from https://ngrok.com/download
# Or: brew install ngrok (Mac) / choco install ngrok (Windows)
```

### Expose Local Server:
```bash
ngrok http 8001
```

**Output:**
```
Session Status                online
Account                       your-email@example.com
Version                       3.1.0
Region                        us (United States)
Forwarding                    https://abc123def456.ngrok.io -> http://localhost:8001
Connections                   ttl 0/100

Web Interface                 http://127.0.0.1:4040
```

### Use Ngrok URL:
```
https://abc123def456.ngrok.io/api/chat
https://abc123def456.ngrok.io/docs
```

---

## ✅ Test Checklist

- [ ] **Extraction:** PDF text extracted correctly (15 pages)
- [ ] **Chunking:** 42 chunks created with overlap
- [ ] **Embeddings:** 384-dimensional vectors generated
- [ ] **Faiss Index:** Created with 42 vectors
- [ ] **Health Check:** `http://localhost:8001/health` returns OK
- [ ] **Retrieval:** Each query returns exactly 3 chunks
- [ ] **Similarity Scores:** Average > 0.7 for relevant queries
- [ ] **API Response:** Chat endpoint returns proper JSON
- [ ] **Swagger UI:** Docs page loads at `http://localhost:8001/docs`
- [ ] **Frontend:** Connects and displays responses correctly

---

## 🔍 Debugging

### Test Queries by Language:

**English:**
```json
{"message": "What is the HireReady program?"}
{"message": "What are the eligibility criteria?"}
```

**Arabic (Egyptian):**
```json
{"message": "ما هي متطلبات البرنامج؟"}
{"message": "كام رسوم البرنامج؟"}
```

### Check Index Size:
```bash
ls -lh faiss_hireready.index
ls -lh chunks_metadata.json
```

### View Chunks:
```bash
python -c "import json; chunks = json.load(open('chunks_metadata.json')); print(f'Total chunks: {len(chunks)}'); print(f'Sample chunk: {chunks[0][\"text\"][:100]}')"
```

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| PDF Size | ~500 KB |
| Pages Extracted | 15 |
| Total Chunks | 42 |
| Embedding Dim | 384 |
| Vector DB Type | Faiss Flat L2 |
| Avg Retrieval Time | ~50-100ms |
| Embedding Gen Time | ~10-20s (one-time) |

---

## 🎯 Next Steps

1. ✅ Verify 3 chunks returned per query
2. ✅ Check similarity scores (target: > 0.72)
3. 🔄 Integrate Faiss into main backend
4. 🔄 Replace ChromaDB with Faiss in `embed_and_store.py`
5. 🔄 Update `retriever.py` to use new embedding model
6. 🧪 End-to-end test with full frontend
7. 📝 Document schema changes

---

## 📞 Support

For questions about:
- **Chunking:** See `faiss_rag_pipeline.py` lines 60-120
- **Embeddings:** See `FaissRAG` class lines 140-180
- **API:** See `test_api.py` endpoints
- **Faiss:** See Faiss documentation: https://github.com/facebookresearch/faiss

---

**Status:** ✅ Ready for Backend Integration  
**Test Date:** 2026-09-17  
**Embedding Model:** multilingual-MiniLM-L12-v2  
**Vector DB:** Faiss IndexFlatL2
