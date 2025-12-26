#!/usr/bin/env python3
"""
UstajonSupport Client - Windows Desktop Application v2.0
Professional remote support client with modern UI
Build: pyinstaller --onefile --windowed --icon=icon.ico --name=UstajonSupport ustajon_support.py
"""
import os
import sys
import json
import socket
import platform
import subprocess
import threading
import time
import urllib.request
import urllib.parse
import tkinter as tk
from tkinter import ttk, messagebox
import uuid
import logging
from datetime import datetime

# ============ SOZLAMALAR ============
VERSION = "2.0.0"
SERVER_URL = "http://31.220.75.75"
RUSTDESK_KEY = "YHo+N4vp+ZWP7wedLh69zCGk3aFf4935hwDKX9OdFXE="
RUSTDESK_SERVER = "31.220.75.75"
RUSTDESK_PASSWORD = "ustajon2025"
RUSTDESK_URL = "https://github.com/rustdesk/rustdesk/releases/download/1.2.3/rustdesk-1.2.3-x86_64.exe"

# Logging sozlash
log_dir = os.path.join(os.environ.get("APPDATA", "."), "UstajonSupport")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "support.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class ModernButton(tk.Canvas):
    """Zamonaviy animatsiyali tugma"""
    def __init__(self, parent, text, command, bg="#00d4ff", fg="#000000", width=380, height=50):
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0)
        self.command = command
        self.bg_color = bg
        self.fg_color = fg
        self.text = text
        self.width = width
        self.height = height
        self.enabled = True
        
        self.draw_button()
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        
    def draw_button(self, hover=False):
        self.delete("all")
        color = self.lighten(self.bg_color, 20) if hover else self.bg_color
        # Rounded rectangle
        r = 12
        self.create_polygon(
            r, 0, self.width-r, 0, self.width, r, self.width, self.height-r,
            self.width-r, self.height, r, self.height, 0, self.height-r, 0, r,
            fill=color, outline=""
        )
        self.create_text(self.width//2, self.height//2, text=self.text, 
                        fill=self.fg_color, font=("Segoe UI", 13, "bold"))
        
    def lighten(self, color, amount):
        color = color.lstrip('#')
        r = min(255, int(color[0:2], 16) + amount)
        g = min(255, int(color[2:4], 16) + amount)
        b = min(255, int(color[4:6], 16) + amount)
        return f"#{r:02x}{g:02x}{b:02x}"
        
    def on_enter(self, e):
        if self.enabled:
            self.draw_button(hover=True)
            
    def on_leave(self, e):
        self.draw_button(hover=False)
        
    def on_click(self, e):
        if self.enabled and self.command:
            self.command()
            
    def set_text(self, text):
        self.text = text
        self.draw_button()
        
    def set_enabled(self, enabled):
        self.enabled = enabled
        if not enabled:
            self.bg_color = "#555555"
        self.draw_button()
        
    def set_color(self, bg):
        self.bg_color = bg
        self.draw_button()


class AnimatedProgress(tk.Canvas):
    """Animatsiyali progress bar"""
    def __init__(self, parent, width=300, height=6):
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0)
        self.width = width
        self.height = height
        self.running = False
        self.position = 0
        
    def start(self):
        self.running = True
        self.animate()
        
    def stop(self):
        self.running = False
        self.delete("all")
        
    def animate(self):
        if not self.running:
            return
        self.delete("all")
        # Background
        self.create_rectangle(0, 0, self.width, self.height, fill="#2d2d44", outline="")
        # Progress bar
        bar_width = 80
        x = self.position % (self.width + bar_width) - bar_width
        self.create_rectangle(x, 0, x + bar_width, self.height, fill="#00d4ff", outline="")
        self.position += 5
        self.after(30, self.animate)


