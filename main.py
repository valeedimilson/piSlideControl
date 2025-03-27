from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDTextButton
from kivy.uix.image import Image
from kivy.resources import resource_add_path
from kivy.core.window import Window
import os
import qrcode
import socket
import webbrowser
import threading
from client_frontend import run_server, update_token, get_current_token


class MainApp(MDApp):
    def build(self):
        resource_add_path(os.path.abspath("."))
        Window.set_icon(os.path.join(os.path.abspath("."), 'icon.ico'))
        self.title = "piSlideControl by Dimi(github.com/valeedimilson)"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"

        self.token = get_current_token()  # Obtém o token inicial
        self.connected_ips = {}
        self.blocked_ips = set()
        self.my_ip = self.get_local_ip()

        self.layout = MDBoxLayout(
            orientation='vertical', padding=10, spacing=10)

        self.qr_image = Image(source=self.generate_qr())
        self.layout.add_widget(self.qr_image)

        self.link_button = MDTextButton(
            text=f"http://{self.my_ip}:5000?token={self.token}",
            pos_hint={'center_x': .5},
            theme_text_color="Custom",
            text_color=(0, 1, 1, 1),
            on_release=self.open_link
        )
        self.layout.add_widget(self.link_button)

        self.new_qr_btn = MDFlatButton(
            text="Gerar Novo QR Code",
            pos_hint={'center_x': .5},
            on_release=self.generate_new_qr
        )
        self.layout.add_widget(self.new_qr_btn)

        self.start_server_thread()
        return self.layout

    def start_server_thread(self):
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def generate_qr(self):
        url = f"http://{self.my_ip}:5000/?token={self.token}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save("qrcode.png")
        return "qrcode.png"

    def generate_new_qr(self, *args):
        self.token = update_token()  # Atualiza o token usando a função do client_frontend
        self.qr_image.source = self.generate_qr()
        self.qr_image.reload()
        self.link_button.text = f"http://{self.my_ip}:5000/?token={self.token}"

    def open_link(self, *args):
        webbrowser.open(f"http://{self.my_ip}:5000?token={self.token}")


if __name__ == '__main__':
    MainApp().run()
