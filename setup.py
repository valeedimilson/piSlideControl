# setup.py
from PyInstaller.__main__ import run

if __name__ == '__main__':
    opts = [
        'server.py',           # Seu arquivo principal
        '--onefile',           # Cria um único executável
        '--windowed',          # Esconde o console (opcional)
        '--icon=icon.ico',     # Ícone personalizado (opcional)
        '--name=SlideControl'  # Nome do executável
    ]
    run(opts)
