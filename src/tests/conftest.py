import sys
import os

# Añadir la carpeta src al inicio de sys.path para permitir imports como `from core...`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
