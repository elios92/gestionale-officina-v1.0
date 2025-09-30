@echo off
echo ========================================
echo   GESTIONALE BICICLETTE v1.0
echo   Avvio Rapido (OFFLINE)
echo ========================================
echo.

echo Verifico Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRORE: Python non trovato!
    echo Esegui prima "installa_e_avvia.bat"
    pause
    exit /b 1
)

echo Avvio il gestionale...
echo.
python main.py

echo.
echo Il gestionale è stato chiuso.
pause
