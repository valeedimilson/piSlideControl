from flask import Flask, request, jsonify, send_file, render_template_string, redirect, url_for
import secrets
import qrcode
import io
import platform
import pyautogui
import time
import webbrowser
import socket
import threading
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
current_token = secrets.token_urlsafe(16)
server_port = 5000

# Estruturas de dados
connected_devices = {}  # {ip: {'connection_time': datetime, 'last_active': datetime}}
blocked_ips = set()    # IPs bloqueados

# Configuração cross-platform
if platform.system() == 'Darwin':
    from pynput.keyboard import Controller
    keyboard = Controller()
else:
    keyboard = None


def send_key(key):
    try:
        if keyboard:
            with keyboard.pressed(key):
                time.sleep(0.1)
        else:
            pyautogui.press(key)
        return True
    except Exception as e:
        print(f"Erro ao enviar tecla: {e}")
        return False


def update_device_activity(ip):
    now = datetime.now()
    if ip not in connected_devices:
        connected_devices[ip] = {
            'connection_time': now,
            'last_active': now
        }
    else:
        connected_devices[ip]['last_active'] = now


@app.route('/')
def admin():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Servidor de Controle</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { 
                    display: flex; 
                    flex-direction: column; 
                    align-items: center; 
                    gap: 15px; 
                    padding: 15px;
                    font-family: Arial, sans-serif;
                }
                .panel {
                    width: 100%;
                    max-width: 500px;
                    background: #f5f5f5;
                    border-radius: 10px;
                    padding: 15px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                h2 {
                    color: #333;
                    text-align: center;
                }
                img.qrcode {
                    width: 200px;
                    height: 200px;
                    margin: 0 auto;
                    display: block;
                }
                button {
                    padding: 12px 20px;
                    font-size: 16px;
                    background: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    width: 100%;
                    margin: 5px 0;
                }
                button.danger {
                    background: #f44336;
                }
                button.success {
                    background: #4CAF50;
                }
                .device-list, .blocked-list {
                    width: 100%;
                    margin: 15px 0;
                }
                .device-card, .blocked-card {
                    background: white;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 5px 0;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .toggle-section {
                    margin: 15px 0;
                }
                .toggle-btn {
                    padding: 8px 12px;
                    background: #ddd;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                }
                .hidden {
                    display: none;
                }
                @media (max-width: 600px) {
                    .panel {
                        width: 95%;
                    }
                }
            </style>
        </head>
        <body>
            <div class="panel">
                <h2>Controle de Apresentação</h2>
                
                <div class="qrcode-container">
                    <img src="{{ url_for('generate_qrcode') }}" class="qrcode" alt="QR Code">
                    <p style="text-align: center;">{{ control_url }}</p>
                </div>
                
                <button onclick="generateNewToken()" class="danger">Gerar Novo QR Code</button>
                
                <div class="toggle-section">
                    <button class="toggle-btn" onclick="toggleSection('devices')">Dispositivos Conectados ▼</button>
                    <div id="devices-section" class="hidden">
                        <div class="device-list" id="device-list">
                            <!-- Dispositivos serão carregados aqui -->
                        </div>
                    </div>
                </div>
                
                <div class="toggle-section">
                    <button class="toggle-btn" onclick="toggleSection('blocked')">IPs Bloqueados ▼</button>
                    <div id="blocked-section" class="hidden">
                        <div class="blocked-list" id="blocked-list">
                            <!-- IPs bloqueados serão carregados aqui -->
                        </div>
                        <input type="text" id="ip-to-block" placeholder="Digite um IP para bloquear" style="width: 100%; padding: 8px; margin: 5px 0;">
                        <button onclick="blockIp()" class="danger">Bloquear IP</button>
                    </div>
                </div>
            </div>

            <script>
                const controlUrl = "http://{{ request.host }}/control?token={{ current_token }}";
                
                function toggleSection(section) {
                    const elem = document.getElementById(`${section}-section`);
                    elem.classList.toggle('hidden');
                }
                
                function generateNewToken() {
                    fetch('/generate-token', { method: 'POST' })
                        .then(() => window.location.reload())
                        .catch(err => alert('Erro: ' + err));
                }
                
                function disconnectDevice(ip) {
                    fetch(`/disconnect?ip=${encodeURIComponent(ip)}`, { method: 'POST' })
                        .then(() => loadDevices())
                        .catch(err => alert('Erro: ' + err));
                }
                
                function blockIp() {
                    const ip = document.getElementById('ip-to-block').value;
                    if (!ip) return;
                    
                    fetch(`/block-ip?ip=${encodeURIComponent(ip)}`, { method: 'POST' })
                        .then(() => {
                            loadBlockedIps();
                            document.getElementById('ip-to-block').value = '';
                        })
                        .catch(err => alert('Erro: ' + err));
                }
                
                function unblockIp(ip) {
                    fetch(`/unblock-ip?ip=${encodeURIComponent(ip)}`, { method: 'POST' })
                        .then(() => loadBlockedIps())
                        .catch(err => alert('Erro: ' + err));
                }
                
                function formatDate(dateStr) {
                    if (!dateStr) return 'N/A';
                    const date = new Date(dateStr);
                    return date.toLocaleString();
                }
                
                function loadDevices() {
                    fetch('/connected-devices')
                        .then(res => res.json())
                        .then(data => {
                            const container = document.getElementById('device-list');
                            container.innerHTML = '';
                            
                            if (Object.keys(data).length === 0) {
                                container.innerHTML = '<p>Nenhum dispositivo conectado</p>';
                                return;
                            }
                            
                            for (const [ip, info] of Object.entries(data)) {
                                const card = document.createElement('div');
                                card.className = 'device-card';
                                
                                const isActive = (new Date() - new Date(info.last_active)) < 300000; // 5 minutos
                                const activeText = isActive ? '🟢 Online' : '🔴 Offline';
                                
                                card.innerHTML = `
                                    <div>
                                        <strong>${ip}</strong><br>
                                        Conectado em: ${formatDate(info.connection_time)}<br>
                                        Última atividade: ${formatDate(info.last_active)}<br>
                                        Status: ${activeText}
                                    </div>
                                    <button onclick="disconnectDevice('${ip}')" class="danger">Desconectar</button>
                                `;
                                container.appendChild(card);
                            }
                        })
                        .catch(err => console.error('Erro ao carregar dispositivos:', err));
                }
                
                function loadBlockedIps() {
                    fetch('/blocked-ips')
                        .then(res => res.json())
                        .then(data => {
                            const container = document.getElementById('blocked-list');
                            container.innerHTML = '';
                            
                            if (data.length === 0) {
                                container.innerHTML = '<p>Nenhum IP bloqueado</p>';
                                return;
                            }
                            
                            for (const ip of data) {
                                const card = document.createElement('div');
                                card.className = 'blocked-card';
                                card.innerHTML = `
                                    <span>${ip}</span>
                                    <button onclick="unblockIp('${ip}')" class="success">Desbloquear</button>
                                `;
                                container.appendChild(card);
                            }
                        })
                        .catch(err => console.error('Erro ao carregar IPs bloqueados:', err));
                }
                
                // Atualiza a cada 10 segundos
                setInterval(() => {
                    loadDevices();
                    loadBlockedIps();
                }, 10000);
                
                // Carrega inicialmente
                loadDevices();
                loadBlockedIps();
            </script>
        </body>
        </html>
    ''', control_url=f"http://{request.host}/control?token={current_token}")


@app.route('/control')
def control():
    token = request.args.get('token')
    ip = request.remote_addr

    if token != current_token:
        return "Token inválido ou expirado!", 403
    if ip in blocked_ips:
        return "Seu IP está bloqueado!", 403

    update_device_activity(ip)
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Controle de Slides</title>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    touch-action: manipulation;
                }
                .control-container {
                    display: flex;
                    flex-direction: column;
                    height: 100dvh;
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
                
                <div class="btn-row">
                    <button class="btn btn-fs" onclick="fullscreen()">Tela Cheia (F5)</button>
                    <button class="btn btn-exit" onclick="exitFullscreen2()">Sair (ESC)</button>
                </div>
                                  <div class="btn-row">
                    <button class="btn btn-prev" onclick="previousSlide()">← Anterior</button>
                    <button class="btn btn-next" onclick="nextSlide()">Próximo →</button>
                </div>
            </div>
            <script>
                const token = new URLSearchParams(window.location.search).get('token');
                
                function ping() {
                    fetch(`/ping?token=${token}`, { method: 'POST' })
                        .catch(err => console.log('Ping error:', err));
                }
                
                // Envia ping a cada 30 segundos
                setInterval(ping, 30000);
                
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
                
                // Atualiza status a cada segundo
                setInterval(() => {
                    const now = new Date();
                    document.getElementById('status').innerText = 
                        `Conectado em: ${now.toLocaleTimeString()}`;
                }, 1000);
            </script>
        </body>
        </html>
    ''', now=datetime.now())

# API Endpoints


@app.route('/generate-token', methods=['POST'])
def generate_new_token():
    global current_token
    current_token = secrets.token_urlsafe(16)
    connected_devices.clear()
    return jsonify(success=True)


@app.route('/connected-devices')
def get_connected_devices():
    # Remove dispositivos inativos (última atividade > 5 minutos)
    inactive_threshold = datetime.now().timestamp() - 300
    to_remove = []

    for ip, info in connected_devices.items():
        last_active = info['last_active'].timestamp() if hasattr(
            info['last_active'], 'timestamp') else datetime.fromisoformat(info['last_active']).timestamp()
        if last_active < inactive_threshold:
            to_remove.append(ip)

    for ip in to_remove:
        connected_devices.pop(ip, None)

    # Converte datetime para string serializável
    serialized = {
        ip: {
            'connection_time': info['connection_time'].isoformat(),
            'last_active': info['last_active'].isoformat() if hasattr(info['last_active'], 'isoformat') else info['last_active']
        }
        for ip, info in connected_devices.items()
    }
    return jsonify(serialized)


@app.route('/disconnect', methods=['POST'])
def disconnect_device():
    ip = request.args.get('ip')
    if ip in connected_devices:
        connected_devices.pop(ip)
    return jsonify(success=True)


@app.route('/blocked-ips')
def get_blocked_ips():
    return jsonify(list(blocked_ips))


@app.route('/block-ip', methods=['POST'])
def block_ip():
    ip = request.args.get('ip')
    if ip:
        blocked_ips.add(ip)
        if ip in connected_devices:
            connected_devices.pop(ip)
    return jsonify(success=True)


@app.route('/unblock-ip', methods=['POST'])
def unblock_ip():
    ip = request.args.get('ip')
    if ip in blocked_ips:
        blocked_ips.remove(ip)
    return jsonify(success=True)


@app.route('/ping', methods=['POST'])
def ping():
    ip = request.remote_addr
    if ip in connected_devices:
        connected_devices[ip]['last_active'] = datetime.now()
    return jsonify(success=True)


@app.route('/qrcode')
def generate_qrcode():
    control_url = f"http://{request.host}/control?token={current_token}"
    img = qrcode.make(control_url)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@app.route('/next', methods=['POST'])
def next_slide():
    ip = request.remote_addr
    if ip in blocked_ips:
        return jsonify(success=False, error="IP bloqueado"), 403

    token = request.args.get('token')
    if token != current_token:
        return jsonify(success=False, error="Token inválido"), 403

    update_device_activity(ip)
    success = send_key('right') or send_key('space')
    return jsonify(success=success)


@app.route('/previous', methods=['POST'])
def previous_slide():
    ip = request.remote_addr
    if ip in blocked_ips:
        return jsonify(success=False, error="IP bloqueado"), 403

    token = request.args.get('token')
    if token != current_token:
        return jsonify(success=False, error="Token inválido"), 403

    update_device_activity(ip)
    success = send_key('left')
    return jsonify(success=success)


@app.route('/fullscreen', methods=['POST'])
def fullscreen():
    ip = request.remote_addr
    if ip in blocked_ips:
        return jsonify(success=False, error="IP bloqueado"), 403

    token = request.args.get('token')
    if token != current_token:
        return jsonify(success=False, error="Token inválido"), 403

    update_device_activity(ip)
    try:
        pyautogui.press('f5')
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@app.route('/exit-fullscreen', methods=['POST'])
def exit_fullscreen():
    ip = request.remote_addr
    if ip in blocked_ips:
        return jsonify(success=False, error="IP bloqueado"), 403

    token = request.args.get('token')
    if token != current_token:
        return jsonify(success=False, error="Token inválido"), 403

    update_device_activity(ip)
    try:
        pyautogui.press('esc')
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def run_server():
    app.run(host='0.0.0.0', port=server_port, debug=False)


if __name__ == "__main__":
    local_ip = get_local_ip()
    url = f"http://{local_ip}:{server_port}/"
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    run_server()
