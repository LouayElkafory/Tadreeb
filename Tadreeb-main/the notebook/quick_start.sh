#!/bin/bash
# Quick Start Script for Faiss RAG Pipeline Testing

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║     🚀 Tadreeb Faiss RAG Pipeline - Quick Start                    ║"
echo "╚════════════════════════════════════════════════════════════════════╝"

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.9+"
    exit 1
fi

echo ""
echo "📦 Step 1: Installing Dependencies..."
echo "────────────────────────────────────────────────────────────────────"
pip install -r requirements_faiss.txt -q

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "🧪 Step 2: Running Extraction & Chunking Test..."
echo "────────────────────────────────────────────────────────────────────"
python faiss_rag_pipeline.py

if [ $? -eq 0 ]; then
    echo "✅ Test completed successfully"
else
    echo "❌ Test failed"
    exit 1
fi

echo ""
echo "🌐 Step 3: Starting API Server..."
echo "────────────────────────────────────────────────────────────────────"
echo ""
echo "📍 Access Points:"
echo "   • Swagger Docs: http://localhost:8001/docs"
echo "   • Health Check: http://localhost:8001/health"
echo "   • API Info: http://localhost:8001/api/info"
echo "   • Quick Test: http://localhost:8001/api/test"
echo ""
echo "💬 Chat API:"
echo "   POST http://localhost:8001/api/chat"
echo ""
echo "────────────────────────────────────────────────────────────────────"
echo ""

python test_api.py
