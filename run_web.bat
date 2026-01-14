@echo off
echo ========================================================
echo   Iniciando LATC EcoAnalytics (Web Edition)
echo ========================================================
echo.
echo   Aguarde enquanto carregamos a interface no seu navegador...
echo.

cd /d "%~dp0"
streamlit run latc_app.py --server.maxUploadSize=2000

pause
