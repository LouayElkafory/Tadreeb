# Quick Start Script for Faiss RAG Pipeline Testing (PowerShell)

Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     🚀 Tadreeb Faiss RAG Pipeline - Quick Start                    ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# Check if Python is installed
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "❌ Python is not installed. Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📦 Step 1: Installing Dependencies..." -ForegroundColor Yellow
Write-Host "────────────────────────────────────────────────────────────────────" -ForegroundColor Gray

pip install -r requirements_faiss.txt -q

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🧪 Step 2: Running Extraction & Chunking Test..." -ForegroundColor Yellow
Write-Host "────────────────────────────────────────────────────────────────────" -ForegroundColor Gray

python faiss_rag_pipeline.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Test completed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Test failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🌐 Step 3: Starting API Server..." -ForegroundColor Yellow
Write-Host "────────────────────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host ""
Write-Host "📍 Access Points:" -ForegroundColor Cyan
Write-Host "   • Swagger Docs: http://localhost:8001/docs" -ForegroundColor White
Write-Host "   • Health Check: http://localhost:8001/health" -ForegroundColor White
Write-Host "   • API Info: http://localhost:8001/api/info" -ForegroundColor White
Write-Host "   • Quick Test: http://localhost:8001/api/test" -ForegroundColor White
Write-Host ""
Write-Host "💬 Chat API:" -ForegroundColor Cyan
Write-Host "   POST http://localhost:8001/api/chat" -ForegroundColor White
Write-Host ""
Write-Host "────────────────────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host ""

python test_api.py
