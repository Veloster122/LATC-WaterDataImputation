@echo off
REM Wrapper script to start Streamlit with MKL threading disabled
REM This prevents "Intel MKL ERROR: Parameter 4 was incorrect on entry to DLASCL"

echo ========================================================
echo   Iniciando LATC EcoAnalytics (Web Edition)
echo   com configuracao otimizada MKL
echo ========================================================
echo.

REM Configure MKL and other threading libraries
set MKL_NUM_THREADS=1
set NUMEXPR_NUM_THREADS=1
set OMP_NUM_THREADS=1
set OPENBLAS_NUM_THREADS=1

REM Optional: Disable MKL threading completely
set MKL_THREADING_LAYER=sequential

echo   [OK] Threads configuradas: 1 por processo
echo   [OK] Joblib vai usar multiplos processos sem conflito
echo.
echo   Aguarde enquanto carregamos a interface no seu navegador...
echo.

REM Start Streamlit
streamlit run latc_app.py

pause
