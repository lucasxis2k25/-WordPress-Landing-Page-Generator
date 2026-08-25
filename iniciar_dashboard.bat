@echo off
title Demo Store - Dashboard B2B
echo ============================================================
echo   Demo Store - DASHBOARD DE ORQUESTRAÇÃO B2B (REDE LOCAL)
echo ============================================================
echo.
echo URL para acesso via Cabo de Rede / LAN:
echo -> http://192.168.1.100:8501
echo.
echo URL para acesso neste computador:
echo -> http://localhost:8501
echo.
echo Pressione Ctrl+C para encerrar o servidor.
echo ============================================================
echo.
python -m streamlit run dashboard.py --server.address 0.0.0.0 --server.port 8501
pause
