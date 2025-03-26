from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDTextButton
from kivymd.uix.label import MDLabel
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelOneLine
from kivy.uix.image import Image
import qrcode
import random
import string
from kivy.clock import Clock
import socket
import webbrowser
import threading  # Adicionado para gerenciar threads

from client_frontend import run_server


class MainApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"

        self.token = "current_token"
        self.connected_ips = {}  # {ip: status}
        self.blocked_ips = set()
        self.my_ip = self.get_local_ip()  # Obtém o IP local da máquina

        self.layout = MDBoxLayout(
            orientation='vertical', padding=20, spacing=20)

        # QR Code
        self.qr_image = Image(source=self.generate_qr())
        self.layout.add_widget(self.qr_image)

        # Botão de texto clicável para o link
        self.link_button = MDTextButton(
            text=f"http://{self.my_ip}:5000?token={self.token}",
            pos_hint={'center_x': .5},
            theme_text_color="Custom",
            text_color=(0, 1, 1, 1),  # Cor ciano para indicar que é clicável
            on_release=self.open_link
        )
        self.layout.add_widget(self.link_button)

        # Botão para gerar novo QR
        self.new_qr_btn = MDFlatButton(
            text="Gerar Novo QR Code",
            pos_hint={'center_x': .5},
            on_release=self.generate_new_qr
        )
        self.layout.add_widget(self.new_qr_btn)

        # Painel de IPs conectados
        self.connected_panel = MDExpansionPanel(
            content=self.create_connected_content(),
            panel_cls=MDExpansionPanelOneLine(text="IPs Conectados")
        )
        self.layout.add_widget(self.connected_panel)

        # Painel de IPs bloqueados
        self.blocked_panel = MDExpansionPanel(
            content=self.create_blocked_content(),
            panel_cls=MDExpansionPanelOneLine(text="IPs Bloqueados")
        )
        self.layout.add_widget(self.blocked_panel)

        # Simulação de atualização de IPs conectados
        Clock.schedule_interval(self.update_connected_ips, 5)

        # Inicia o servidor em uma thread separada
        self.start_server_thread()

        return self.layout

    def start_server_thread(self):
        # Cria e inicia a thread para rodar o servidor
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

    def get_local_ip(self):
        # Obtém o IP local da máquina
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Conecta a um servidor externo (Google DNS)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"  # Retorna localhost em caso de erro

    def generate_qr(self):
        url = f"http://{self.my_ip}:5000?token={self.token}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save("qrcode.png")
        return "qrcode.png"

    def generate_new_qr(self, *args):
        
        self.token = "sdfsd"
        self.qr_image.source = self.generate_qr()
        self.qr_image.reload()
        # Atualiza o texto do botão de link
        self.link_button.text = f"http://{self.my_ip}:5000?token={self.token}"

    def open_link(self, *args):
        # Abre o link no navegador padrão
        webbrowser.open(f"http://{self.my_ip}:5000?token={self.token}")

    def create_connected_content(self):
        content = MDBoxLayout(orientation='vertical', padding=10)
        self.connected_content = content
        return content

    def create_blocked_content(self):
        content = MDBoxLayout(orientation='vertical', padding=10)
        self.blocked_content = content
        return content

    def update_connected_ips(self, dt):
        # Lê os IPs do arquivo ativos.txt
        try:
            with open("ativos.txt", "r") as file:
                sample_ips = [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            sample_ips = []  # Se o arquivo não existir, usa lista vazia

        # Atualiza o dicionário de IPs conectados
        # Assume todos como ativos por padrão
        self.connected_ips = {ip: True for ip in sample_ips}

        # Atualizar conteúdo dos IPs conectados
        self.connected_content.clear_widgets()
        for ip, active in self.connected_ips.items():
            if ip not in self.blocked_ips:
                row = MDBoxLayout(orientation='horizontal',
                                  size_hint_y=None, height=40)
                status = "Ativo" if active else "Inativo"
                row.add_widget(MDLabel(text=f"{ip} - {status}"))
                block_btn = MDFlatButton(
                    text="Bloquear",
                    on_release=lambda x, ip=ip: self.block_ip(ip)
                )
                row.add_widget(block_btn)
                self.connected_content.add_widget(row)

        # Atualizar conteúdo dos IPs bloqueados
        self.blocked_content.clear_widgets()
        for ip in self.blocked_ips:
            row = MDBoxLayout(orientation='horizontal',
                              size_hint_y=None, height=40)
            row.add_widget(MDLabel(text=ip))
            unblock_btn = MDFlatButton(
                text="Desbloquear",
                on_release=lambda x, ip=ip: self.unblock_ip(ip)
            )
            row.add_widget(unblock_btn)
            self.blocked_content.add_widget(row)

    def block_ip(self, ip):
        self.blocked_ips.add(ip)
        self.update_connected_ips(0)

    def unblock_ip(self, ip):
        self.blocked_ips.discard(ip)
        self.update_connected_ips(0)


if __name__ == '__main__':
    MainApp().run()
