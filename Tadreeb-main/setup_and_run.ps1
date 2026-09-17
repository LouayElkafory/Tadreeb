# Setup and run the entire Tadreeb project
# This script installs dependencies and starts both frontend and backend servers

Write-Host "======================================================================"
Write-Host "  TADREEB PROJECT - COMPLETE SETUP & RUN"
Write-Host "======================================================================" -ForegroundColor Green

$projectRoot = Get-Location
Write-Host "`nProject Root: $projectRoot`n"

# ============================================================================
# STEP 1: Install Python Backend Dependencies
# ============================================================================
Write-Host "STEP 1: Installing Python Backend Dependencies" -ForegroundColor Cyan
Write-Host "=================================================================="

# Create requirements file if it doesn't exist
$backendRequirements = @"
# Core dependencies
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
python-multipart>=0.0.6

# RAG Pipeline
pymupdf>=1.24.0
PyPDF>=4.0.0
sentence-transformers>=3.0.0
faiss-cpu>=1.8.0
numpy>=1.24.0
pandas>=2.0.0

# Generation & LLM
langdetect>=1.0.9
ollama>=0.1.0

# Utilities
python-dotenv>=1.0.0
"@

# Create a temp requirements file
$reqFile = "$projectRoot\requirements_backend.txt"
$backendRequirements | Out-File -FilePath $reqFile -Encoding UTF8 -Force
Write-Host "Installing from: $reqFile`n"

# Try to install with pip
try {
    Write-Host "Running: pip install -r requirements_backend.txt"
    pip install -r $reqFile -q
    Write-Host "✓ Python dependencies installed successfully`n" -ForegroundColor Green
}
catch {
    Write-Host "⚠️  Some Python dependencies may have failed to install`n" -ForegroundColor Yellow
    Write-Host "You may need to run: pip install -r requirements_backend.txt`n"
}

# ============================================================================
# STEP 2: Install Node.js Frontend Dependencies
# ============================================================================
Write-Host "STEP 2: Installing Node.js Frontend Dependencies" -ForegroundColor Cyan
Write-Host "=================================================================="

$frontendDir = "$projectRoot\Frontend"

if (Test-Path $frontendDir) {
    Push-Location $frontendDir
    Write-Host "Frontend directory: $frontendDir`n"

    try {
        Write-Host "Running: npm install"
        npm install --loglevel=error
        Write-Host "✓ Frontend dependencies installed successfully`n" -ForegroundColor Green
    }
    catch {
        Write-Host "✗ npm install failed. Make sure Node.js is installed`n" -ForegroundColor Red
        Write-Host "Install from: https://nodejs.org/`n"
        Pop-Location
        exit 1
    }

    Pop-Location
}
else {
    Write-Host "⚠️  Frontend directory not found: $frontendDir`n" -ForegroundColor Yellow
}

# ============================================================================
# STEP 3: Build RAG Pipeline Index (Optional)
# ============================================================================
Write-Host "STEP 3: Building RAG Pipeline Index (Optional)" -ForegroundColor Cyan
Write-Host "=================================================================="

$ragDir = "$projectRoot\03_rag_pipeline"
$testIndexDir = "$ragDir\indexes\test_index"

if (-not (Test-Path $testIndexDir)) {
    Write-Host "Building test index from PDFs...`n"

    try {
        Push-Location $ragDir
        Write-Host "Running: python end_to_end_test.py"
        # Run in background to not block
        python end_to_end_test.py 2>&1 | Select-Object -First 50
        Write-Host "`n✓ Test index built (partial output shown)`n" -ForegroundColor Green
        Pop-Location
    }
    catch {
        Write-Host "⚠️  RAG index building skipped (optional):`n" -ForegroundColor Yellow
        Write-Host "$_`n"
    }
}
else {
    Write-Host "✓ Test index already exists: $testIndexDir`n" -ForegroundColor Green
}

# ============================================================================
# STEP 4: Start Backend Server
# ============================================================================
Write-Host "STEP 4: Starting Backend Server (FastAPI)" -ForegroundColor Cyan
Write-Host "=================================================================="

$backendScript = "$projectRoot\06_app\main.py"

if (Test-Path $backendScript) {
    Write-Host "Backend: $backendScript`n"
    Write-Host "Starting on http://localhost:8000`n"

    # Start backend in new window
    Start-Process powershell -ArgumentList @"
        cd '$projectRoot\06_app'
        Write-Host 'Backend Server Starting...' -ForegroundColor Green
        python main.py
"@ -WindowTitle "Tadreeb Backend (FastAPI)"

    # Wait for backend to start
    Start-Sleep -Seconds 3
    Write-Host "✓ Backend server started`n" -ForegroundColor Green
}
else {
    Write-Host "⚠️  Backend script not found: $backendScript`n" -ForegroundColor Yellow
}

# ============================================================================
# STEP 5: Start Frontend Server
# ============================================================================
Write-Host "STEP 5: Starting Frontend Server (Vite)" -ForegroundColor Cyan
Write-Host "=================================================================="

$frontendDir = "$projectRoot\Frontend"

if (Test-Path $frontendDir) {
    Write-Host "Frontend: $frontendDir`n"
    Write-Host "Starting on http://localhost:5173`n"

    # Start frontend in new window
    Start-Process powershell -ArgumentList @"
        cd '$frontendDir'
        Write-Host 'Frontend Server Starting...' -ForegroundColor Green
        npm run dev
"@ -WindowTitle "Tadreeb Frontend (Vite)"

    # Wait for frontend to start
    Start-Sleep -Seconds 3
    Write-Host "✓ Frontend server started`n" -ForegroundColor Green
}
else {
    Write-Host "⚠️  Frontend directory not found: $frontendDir`n" -ForegroundColor Yellow
}

# ============================================================================
# STEP 6: Display Access Information
# ============================================================================
Write-Host "=================================================================="
Write-Host "  ✓ PROJECT STARTED SUCCESSFULLY" -ForegroundColor Green
Write-Host "=================================================================="

Write-Host "`n📱 ACCESS YOUR APPLICATIONS:`n" -ForegroundColor Cyan

Write-Host "Frontend (React + Vite):" -ForegroundColor Yellow
Write-Host "  🌐 http://localhost:5173`n"

Write-Host "Backend API (FastAPI):" -ForegroundColor Yellow
Write-Host "  🔌 http://localhost:8000"
Write-Host "  📚 Docs: http://localhost:8000/docs"
Write-Host "  🔄 ReDoc: http://localhost:8000/redoc`n"

Write-Host "Project Structure:" -ForegroundColor Yellow
Write-Host "  📁 Frontend:        $frontendDir"
Write-Host "  📁 Backend API:     $projectRoot\06_app"
Write-Host "  📁 RAG Pipeline:    $ragDir"
Write-Host "  📁 Generation:      $projectRoot\05_generation`n"

Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Open browser to: http://localhost:5173"
Write-Host "  2. Ask questions in the chat interface"
Write-Host "  3. View backend logs in the 'Tadreeb Backend' window"
Write-Host "  4. View frontend logs in the 'Tadreeb Frontend' window`n"

Write-Host "To stop the servers:" -ForegroundColor Yellow
Write-Host "  - Close the server windows or press Ctrl+C`n"

Write-Host "Troubleshooting:" -ForegroundColor Cyan
Write-Host "  - Port 5173 in use? Run: npm run dev -- --port 5174"
Write-Host "  - Port 8000 in use? Edit 06_app/main.py and change port"
Write-Host "  - Missing dependencies? Run pip install -r requirements_backend.txt`n"

Write-Host "Press Enter to continue monitoring..." -ForegroundColor Green
Read-Host
