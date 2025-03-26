@echo off
:: Build Script para SlideControl - Instala dependências automaticamente
set PYTHON_PATH="C:\Program Files\Python313\python.exe"
set SCRIPT_PATH="server.py"

echo [1/4] Verificando ícone...
if not exist "icon.ico" (
    echo ! AVISO: Criando ícone vazio (substitua por um .ico real depois)
    fsutil file createnew icon.ico 0 > nul
)

echo [2/4] Instalando dependências...
%PYTHON_PATH% -m pip install --upgrade pip
%PYTHON_PATH% -m pip install pyinstaller Flask qrcode pyautogui pynput pillow

echo [3/4] Construindo executável...
%PYTHON_PATH% -m PyInstaller --onefile --windowed --icon=icon.ico --name SlideControl %SCRIPT_PATH%

echo [4/4] Verificando resultado...
if exist "dist\SlideControl.exe" (
    echo ----------------------------------------
    echo BUILD SUCESSO!
    echo Executável criado em: dist\SlideControl.exe
    echo ----------------------------------------
) else (
    echo ----------------------------------------
    echo ERRO: Falha na compilação
    echo Verifique as mensagens acima
    echo ----------------------------------------
)

pause