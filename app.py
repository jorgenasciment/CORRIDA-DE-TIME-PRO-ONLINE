"""Entrada compatível para hospedagens como Render."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parent / "server" / "main.py"), run_name="__main__")
