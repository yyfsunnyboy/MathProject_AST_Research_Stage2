@echo off
echo ==========================================
echo Ollama Service Restart Script
echo ==========================================

echo [1/3] Killing existing Ollama processes...
taskkill /F /IM ollama.exe 2>nul
taskkill /F /IM ollama_app.exe 2>nul
timeout /t 3 /nobreak >nul

echo [2/3] Clearing VRAM cache...
echo (Waiting 5 seconds for GPU memory release)
timeout /t 5 /nobreak >nul

echo [3/3] Starting Ollama service...
start "" "C:\Users\%USERNAME%\AppData\Local\Programs\Ollama\ollama app.exe"
timeout /t 3 /nobreak >nul

echo ==========================================
echo Ollama restarted successfully!
echo Wait 10 seconds before running experiments
echo ==========================================
timeout /t 10 /nobreak