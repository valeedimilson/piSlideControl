from flask import Flask, request, jsonify,  render_template_string
import secrets
import pyautogui
import ctypes
from datetime import datetime
from waitress import serve
import random
import pytesseract
from PIL import ImageGrab

app = Flask(__name__)

class Estado:
    def __init__(self):
        self.token = "123456" #secrets.token_urlsafe(16)
        self.port = 1000 #random.randint(1000, 5000)

estado = Estado()
current_token = estado.token 
server_port = estado.port
connected_devices = {}

def randomToken():
    return "123456" #secrets.token_urlsafe(16)

def update_token():
    """Atualiza o token atual e retorna o novo valor."""
    global current_token
    estado.token = randomToken()
    current_token = estado.token
    return current_token

def get_current_token():
    """Retorna o token atual."""
    return current_token

def send_key(key):
    try:       
        pyautogui.press(key)
        return True
    except Exception as e:
        print(f"Erro ao enviar tecla: {e}")
        return False
    

def detect_text_on_screen():
    """Captura a tela e usa OCR para identificar texto relevante."""
    screenshot = ImageGrab.grab()  # Captura a tela inteira
    text = pytesseract.image_to_string(screenshot, lang="por")
    print(text)
    return text.lower()

def isCanvaActive():
    """Verifica se a palavra 'Canva' aparece na tela."""
    screen_text = detect_text_on_screen()
    return "Compartilhar" in screen_text

def isBrowser(title):
    browsers = ["google chrome", "mozilla firefox", "microsoft edge", "chrome", "firefox", "edge"]
    title_lower = title.lower()
    for browser in browsers:
        if browser in title_lower:
            return True
    return False

def isSoftware(software, title):
    title_lower = title.lower()
    if software in title_lower:
        return True
    return False

def getWindowTitle():
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)

    return buffer.value


@app.route('/')
def control():
    token = request.args.get('token') 
    if token != get_current_token():  # Usa a função para obter o token atual
        return "Token inválido ou expirado!", 403
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <link rel="icon" type="image/x-icon" href="{{ url_for('static', filename='favicon.ico') }}">

            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>piSlideControl - dimi(github.com/valeedimilson)</title>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    touch-action: manipulation;
                }
                .control-container {
                    position: fixed;
                    bottom: 0px;
                    display: flex;
                    flex-direction: column;
                    height: 50dvh;
                    width: 100dvw;
                }
                .btn-row {
                    display: flex;
                    flex: 1;
                }
                .btn {
                    flex: 1;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 24px;
                    background: #2196F3;
                    color: white;
                    border: none;
                    margin: 5px;
                    border-radius: 10px;
                    cursor: pointer;
                    user-select: none;
                    -webkit-tap-highlight-color: transparent;
                }
                .btn:active {
                    background: #0b7dda;
                    transform: scale(0.98);
                }
                .btn-full {
                    flex-basis: 100%;
                }
                .btn-prev {
                    background: #4CAF50;
                }
                .btn-next {
                    background: #2196F3;
                }
                .btn-fs {
                    background: #FF9800;
                }
                .btn-exit {
                    background: #f44336;
                }
            </style>
        </head>
        <body>
            <div class="control-container">
                <div class="btn-row" style="display:none">
                    <button class="btn btn-fs" onclick="fullscreen()">Slide em Tela Cheia</button>
                    <button class="btn btn-exit" onclick="exitFullscreen2()">Sair Tela Cheia</button>
                </div>
                <div class="btn-row">
                    <button class="btn btn-prev" onclick="previousSlide()">← Anterior</button>
                    <button class="btn btn-next" onclick='nextSlide()'>Próximo →</button>
                </div>
            </div>
            <script>
                const token = new URLSearchParams(window.location.search).get('token');
                
                
                function handleResponse(response) {
                    if (!response.ok) throw new Error('Erro na comunicação');
                    return response.json();
                }
                
                function nextSlide() {
                    fetch(`/next?token=${token}`, { method: 'POST' })
                        .then(handleResponse)
                        .catch(err => alert('Erro: ' + err));
                }
                
                function previousSlide() {
                    fetch(`/previous?token=${token}`, { method: 'POST' })
                        .then(handleResponse)
                        .catch(err => alert('Erro: ' + err));
                }
                
                function fullscreen() {
                    fetch(`/fullscreen?token=${token}`, { method: 'POST' })
                        .then(handleResponse)
                        .catch(err => alert('Erro: ' + err));
                }
                
                function exitFullscreen2() {
                    fetch(`/exit-fullscreen?token=${token}`, { method: 'POST' })
                        .then(handleResponse)
                        .catch(err => alert('Erro: ' + err));
                }
                
            </script>
        </body>
        </html>
    ''', now=datetime.now())


@app.route('/next', methods=['POST'])
def next_slide():    
    token = request.args.get('token')
    if token != get_current_token():  # Usa a função para obter o token atual
        return jsonify(success=False, error="Token inválido"), 403
    success = send_key('right') or send_key('space')
    return jsonify(success=success)


@app.route('/previous', methods=['POST'])
def previous_slide():    
    token = request.args.get('token')
    if token != get_current_token():  # Usa a função para obter o token atual
        return jsonify(success=False, error="Token inválido"), 403
    success = send_key('left')
    return jsonify(success=success)


@app.route('/fullscreen', methods=['POST'])
def fullscreen():    
    token = request.args.get('token')
    if token != get_current_token():  # Usa a função para obter o token atual
        return jsonify(success=False, error="Token inválido"), 403      

    try:        
        
        if(isBrowser(getWindowTitle())):
           
            if(isSoftware("apresentações google", getWindowTitle())):
                pyautogui.hotkey("ctrl","f5")
                return jsonify(success=True)
            
            pyautogui.press('f11')
            return jsonify(success=True)
        
        if(not isBrowser(getWindowTitle())):
            pyautogui.press('f5')
            return jsonify(success=True)
        
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@app.route('/exit-fullscreen', methods=['POST'])
def exit_fullscreen():    
    token = request.args.get('token')
    if token != get_current_token():  # Usa a função para obter o token atual
        return jsonify(success=False, error="Token inválido"), 403
    try:
        if(isBrowser(getWindowTitle())):            
            pyautogui.press('esc')
            return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


def run_server():
    serve(app, host="0.0.0.0", port=server_port)


if __name__ == "__main__":
    run_server()