class StatusLabel(tk.Label):
    """Animatsiyali status label"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.dots = 0
        self.base_text = ""
        self.animating = False
        
    def set_status(self, text, color="#888888", animate=False):
        self.base_text = text
        self.config(text=text, fg=color)
        if animate and not self.animating:
            self.animating = True
            self.animate_dots()
        elif not animate:
            self.animating = False
            
    def animate_dots(self):
        if not self.animating:
            return
        self.dots = (self.dots + 1) % 4
        self.config(text=self.base_text + "." * self.dots)
        self.after(500, self.animate_dots)


class UstajonSupport:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"UstajonSupport v{VERSION}")
        self.root.geometry("480x620")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f0f1a")
        
        # Center window
        self.center_window()
        
        # Variables
        self.name_var = tk.StringVar()
        self.phone_var = tk.StringVar(value="+998")
        self.problem_var = tk.StringVar(value="Kompyuter sekin ishlayapti")
        self.rustdesk_id = None
        self.connection_status = "disconnected"
        
        # Tray icon placeholder
        self.setup_ui()
        logging.info(f"UstajonSupport v{VERSION} ishga tushdi")
        
    def center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - 480) // 2
        y = (sh - 620) // 2
        self.root.geometry(f"480x620+{x}+{y}")
        
    def setup_ui(self):
        # Main container with padding
        main = tk.Frame(self.root, bg="#0f0f1a")
        main.pack(fill="both", expand=True, padx=40, pady=30)
        
        # === HEADER ===
        header = tk.Frame(main, bg="#0f0f1a")
        header.pack(fill="x", pady=(0, 20))
        
        # Logo circle
        logo_canvas = tk.Canvas(header, width=80, height=80, bg="#0f0f1a", highlightthickness=0)
        logo_canvas.pack()
        logo_canvas.create_oval(5, 5, 75, 75, fill="#00d4ff", outline="")
        logo_canvas.create_text(40, 40, text="U", font=("Segoe UI", 32, "bold"), fill="#0f0f1a")
        
        # Title
        tk.Label(header, text="UstajonSupport", font=("Segoe UI", 26, "bold"),
                fg="#ffffff", bg="#0f0f1a").pack(pady=(15, 2))
        tk.Label(header, text="Professional kompyuter yordam xizmati", 
                font=("Segoe UI", 10), fg="#666666", bg="#0f0f1a").pack()
        
        # === FORM ===
        form = tk.Frame(main, bg="#0f0f1a")
        form.pack(fill="x", pady=(10, 0))
        
        # Input style
        entry_style = {"font": ("Segoe UI", 12), "bg": "#1a1a2e", "fg": "#ffffff",
                      "insertbackground": "#00d4ff", "relief": "flat", 
                      "highlightthickness": 2, "highlightbackground": "#2d2d44",
                      "highlightcolor": "#00d4ff"}
        
        # Name field
        name_frame = tk.Frame(form, bg="#0f0f1a")
        name_frame.pack(fill="x", pady=(0, 15))
        tk.Label(name_frame, text="👤 Ismingiz", font=("Segoe UI", 10, "bold"),
                fg="#aaaaaa", bg="#0f0f1a", anchor="w").pack(fill="x")
        name_entry = tk.Entry(name_frame, textvariable=self.name_var, **entry_style)
        name_entry.pack(fill="x", pady=(5, 0), ipady=12)
        
        # Phone field
        phone_frame = tk.Frame(form, bg="#0f0f1a")
        phone_frame.pack(fill="x", pady=(0, 15))
        tk.Label(phone_frame, text="📱 Telefon raqam", font=("Segoe UI", 10, "bold"),
                fg="#aaaaaa", bg="#0f0f1a", anchor="w").pack(fill="x")
        phone_entry = tk.Entry(phone_frame, textvariable=self.phone_var, **entry_style)
        phone_entry.pack(fill="x", pady=(5, 0), ipady=12)
        
        # Problem dropdown
        problem_frame = tk.Frame(form, bg="#0f0f1a")
        problem_frame.pack(fill="x", pady=(0, 25))
        tk.Label(problem_frame, text="🔧 Muammo turi", font=("Segoe UI", 10, "bold"),
                fg="#aaaaaa", bg="#0f0f1a", anchor="w").pack(fill="x")
        
        problems = [
            "Kompyuter sekin ishlayapti",
            "Virus tekshirish kerak",
            "Dastur o'rnatish",
            "Internet ishlamayapti",
            "Windows muammosi",
            "Office dasturlari",
            "Printer sozlash",
            "Boshqa muammo"
        ]
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Custom.TCombobox", 
                       fieldbackground="#1a1a2e",
                       background="#1a1a2e",
                       foreground="#ffffff",
                       arrowcolor="#00d4ff")
        
        combo = ttk.Combobox(problem_frame, textvariable=self.problem_var, 
                            values=problems, font=("Segoe UI", 11), 
                            state="readonly", style="Custom.TCombobox")
        combo.pack(fill="x", pady=(5, 0), ipady=10)
        
        # === BUTTON ===
        self.btn = ModernButton(form, text="🚀 Yordam olish", command=self.start_support)
        self.btn.pack(pady=(10, 0))
        
        # === STATUS ===
        status_frame = tk.Frame(main, bg="#0f0f1a")
        status_frame.pack(fill="x", pady=(20, 0))
        
        self.status_label = StatusLabel(status_frame, text="Tayyor", 
                                        font=("Segoe UI", 10), fg="#666666", bg="#0f0f1a")
        self.status_label.pack()
        
        self.progress = AnimatedProgress(status_frame)
        
        # === INFO BOX ===
        info_frame = tk.Frame(main, bg="#1a1a2e", padx=15, pady=15)
        info_frame.pack(fill="x", pady=(25, 0))
        
        tk.Label(info_frame, text="ℹ️ Qanday ishlaydi?", font=("Segoe UI", 11, "bold"),
                fg="#00d4ff", bg="#1a1a2e", anchor="w").pack(fill="x")
        
        steps = [
            "1. Ma'lumotlaringizni kiriting",
            "2. \"Yordam olish\" tugmasini bosing", 
            "3. RustDesk avtomatik o'rnatiladi",
            "4. Admin kompyuteringizga ulanadi"
        ]
        for step in steps:
            tk.Label(info_frame, text=step, font=("Segoe UI", 9),
                    fg="#888888", bg="#1a1a2e", anchor="w").pack(fill="x", pady=(3, 0))
        
        # === FOOTER ===
        footer = tk.Frame(main, bg="#0f0f1a")
        footer.pack(side="bottom", fill="x", pady=(20, 0))
        
        tk.Label(footer, text=f"v{VERSION} • Telegram: @ustajonbot", 
                font=("Segoe UI", 8), fg="#444444", bg="#0f0f1a").pack()
        
    def start_support(self):
        name = self.name_var.get().strip()
        phone = self.phone_var.get().strip()
        
        # Validation
        if not name or len(name) < 2:
            self.show_error("Ismingizni to'liq kiriting!")
            return
            
        if not phone or len(phone) < 12:
            self.show_error("Telefon raqamni to'liq kiriting!\nMasalan: +998901234567")
            return
            
        if not phone.startswith("+998"):
            self.show_error("Telefon +998 bilan boshlanishi kerak!")
            return
        
        # Disable button and start
        self.btn.set_enabled(False)
        self.btn.set_text("⏳ Kutib turing...")
        self.progress.pack(pady=(15, 0))
        self.progress.start()
        
        logging.info(f"Yordam so'rovi: {name}, {phone}")
        threading.Thread(target=self.setup_process, args=(name, phone), daemon=True).start()
        
    def show_error(self, message):
        self.status_label.set_status("❌ " + message.split("\n")[0], "#ff4444")
        messagebox.showerror("Xatolik", message)
        
    def setup_process(self, name, phone):
        try:
            # Step 1: Check RustDesk
            self.update_status("🔍 RustDesk tekshirilmoqda", "#ffaa00", True)
            rustdesk_path = self.find_rustdesk()
            
            # Step 2: Download if needed
            if not rustdesk_path:
                self.update_status("📥 RustDesk yuklanmoqda", "#ffaa00", True)
                rustdesk_path = self.download_rustdesk()
                if not rustdesk_path:
                    raise Exception("RustDesk yuklab bo'lmadi")
            
            # Step 3: Configure
            self.update_status("⚙️ Sozlanmoqda", "#ffaa00", True)
            self.configure_rustdesk(rustdesk_path)
            
            # Step 4: Get ID
            self.update_status("🔑 ID olinmoqda", "#ffaa00", True)
            time.sleep(3)
            self.rustdesk_id = self.get_rustdesk_id()
            logging.info(f"RustDesk ID: {self.rustdesk_id}")
            
            # Step 5: Register with server
            self.update_status("🌐 Serverga ulanmoqda", "#ffaa00", True)
            success = self.register_with_server(name, phone)
            
            if success:
                self.update_status("✅ Muvaffaqiyatli ulandi!", "#00ff00", False)
                self.connection_status = "connected"
                self.root.after(0, self.show_success)
                self.start_heartbeat()
            else:
                raise Exception("Server bilan bog'lanib bo'lmadi")
                
        except Exception as e:
            logging.error(f"Xatolik: {str(e)}")
            self.update_status(f"❌ Xatolik: {str(e)}", "#ff4444", False)
            self.root.after(0, self.reset_button)
            
    def update_status(self, text, color, animate):
        self.root.after(0, lambda: self.status_label.set_status(text, color, animate))
        
    def find_rustdesk(self):
        """RustDesk o'rnatilganligini tekshirish"""
        paths = [
            os.path.expandvars(r"%ProgramFiles%\RustDesk\rustdesk.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\RustDesk\rustdesk.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\RustDesk\rustdesk.exe"),
            r"C:\Program Files\RustDesk\rustdesk.exe",
            r"C:\Program Files (x86)\RustDesk\rustdesk.exe"
        ]
        for path in paths:
            if os.path.exists(path):
                logging.info(f"RustDesk topildi: {path}")
                return path
        logging.info("RustDesk topilmadi, yuklab olish kerak")
        return None
        
    def download_rustdesk(self):
        """RustDesk yuklab olish va o'rnatish"""
        try:
            temp_path = os.path.join(os.environ.get("TEMP", "."), "rustdesk_setup.exe")
            
            # Download with progress
            logging.info(f"RustDesk yuklanmoqda: {RUSTDESK_URL}")
            urllib.request.urlretrieve(RUSTDESK_URL, temp_path)
            
            # Silent install
            logging.info("RustDesk o'rnatilmoqda...")
            result = subprocess.run(
                [temp_path, "--silent-install"], 
                capture_output=True, 
                timeout=180,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            time.sleep(5)
            
            # Find installed path
            return self.find_rustdesk()
            
        except Exception as e:
            logging.error(f"RustDesk yuklashda xatolik: {str(e)}")
            return None
            
    def configure_rustdesk(self, rustdesk_path):
        """RustDesk sozlash"""
        try:
            config_dir = os.path.join(os.environ.get("APPDATA", "."), "RustDesk", "config")
            os.makedirs(config_dir, exist_ok=True)
            
            # Main config
            config_content = f'''rendezvous_server = "{RUSTDESK_SERVER}"
nat_type = 1
serial = 0

[options]
custom-rendezvous-server = "{RUSTDESK_SERVER}"
relay-server = "{RUSTDESK_SERVER}"
key = "{RUSTDESK_KEY}"
direct-server = "Y"
direct-access-port = ""
'''
            
            config_path = os.path.join(config_dir, "RustDesk2.toml")
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(config_content)
            logging.info(f"Config saqlandi: {config_path}")
            
            # Set password
            try:
                subprocess.run(
                    [rustdesk_path, "--password", RUSTDESK_PASSWORD],
                    capture_output=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
            except:
                pass
                
            # Start RustDesk
            subprocess.Popen(
                [rustdesk_path],
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0x08000000
            )
            logging.info("RustDesk ishga tushirildi")
            
        except Exception as e:
            logging.error(f"RustDesk sozlashda xatolik: {str(e)}")
            raise
            
    def get_rustdesk_id(self):
        """RustDesk ID olish"""
        config_path = os.path.join(
            os.environ.get("APPDATA", "."), 
            "RustDesk", "config", "RustDesk.toml"
        )
        
        for attempt in range(15):
            try:
                if os.path.exists(config_path):
                    with open(config_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        for line in content.split("\n"):
                            if line.strip().startswith("id"):
                                parts = line.split("=")
                                if len(parts) >= 2:
                                    id_value = parts[1].strip().strip("'\"")
                                    if id_value and len(id_value) >= 6:
                                        return id_value
            except Exception as e:
                logging.warning(f"ID olishda xatolik (urinish {attempt+1}): {str(e)}")
            time.sleep(1)
            
        # Fallback ID
        fallback_id = str(uuid.uuid4())[:9].upper().replace("-", "")
        logging.warning(f"Fallback ID ishlatilmoqda: {fallback_id}")
        return fallback_id
        
    def register_with_server(self, name, phone):
        """Serverga ro'yxatdan o'tish"""
        try:
            data = {
                "name": name,
                "phone": phone,
                "problem": self.problem_var.get(),
                "rustdesk_id": self.rustdesk_id,
                "computer_name": socket.gethostname(),
                "os_info": f"{platform.system()} {platform.release()} ({platform.machine()})",
                "client_version": VERSION,
                "local_ip": self.get_local_ip()
            }
            
            encoded_data = urllib.parse.urlencode(data).encode("utf-8")
            
            req = urllib.request.Request(
                f"{SERVER_URL}/api/agent/register",
                data=encoded_data,
                method="POST"
            )
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            req.add_header("User-Agent", f"UstajonSupport/{VERSION}")
            
            response = urllib.request.urlopen(req, timeout=30)
            result = response.read().decode("utf-8")
            logging.info(f"Server javobi: {result}")
            return True
            
        except Exception as e:
            logging.error(f"Server bilan bog'lanishda xatolik: {str(e)}")
            return False
            
    def get_local_ip(self):
        """Lokal IP manzilni olish"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "Unknown"
            
    def show_success(self):
        """Muvaffaqiyat oynasi"""
        self.progress.stop()
        self.progress.pack_forget()
        self.btn.set_color("#00aa00")
        self.btn.set_text("✅ Ulangan")
        
        success_msg = f"""🎉 Muvaffaqiyatli ulandi!

�� RustDesk ID: {self.rustdesk_id}
🔐 Parol: {RUSTDESK_PASSWORD}

Admin tez orada kompyuteringizga ulanadi.
Iltimos, dasturni yopmang!

📱 Telegram: @ustajonbot
📞 Qo'ng'iroq: +998912981511"""
        
        messagebox.showinfo("Muvaffaqiyat!", success_msg)
        
    def reset_button(self):
        """Tugmani qayta tiklash"""
        self.progress.stop()
        self.progress.pack_forget()
        self.btn.set_color("#00d4ff")
        self.btn.set_text("🚀 Yordam olish")
        self.btn.set_enabled(True)
        
    def start_heartbeat(self):
        """Server bilan aloqani saqlab turish"""
        def heartbeat_loop():
            while True:
                try:
                    data = urllib.parse.urlencode({
                        "rustdesk_id": self.rustdesk_id,
                        "status": "online",
                        "version": VERSION
                    }).encode("utf-8")
                    
                    req = urllib.request.Request(
                        f"{SERVER_URL}/api/agent/heartbeat",
                        data=data,
                        method="POST"
                    )
                    req.add_header("Content-Type", "application/x-www-form-urlencoded")
                    urllib.request.urlopen(req, timeout=10)
                    
                except Exception as e:
                    logging.warning(f"Heartbeat xatolik: {str(e)}")
                    
                time.sleep(60)
                
        thread = threading.Thread(target=heartbeat_loop, daemon=True)
        thread.start()
        logging.info("Heartbeat boshlandi")
        
    def run(self):
        """Dasturni ishga tushirish"""
        try:
            # Icon sozlash (agar mavjud bo'lsa)
            icon_path = os.path.join(os.path.dirname(sys.executable), "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
            
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()
        
    def on_close(self):
        """Dasturni yopish"""
        if self.connection_status == "connected":
            if messagebox.askyesno("Chiqish", "Dasturni yopmoqchimisiz?\nAdmin ulanishi mumkin emas bo'lib qoladi."):
                logging.info("Dastur yopildi")
                self.root.destroy()
        else:
            self.root.destroy()


def check_single_instance():
    """Bitta nusxada ishlashini tekshirish"""
    lock_file = os.path.join(os.environ.get("TEMP", "."), "ustajon_support.lock")
    try:
        if os.path.exists(lock_file):
            # Check if old process is still running
            with open(lock_file, "r") as f:
                old_pid = f.read().strip()
            # Windows process check
            try:
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {old_pid}"],
                    capture_output=True, text=True
                )
                if old_pid in result.stdout:
                    messagebox.showwarning("Ogohlantirish", 
                        "UstajonSupport allaqachon ishlamoqda!")
                    return False
            except:
                pass
                
        # Write current PID
        with open(lock_file, "w") as f:
            f.write(str(os.getpid()))
        return True
        
    except Exception as e:
        logging.warning(f"Lock tekshirishda xatolik: {str(e)}")
        return True


if __name__ == "__main__":
    if check_single_instance():
        app = UstajonSupport()
        app.run()
