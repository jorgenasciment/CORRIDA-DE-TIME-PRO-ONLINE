@echo off
cd /d "%~dp0"
title Corrida Times TikTok - MODO ONLINE
echo ===================================================
echo  MODO ONLINE - PAINEL E JOGO EM CELULARES DIFERENTES
echo ===================================================
echo.
echo O PC precisa continuar ligado e conectado a internet.
echo Na primeira vez, o componente online sera baixado automaticamente.
echo Nao feche esta janela durante a live.
echo.
cd /d "%~dp0server"
python iniciar_online.py
pause
