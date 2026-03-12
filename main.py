import customtkinter as ctk
from PIL import Image, ImageTk
import webbrowser
import qrcode
import threading
import time
import requests
import uuid
import socket
import os
import pinggy

# Importações do seu arquivo existente
from client_frontend import run_server, update_token, get_current_token, server_port

# Configurações da sua API e Site
SITE_BASE_URL = "http://10.0.0.10:3000" # Mude para a URL da Vercel depois!
API_URL = f"{SITE_BASE_URL}/api/tunnel"

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configurações da Janela
        self.title("PiSlideControl - Servidor")
        self.geometry("400x750") # Aumentei a altura para caber tudo confortavelmente
        self.resizable(False, False)

        # --- Configuração do Ícone da Janela (Método Definitivo Windows) ---
        try:
            # Coloque aqui o nome da sua imagem (logo.png ou logo.jpg)
            img_path = os.path.join(os.getcwd(), "static/logo.jpg") 
            
            if os.path.exists(img_path):
                img = Image.open(img_path)
                ico_path = os.path.join(os.getcwd(), "logo.ico")
                
                # Salva uma cópia temporária como .ico (padrão do Windows)
                img.save(ico_path, format="ICO", sizes=[(64, 64)])
                
                # Aplica o ícone na janela
                self.iconbitmap(ico_path)
        except Exception as e:
            print(f"Aviso: Não foi possível carregar o ícone da janela: {e}")
        # -------------------------------------------------------------------
        
        # Cor de fundo igual a do site (Beige)
        self.configure(fg_color="#ffecce") 

        # Variáveis de Controle
        self.pinggy_tunnel = None
        self.session_id = str(uuid.uuid4())[:8]
        self.token = get_current_token()
        self.my_ip = self.get_local_ip()
        
        # URL que o usuário vai acessar
        self.user_site_url = f"{SITE_BASE_URL}/control?sessionId={self.session_id}"
        
        self.stop_event = threading.Event()

        self.setup_ui()
        
        threading.Thread(target=run_server, daemon=True).start()
        threading.Thread(target=self.tunnel_lifecycle, daemon=True).start()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        # Barra de Título Azul (Header)
        self.header_frame = ctk.CTkFrame(self, fg_color="#2196f3", height=60, corner_radius=0)
        self.header_frame.pack(fill="x", side="top")
        self.header_frame.pack_propagate(False) # Impede que o frame encolha

        self.title_label = ctk.CTkLabel(self.header_frame, text="PiSlideControl v2.0", font=("Arial", 20, "bold"), text_color="white")
        self.title_label.pack(side="left", padx=15, pady=15)

        # Logo do Patinho (Precisa ter o arquivo logo.png na pasta!)
        try:
            logo_path = os.path.join(os.getcwd(), "static/logo.jpg")
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path)
                self.logo_ctk = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(160, 190))
                self.logo_label = ctk.CTkLabel(self, image=self.logo_ctk, text="")
                self.logo_label.pack(pady=(20, 10))
        except Exception as e:
            print("Aviso: logo.jpg não encontrado. A interface ficará sem o patinho.")

        # Textos com ID e Link
        self.id_label = ctk.CTkLabel(self, text=f"ID da Sessão: {self.session_id}", font=("Arial", 14, "bold"), text_color="#333333")
        self.id_label.pack(pady=(0, 5))

        # Espaço para o QR Code
        self.qr_label = ctk.CTkLabel(self, text="")
        self.qr_label.pack(pady=5)
        self.update_qr_code()

         # Novo Label mostrando o Link
        self.link_label = ctk.CTkLabel(self, text=self.user_site_url, font=("Arial", 12), text_color="#2196f3")
        self.link_label.pack(pady=(0, 10))

        # Botão para copiar link (Estilizado)
        self.copy_btn = ctk.CTkButton(self, text="Copiar Link", command=self.copy_link, fg_color="#2196f3", hover_color="#1976d2", font=("Arial", 14, "bold"), corner_radius=10)
        self.copy_btn.pack(pady=5)

        # Status
        self.status_label = ctk.CTkLabel(self, text="Iniciando ponte com o servidor...", font=("Arial", 14, "bold"), text_color="#f57c00")
        self.status_label.pack(pady=5)


        # Botão/Link para a Landing Page (Estilo Hyperlink)
        self.site_btn = ctk.CTkButton(
            self, 
            text="Visitar o site oficial", 
            command=self.open_landing_page, 
            fg_color="transparent", # Deixa sem fundo
            text_color="#2196f3",   # Azul padrão do seu tema
            hover_color="#ffcc80",  # Cor suave ao passar o mouse
            font=("Arial", 12, "underline"),
            cursor="hand2"          # Muda o mouse para a "mãozinha" de clique
        )
        self.site_btn.pack(pady=(0, 5))

        # Informativo no rodapé
        self.info_label = ctk.CTkLabel(self, text="Renovação automática: 55 min", font=("Arial", 11), text_color="#888888")
        self.info_label.pack(side="bottom", pady=5)

    def tunnel_lifecycle(self):
        while not self.stop_event.is_set():
            print("\n[+] Iniciando nova conexão Pinggy...")
            self.update_status_ui("Conectando ao Pinggy...", "yellow")
            
            try:
                self.pinggy_tunnel = pinggy.start_tunnel(forwardto=f"localhost:{server_port}")
                urls = self.pinggy_tunnel.urls
                
                pinggy_url = None
                if isinstance(urls, list):
                    pinggy_url = next((u for u in urls if u.startswith("https://")), urls[0] if urls else None)
                elif isinstance(urls, dict):
                    pinggy_url = urls.get("https", str(urls))
                else:
                    pinggy_url = str(urls)

                if pinggy_url:
                    pinggy_url = pinggy_url.rstrip("/")
                    full_local_url = f"{pinggy_url}/?token={self.token}"
                    print(f"[+] Túnel criado: {full_local_url}")
                    
                    self.update_status_ui("Sincronizando com o Site...", "orange")
                    self.send_to_api(full_local_url)
                else:
                    self.update_status_ui("Erro ao obter URL do Pinggy", "red")

            except Exception as e:
                self.update_status_ui("Erro na conexão Pinggy", "red")

            interrupted = self.stop_event.wait(timeout=55 * 60)
            if interrupted:
                break
                
            print("\n[*] 55 minutos se passaram. Renovando túnel...")
            self.close_tunnel()

    def send_to_api(self, pinggy_url):
        payload = {"sessionId": self.session_id, "pinggyUrl": pinggy_url}
        try:
            response = requests.post(API_URL, json=payload, timeout=10)
            if response.status_code == 200:
                # Cor verde escuro para dar contraste no fundo bege
                self.update_status_ui("Túnel Ativo e Sincronizado", "#388e3c") 
            else:
                self.update_status_ui("Erro ao sincronizar com DB", "red")
        except Exception as e:
            self.update_status_ui("Falha de rede (API Offline)", "red")

    def update_status_ui(self, text, color):
        # Ajuste de cores para tema claro
        if color == "yellow": color = "#f57c00" # Laranja escuro no lugar do amarelo
        elif color == "orange": color = "#e65100"
        self.after(0, lambda: self.status_label.configure(text=text, text_color=color))

    def update_qr_code(self):
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(self.user_site_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        qr_path = os.path.join(os.getcwd(), "qrcode_site.png")
        img.save(qr_path)

        pil_img = Image.open(qr_path)
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(250, 250))
        self.qr_label.configure(image=ctk_img)
        self.qr_label.image = ctk_img

    def copy_link(self):
        self.clipboard_clear()
        self.clipboard_append(self.user_site_url)
        self.update()
        self.copy_btn.configure(text="Copiado!", fg_color="#388e3c") # Fica verde ao copiar
        self.after(2000, lambda: self.copy_btn.configure(text="Copiar Link", fg_color="#2196f3"))

    def open_landing_page(self):
        """Abre a página inicial (Landing Page) no navegador padrão"""
        webbrowser.open(SITE_BASE_URL)

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def close_tunnel(self):
        if self.pinggy_tunnel:
            try:
                if hasattr(self.pinggy_tunnel, 'stop'):
                    self.pinggy_tunnel.stop()
                elif hasattr(self.pinggy_tunnel, 'close'):
                    self.pinggy_tunnel.close()
            except Exception:
                pass

    def on_close(self):
        print("\nEncerrando aplicação e limpando processos...")
        self.stop_event.set()
        self.close_tunnel()
        self.destroy()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()