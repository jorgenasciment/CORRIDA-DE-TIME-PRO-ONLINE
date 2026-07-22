@echo off
cd /d "%~dp0"
title Servidor Corrida Times TikTok
echo Instalando/verificando dependencias...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Python nao respondeu como "python". Tentando com "py"...
  py -m pip install -r requirements.txt
  py main.py
  pause
  exit /b
)
cls
python main.py
pause
