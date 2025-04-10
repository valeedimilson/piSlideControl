from flask import Flask, request, jsonify,  render_template_string
import secrets
import pyautogui
import ctypes
from datetime import datetime
from waitress import serve
import random
from PIL import ImageGrab

app = Flask(__name__)

class Estado:
    def __init__(self):
        self.token = secrets.token_urlsafe(16)
        self.port = random.randint(1000, 5000)

estado = Estado()
current_token = estado.token 
server_port = estado.port
connected_devices = {}

def randomToken():
    return secrets.token_urlsafe(16)

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
    <meta charset="UTF-8" />
    <meta
      name="viewport"
      content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"
    />
    <title>PiSlideControl</title>
    <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
    <link rel="icon" href="data:," />
    <style>
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        -webkit-tap-highlight-color: transparent;
      }
      a{
        color:#2196f3;
        text-decoration: none;
      }

      body {
        font-family: Arial, sans-serif;
        height: 100dvh;
        display: flex;
        flex-direction: column;
        background-color: #ffecce;
        touch-action: manipulation;
      }

      .title-bar {
        width: 100%;
        height: 60px;
        padding-left: 10px;
        padding-right: 10px;
        background-color: #2196f3;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        z-index: 100;
      }

      .title-text {
        color: white;
        font-size: 1.2em;
        font-weight: bold;
      }

      .social-icons {
        display: flex;
        gap: 15px;
      }

      .social-icon {
        color: white;
        text-decoration: none;
        transition: opacity 0.3s;
      }

      .social-icon:hover {
        opacity: 0.8;
      }

      .social-icon svg {
        width: 24px;
        height: 24px;
      }

      .controls {
        flex: 1;
        display: flex;
        gap: 20px;
        padding-left: 20px;
        padding-right: 20px;
        max-width: 400px;
        flex-direction: column;
        align-items: center;
        width: 100%;
        margin: 0 auto;
      }

      .logo {
        padding-left: 60px;
        padding-top: 10px;
      }

      .buttons {
        padding-top: 60px;
        width: 100%;
        display: flex;
        justify-content: space-between;
      }

      .btn {
        width: 150px;
        height: 200px;
        flex: 1;
        padding: 25px;
        font-size: 5.5em;
        border: none;
        border-radius: 15px;
        background-color: #2196f3;
        color: white;
        cursor: pointer;
        transition: background-color 0.3s;
        user-select: none;
        -webkit-user-select: none;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .btn:active {
        background-color: #1976d2;
      }

      .btn svg {
        width: 1em;
        height: 1em;
        stroke: currentColor;
        fill: currentColor;
      }

      footer {
        text-align: right;
        padding-bottom: 5px;
        padding-right: 10px;
        font-size: 0.9em;
        color: #555;
      }

      @media (orientation: landscape) {
        .controls {
          max-width: 600px;
        }
      }
    </style>
  </head>
  <body>
    <div class="title-bar">
      <div class="title-text">PiSlideControl v1.0.2</div>
      <div class="social-icons">
        <a href="https://www.linkedin.com/in/valeedimilson" class="social-icon">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path
              d="M19 0h-14C2.24 0 0 2.24 0 5v14c0 2.76 2.24 5 5 5h14c2.76 
    0 5-2.24 5-5V5c0-2.76-2.24-5-5-5zM7.12 20H3.56V9h3.56v11zM5.34 
    7.43c-1.14 0-2.07-.94-2.07-2.09s.93-2.09 2.07-2.09 2.07.94 
    2.07 2.09-.93 2.09-2.07 2.09zM20.44 20h-3.56v-5.41c0-1.29-.03-2.95-1.8-2.95-1.8 
    0-2.08 1.4-2.08 2.85V20H9.44V9h3.42v1.5h.05c.48-.9 
    1.66-1.84 3.42-1.84 3.66 0 4.34 2.41 4.34 5.54V20z"
            />
          </svg>
        </a>
        <a href="https://github.com/valeedimilson/piSlideControl" class="social-icon">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path
              d="M12 0C5.37 0 0 5.373 0 12c0 5.303 3.438 9.8 8.207 11.387.6.113.793-.258.793-.577 
    0-.285-.01-1.04-.015-2.04-3.338.726-4.042-1.61-4.042-1.61C4.422 17.07 
    3.633 16.7 3.633 16.7c-1.087-.744.083-.729.083-.729 1.205.085 
    1.84 1.237 1.84 1.237 1.07 1.835 2.809 1.305 3.495.998.108-.776.418-1.305.762-1.605-2.665-.3-5.467-1.335-5.467-5.933 
    0-1.31.468-2.38 1.235-3.22-.124-.303-.535-1.523.117-3.176 
    0 0 1.008-.322 3.3 1.23a11.51 11.51 0 0 1 3.003-.403c1.02.005 
    2.047.137 3.003.403 2.29-1.552 3.297-1.23 3.297-1.23.653 1.653.242 
    2.873.12 3.176.77.84 1.233 1.91 1.233 3.22 0 4.61-2.807 
    5.63-5.48 5.922.43.372.823 1.102.823 2.222 
    0 1.606-.015 2.898-.015 3.293 0 .32.192.694.8.576C20.565 
    21.796 24 17.298 24 12c0-6.627-5.373-12-12-12z"
            />
          </svg>
        </a>
      </div>
    </div>

    <div class="controls">
      <div class="logo">
        <img src="{{ url_for('static', filename='logo.jpg') }}" width="250px" alt="Logo" />
      </div>
      <div class="buttons">
        <div>
          <button class="btn" onclick="previousSlide()">
            <svg viewBox="0 0 24 24">
              <path
                d="M15.41 16.59L10.83 12l4.58-4.59L14 6l-6 6 6 6 1.41-1.41z"
              />
            </svg>
          </button>
        </div>
        <div>
          <button class="btn" onclick="nextSlide()">
            <svg viewBox="0 0 24 24">
              <path
                d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
    <footer>
      By
      <a
        href="https://github.com/valeedimilson/piSlideControl"
        target="_blank">dimi (github.com/valeedimilson)</a
      >
    </footer>

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

      document.addEventListener("gesturestart", (e) => e.preventDefault());
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
