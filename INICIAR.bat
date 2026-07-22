@echo off
cd /d "%~dp0"
title Corrida Times TikTok - INICIAR
echo Iniciando servidor. O painel fica no PC e o jogo abre no celular...
start "Servidor Corrida Times" /min cmd /c "cd /d ""%~dp0server"" && iniciar.bat"
timeout /t 5 /nobreak >nul
start "Painel Corrida Times" http://127.0.0.1:8787/painel
exit
