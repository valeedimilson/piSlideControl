import qrcode
import socket
import webbrowser
import threading
import tkinter as tk
from tkinter import Label, Button, PhotoImage
from PIL import Image, ImageTk
from client_frontend import run_server, update_token, get_current_token

class MainApp:
    def center_window(self, width=440, height=550):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def __init__(self, root):
        self.root = root
        self.root.title("piSlideControl by Dimi (github.com/valeedimilson)")
        self.root.iconbitmap("icon.ico")
        self.root.configure(bg='black')
        self.root.geometry("440x550")

        self.center_window()

        self.token = get_current_token()
        self.my_ip = self.get_local_ip()
        
        # Gerar QR Code inicial
        self.qr_path = self.generate_qr()
        
        # Exibir QR Code
        self.qr_image = ImageTk.PhotoImage(Image.open(self.qr_path))
        self.qr_label = Label(root, image=self.qr_image, bg='black')
        self.qr_label.pack(pady=10)

        # Botão para abrir o link
        self.link_button = Button(
            root, text=f"http://{self.my_ip}:5000?token={self.token}",
            fg='cyan', bg='black', borderwidth=0,
            command=self.open_link
        )
        self.link_button.pack(pady=10)

        # Botão para gerar novo QR Code
        self.new_qr_btn = Button(
            root, text="Gerar Novo QR Code",
            command=self.generate_new_qr
        )
        self.new_qr_btn.pack(pady=10)

        self.start_server_thread()

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
        qr_path = "qrcode.png"
        img.save(qr_path)
        return qr_path

    def generate_new_qr(self):
        self.token = update_token()
        self.qr_path = self.generate_qr()
        self.qr_image = ImageTk.PhotoImage(Image.open(self.qr_path))
        self.qr_label.config(image=self.qr_image)
        self.link_button.config(text=f"http://{self.my_ip}:5000/?token={self.token}")

    def open_link(self):
        webbrowser.open(f"http://{self.my_ip}:5000?token={self.token}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
