@echo off
REM Setup and run the entire Tadreeb project

setlocal enabledelayedexpansion

echo.
echo ======================================================================
echo   TADREEB PROJECT - COMPLETE SETUP ^& RUN
echo ======================================================================
echo.

set "PROJECT_ROOT=%CD%"
echo Project Root: %PROJECT_ROOT%
echo.

REM ========================================================================
REM STEP 1: Install Python Backend Dependencies
REM ========================================================================
echo.
echo STEP 1: Installing Python Backend Dependencies
echo ==================================================================
echo.

echo Creating requirements_backend.txt...
(
    echo # Core dependencies
    echo fastapi^>=0.104.0
    echo uvicorn[standard]^>=0.24.0
    echo pydantic^>=2.0.0
    echo python-multipart^>=0.0.6
    echo.
    echo # RAG Pipeline
    echo pymupdf^>=1.24.0
    echo PyPDF^>=4.0.0
    echo sentence-transformers^>=3.0.0
    echo faiss-cpu^>=1.8.0
    echo numpy^>=1.24.0
    echo pandas^>=2.0.0
    echo.
    echo # Generation
    echo langdetect^>=1.0.9
    echo ollama^>=0.1.0
) > requirements_backend.txt

echo Installing Python dependencies...
pip install -r requirements_backend.txt -q
if errorlevel 1 (
    echo ⚠️  Some dependencies may have failed. Continuing anyway...
) else (
    echo ✓ Python dependencies installed
)
echo.

REM ========================================================================
REM STEP 2: Install Node.js Frontend Dependencies
REM ========================================================================
echo.
echo STEP 2: Installing Node.js Frontend Dependencies
echo ==================================================================
echo.

if exist "Frontend\package.json" (
    echo Installing Frontend dependencies...
    cd Frontend
    call npm install --loglevel=error
    if errorlevel 1 (
        echo ✗ npm install failed. Make sure Node.js is installed
        cd ..
        pause
        exit /b 1
    )
    echo ✓ Frontend dependencies installed
    cd ..
) else (
    echo ⚠️  Frontend directory not found
)
echo.

REM ========================================================================
REM STEP 3: Display System Information
REM ========================================================================
echo.
echo STEP 3: System Information
echo ==================================================================
echo.

echo Checking Python...
python --version
echo.

echo Checking Node.js...
node --version
echo.

echo Checking npm...
npm --version
echo.

REM ========================================================================
REM STEP 4: Start Servers
REM ========================================================================
echo.
echo ======================================================================
echo   STARTING SERVERS
echo ======================================================================
echo.

echo Starting Backend Server (FastAPI on port 8000)...
echo.
cd 06_app
start "Tadreeb Backend" cmd /k python main.py
cd ..

timeout /t 3 /nobreak

echo.
echo Starting Frontend Server (Vite on port 5173)...
echo.
cd Frontend
start "Tadreeb Frontend" cmd /k npm run dev
cd ..

timeout /t 3 /nobreak

REM ========================================================================
REM STEP 5: Display Access Information
REM ========================================================================
echo.
echo ======================================================================
echo   ✓ PROJECT STARTED SUCCESSFULLY
echo ======================================================================
echo.

echo 📱 ACCESS YOUR APPLICATIONS:
echo.
echo Frontend (React + Vite):
echo   🌐 http://localhost:5173
echo.
echo Backend API (FastAPI):
echo   🔌 http://localhost:8000
echo   📚 Docs: http://localhost:8000/docs
echo   🔄 ReDoc: http://localhost:8000/redoc
echo.

echo Project Structure:
echo   📁 Frontend:        %PROJECT_ROOT%\Frontend
echo   📁 Backend API:     %PROJECT_ROOT%\06_app
echo   📁 RAG Pipeline:    %PROJECT_ROOT%\03_rag_pipeline
echo.

echo Next Steps:
echo   1. Open browser to: http://localhost:5173
echo   2. Ask questions in the chat interface
echo   3. View backend logs in the "Tadreeb Backend" window
echo   4. View frontend logs in the "Tadreeb Frontend" window
echo.

echo To stop the servers, close the server windows or press Ctrl+C
echo.

pause
