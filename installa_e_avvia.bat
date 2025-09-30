@echo off
echo ========================================
echo   GESTIONALE BICICLETTE v1.0
echo   Installazione e Avvio Automatico
echo   (Funziona Completamente OFFLINE)
echo ========================================
echo.

echo [1/3] Verifico Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRORE: Python non trovato!
    echo Installa Python 3.8+ da https://python.org
    pause
    exit /b 1
)
echo ✓ Python trovato

echo.
echo [2/3] Installo le dipendenze...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERRORE: Installazione dipendenze fallita!
    pause
    exit /b 1
)
echo ✓ Dipendenze installate

echo.
echo [3/3] Avvio il gestionale...
echo.
echo ========================================
echo   AVVIO GESTIONALE BICICLETTE
echo ========================================
echo.
python main.py

echo.
echo Il gestionale è stato chiuso.
pause
