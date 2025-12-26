#!/usr/bin/env python3
"""
UstajonSupport Client v3.1 - Professional Windows Application
Fixed RustDesk ID detection
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
import urllib.error
import tkinter as tk
from tkinter import ttk, messagebox
import uuid
import hashlib
import logging
import re
from datetime import datetime
import ctypes

# ============ CONSTANTS ============
VERSION = "3.1.0"
APP_NAME = "UstajonSupport"
SERVER_URL = "http://31.220.75.75"
RUSTDESK_KEY = "YHo+N4vp+ZWP7wedLh69zCGk3aFf4935hwDKX9OdFXE="
RUSTDESK_SERVER = "31.220.75.75"
RUSTDESK_PASSWORD = "ustajon2025"
RUSTDESK_URL = "https://github.com/rustdesk/rustdesk/releases/download/1.2.3/rustdesk-1.2.3-x86_64.exe"

# Colors
COLORS = {
    "bg_dark": "#0a0a0f",
    "bg_card": "#12121a",
    "bg_input": "#1a1a25",
    "accent": "#6366f1",
    "accent_light": "#818cf8",
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "text": "#ffffff",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "border": "#2d2d3d"
}

# App Data
APP_DATA = os.path.join(os.environ.get("APPDATA", "."), APP_NAME)
os.makedirs(APP_DATA, exist_ok=True)
CONFIG_FILE = os.path.join(APP_DATA, "config.json")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(APP_DATA, "app.log"), encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        self.data = self._load()
    
    def _load(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except:
            pass
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def set(self, key, value):
        self.data[key] = value
        self.save()


class GradientButton(tk.Canvas):
    def __init__(self, parent, text, command, width=360, height=52, gradient=("6366f1", "8b5cf6")):
        super().__init__(parent, width=width, height=height, bg=COLORS["bg_card"], highlightthickness=0)
        self.text = text
        self.command = command
        self.width = width
        self.height = height
        self.gradient = gradient
        self.enabled = True
        self.hover = False
        self._draw()
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<Button-1>", self._click)
        
    def _draw(self):
        self.delete("all")
        c = self.gradient[1] if self.hover and self.enabled else self.gradient[0]
        if not self.enabled:
            c = "4b5563"
        self.create_rectangle(0, 0, self.width, self.height, fill=f"#{c}", outline="")
        self.create_text(self.width//2, self.height//2, text=self.text, fill="#fff", font=("Segoe UI", 13, "bold"))
    
    def _set_hover(self, h):
        self.hover = h
        self._draw()
        self.config(cursor="hand2" if h and self.enabled else "")
    
    def _click(self, e):
        if self.enabled and self.command:
            self.command()
    
    def set_text(self, t):
        self.text = t
        self._draw()
    
    def set_enabled(self, e):
        self.enabled = e
        self._draw()
    
    def set_gradient(self, g):
        self.gradient = g
        self._draw()


class ProgressBar(tk.Canvas):
    def __init__(self, parent, width=300, height=4):
        super().__init__(parent, width=width, height=height, bg=COLORS["bg_card"], highlightthickness=0)
        self.w = width
        self.h = height
        self.running = False
        self.pos = 0
        
    def start(self):
        self.running = True
        self._animate()
    
    def stop(self):
        self.running = False
        self.delete("all")
    
    def _animate(self):
        if not self.running:
            return
        self.delete("all")
        self.create_rectangle(0, 0, self.w, self.h, fill=COLORS["bg_input"], outline="")
        x = self.pos % (self.w + 80) - 80
        self.create_rectangle(max(0, x), 0, min(self.w, x+80), self.h, fill=COLORS["accent"], outline="")
        self.pos += 4
        self.after(20, self._animate)


class StatusBadge(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg_card"])
        self.dot = tk.Canvas(self, width=10, height=10, bg=COLORS["bg_card"], highlightthickness=0)
        self.dot.pack(side="left", padx=(0, 8))
        self.label = tk.Label(self, text="Tayyor", font=("Segoe UI", 10), fg=COLORS["text_muted"], bg=COLORS["bg_card"])
        self.label.pack(side="left")
        self.set("default", "Tayyor")
    
    def set(self, status, text):
        colors = {"default": COLORS["text_muted"], "loading": COLORS["warning"], 
                  "success": COLORS["success"], "error": COLORS["error"]}
        c = colors.get(status, COLORS["text_muted"])
        self.dot.delete("all")
        self.dot.create_oval(1, 1, 9, 9, fill=c, outline="")
        self.label.config(text=text, fg=c)


class UstajonSupportApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{VERSION}")
        self.root.geometry("500x700")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS["bg_dark"])
        self._center()
        
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        
        self.config = Config()
        self.client_id = None
        self.rustdesk_id = self.config.get("rustdesk_id")
        self.is_registered = self.config.get("registered", False)
        self.is_connected = False
        
        self._build_ui()
        logger.info(f"{APP_NAME} v{VERSION} started")
        
        if self.is_registered:
            self._check_existing()
    
    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 500) // 2
        y = (self.root.winfo_screenheight() - 700) // 2
        self.root.geometry(f"500x700+{x}+{y}")
    
    def _build_ui(self):
        main = tk.Frame(self.root, bg=COLORS["bg_dark"])
        main.pack(fill="both", expand=True, padx=30, pady=25)
        
        # Header
        tk.Label(main, text="🖥️", font=("Segoe UI", 48), bg=COLORS["bg_dark"]).pack()
        tk.Label(main, text=APP_NAME, font=("Segoe UI", 28, "bold"), fg=COLORS["text"], bg=COLORS["bg_dark"]).pack(pady=(10, 5))
        tk.Label(main, text="Professional kompyuter xizmati", font=("Segoe UI", 11), fg=COLORS["text_muted"], bg=COLORS["bg_dark"]).pack()
        
        # Registered banner
        if self.is_registered and self.rustdesk_id:
            banner = tk.Frame(main, bg="#1a2e1a", padx=16, pady=12)
            banner.pack(fill="x", pady=(20, 0))
            tk.Label(banner, text=f"✓ Siz ro'yxatdan o'tgansiz", font=("Segoe UI", 11, "bold"), fg=COLORS["success"], bg="#1a2e1a").pack(anchor="w")
            tk.Label(banner, text=f"RustDesk ID: {self.rustdesk_id}", font=("Segoe UI", 10), fg="#86efac", bg="#1a2e1a").pack(anchor="w")
        
        # Form
        card = tk.Frame(main, bg=COLORS["bg_card"], padx=25, pady=25)
        card.pack(fill="x", pady=(20, 0))
        
        # Name
        tk.Label(card, text="👤 Ismingiz", font=("Segoe UI", 10, "bold"), fg=COLORS["text_secondary"], bg=COLORS["bg_card"]).pack(anchor="w")
        self.name_var = tk.StringVar(value=self.config.get("name", ""))
        tk.Entry(card, textvariable=self.name_var, font=("Segoe UI", 12), bg=COLORS["bg_input"], fg=COLORS["text"], 
                insertbackground=COLORS["accent"], relief="flat", bd=10).pack(fill="x", pady=(5, 15))
        
        # Phone
        tk.Label(card, text="📱 Telefon raqam", font=("Segoe UI", 10, "bold"), fg=COLORS["text_secondary"], bg=COLORS["bg_card"]).pack(anchor="w")
        self.phone_var = tk.StringVar(value=self.config.get("phone", "+998"))
        tk.Entry(card, textvariable=self.phone_var, font=("Segoe UI", 12), bg=COLORS["bg_input"], fg=COLORS["text"],
                insertbackground=COLORS["accent"], relief="flat", bd=10).pack(fill="x", pady=(5, 15))
        
        # Problem
        tk.Label(card, text="🔧 Muammo turi", font=("Segoe UI", 10, "bold"), fg=COLORS["text_secondary"], bg=COLORS["bg_card"]).pack(anchor="w")
        problems = ["Kompyuter sekin ishlayapti", "Virus tekshirish", "Dastur o'rnatish", "Internet muammosi", "Windows muammosi", "Boshqa"]
        self.problem_var = tk.StringVar(value=problems[0])
        ttk.Combobox(card, textvariable=self.problem_var, values=problems, font=("Segoe UI", 11), state="readonly").pack(fill="x", pady=(5, 20))
        
        # Button
        self.btn = GradientButton(card, "🚀 Yordam so'rash" if not self.is_registered else "🔄 Qayta ulanish", self._on_submit)
        self.btn.pack()
        
        # Progress & Status
        self.progress = ProgressBar(card, width=360)
        self.status = StatusBadge(card)
        self.status.pack(pady=(20, 0))
        
        # Info
        info = tk.Frame(main, bg=COLORS["bg_card"], padx=20, pady=15)
        info.pack(fill="x", pady=(20, 0))
        tk.Label(info, text="ℹ️ Qanday ishlaydi?", font=("Segoe UI", 11, "bold"), fg=COLORS["accent_light"], bg=COLORS["bg_card"]).pack(anchor="w")
        for s in ["1. Ma'lumotlaringizni kiriting", "2. \"Yordam so'rash\" tugmasini bosing", "3. RustDesk avtomatik sozlanadi", "4. Mutaxassis kompyuteringizga ulanadi"]:
            tk.Label(info, text=s, font=("Segoe UI", 9), fg=COLORS["text_muted"], bg=COLORS["bg_card"]).pack(anchor="w")
        
        # Footer
        tk.Label(main, text=f"v{VERSION} • Telegram: @ustajonbot", font=("Segoe UI", 9), fg=COLORS["text_muted"], bg=COLORS["bg_dark"]).pack(side="bottom")
    
    def _check_existing(self):
        def check():
            try:
                phone = self.config.get("phone", "")
                if phone:
                    data = urllib.parse.urlencode({"phone": phone}).encode()
                    req = urllib.request.Request(f"{SERVER_URL}/api/client/check", data=data, method="POST")
                    req.add_header("Content-Type", "application/x-www-form-urlencoded")
                    resp = urllib.request.urlopen(req, timeout=10)
                    result = json.loads(resp.read().decode())
                    if result.get("exists") and result.get("active"):
                        self.is_connected = True
                        self._start_heartbeat()
            except:
                pass
        threading.Thread(target=check, daemon=True).start()
    
    def _on_submit(self):
        name = self.name_var.get().strip()
        phone = self.phone_var.get().strip()
        
        if not name or len(name) < 2:
            messagebox.showerror("Xatolik", "Ismingizni kiriting!")
            return
        if not phone or len(phone) < 12 or not phone.startswith("+998"):
            messagebox.showerror("Xatolik", "Telefon: +998XXXXXXXXX formatida")
            return
        
        self.client_id = hashlib.md5(phone.encode()).hexdigest()[:12].upper()
        self.btn.set_enabled(False)
        self.btn.set_text("⏳ Kutib turing...")
        self.progress.pack(pady=(15, 0))
        self.progress.start()
        
        threading.Thread(target=self._setup, args=(name, phone), daemon=True).start()
    
    def _update_status(self, s, t):
        self.root.after(0, lambda: self.status.set(s, t))
    
    def _setup(self, name, phone):
        try:
            # Find RustDesk
            self._update_status("loading", "RustDesk tekshirilmoqda...")
            rustdesk = self._find_rustdesk()
            
            if not rustdesk:
                self._update_status("loading", "RustDesk yuklanmoqda...")
                rustdesk = self._download_rustdesk()
                if not rustdesk:
                    raise Exception("RustDesk yuklab bo'lmadi")
            
            # Configure
            self._update_status("loading", "Sozlanmoqda...")
            self._configure_rustdesk(rustdesk)
            time.sleep(3)
            
            # Get ID - MUHIM!
            self._update_status("loading", "ID olinmoqda...")
            self.rustdesk_id = self._get_rustdesk_id()
            logger.info(f"RustDesk ID: {self.rustdesk_id}")
            
            if not self.rustdesk_id or len(self.rustdesk_id) < 6:
                raise Exception("RustDesk ID olinmadi")
            
            # Register
            self._update_status("loading", "Serverga ulanmoqda...")
            result = self._register(name, phone)
            
            if result.get("success"):
                self.config.set("name", name)
                self.config.set("phone", phone)
                self.config.set("client_id", self.client_id)
                self.config.set("rustdesk_id", self.rustdesk_id)
                self.config.set("registered", True)
                
                self._update_status("success", "Muvaffaqiyatli!")
                self.is_registered = True
                self.is_connected = True
                self.root.after(0, self._show_success)
                self._start_heartbeat()
            else:
                raise Exception(result.get("message", "Xatolik"))
                
        except Exception as e:
            logger.error(f"Error: {e}")
            self._update_status("error", str(e)[:50])
            self.root.after(0, self._reset)
    
    def _find_rustdesk(self):
        paths = [
            os.path.expandvars(r"%ProgramFiles%\RustDesk\rustdesk.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\RustDesk\rustdesk.exe"),
            r"C:\Program Files\RustDesk\rustdesk.exe",
        ]
        for p in paths:
            if os.path.exists(p):
                return p
        return None
    
    def _download_rustdesk(self):
        try:
            temp = os.path.join(os.environ.get("TEMP", "."), "rustdesk_setup.exe")
            urllib.request.urlretrieve(RUSTDESK_URL, temp)
            subprocess.run([temp, "--silent-install"], capture_output=True, timeout=180,
                          creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            time.sleep(5)
            return self._find_rustdesk()
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    def _configure_rustdesk(self, path):
        cfg_dir = os.path.join(os.environ.get("APPDATA", "."), "RustDesk", "config")
        os.makedirs(cfg_dir, exist_ok=True)
        
        config = f'''rendezvous_server = "{RUSTDESK_SERVER}"
nat_type = 1
serial = 0

[options]
custom-rendezvous-server = "{RUSTDESK_SERVER}"
relay-server = "{RUSTDESK_SERVER}"
key = "{RUSTDESK_KEY}"
direct-server = "Y"
'''
        with open(os.path.join(cfg_dir, "RustDesk2.toml"), "w") as f:
            f.write(config)
        
        try:
            subprocess.run([path, "--password", RUSTDESK_PASSWORD], capture_output=True, timeout=30,
                          creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except:
            pass
        
        # RustDesk ni ishga tushirish
        subprocess.Popen([path], creationflags=0x08000000)
    
    def _get_rustdesk_id(self):
        """RustDesk ID ni bir necha usulda olish"""
        appdata = os.environ.get("APPDATA", "")
        
        # Usul 1: RustDesk.toml dan
        toml_path = os.path.join(appdata, "RustDesk", "config", "RustDesk.toml")
        for attempt in range(20):
            try:
                if os.path.exists(toml_path):
                    with open(toml_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    # id = '123456789' yoki id = "123456789" formatini qidirish
                    match = re.search(r"^id\s*=\s*['\"]?(\d{9,})['\"]?", content, re.MULTILINE)
                    if match:
                        return match.group(1)
                    # enc_id mavjud bo'lsa
                    if "enc_id" in content:
                        logger.info("enc_id topildi, RustDesk yangi versiya")
            except Exception as e:
                logger.warning(f"TOML read error: {e}")
            time.sleep(0.5)
        
        # Usul 2: id2.txt dan (yangi RustDesk versiyalari)
        id2_path = os.path.join(appdata, "RustDesk", "config", "id2.txt")
        try:
            if os.path.exists(id2_path):
                with open(id2_path, "r") as f:
                    id_val = f.read().strip()
                if id_val and len(id_val) >= 6:
                    return id_val
        except:
            pass
        
        # Usul 3: RustDesk --get-id buyrug'i
        rustdesk = self._find_rustdesk()
        if rustdesk:
            try:
                result = subprocess.run([rustdesk, "--get-id"], capture_output=True, text=True, timeout=10,
                                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                if result.stdout:
                    id_val = result.stdout.strip()
                    if id_val and len(id_val) >= 6 and id_val.isdigit():
                        return id_val
            except:
                pass
        
        # Usul 4: Config papkasidagi barcha fayllarni tekshirish
        config_dir = os.path.join(appdata, "RustDesk", "config")
        if os.path.exists(config_dir):
            for fname in os.listdir(config_dir):
                fpath = os.path.join(config_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    # 9+ raqamli ID qidirish
                    match = re.search(r'\b(\d{9,12})\b', content)
                    if match:
                        return match.group(1)
                except:
                    pass
        
        logger.error("RustDesk ID topilmadi!")
        return None
    
    def _register(self, name, phone):
        try:
            data = {
                "client_id": self.client_id,
                "name": name,
                "phone": phone,
                "problem": self.problem_var.get(),
                "rustdesk_id": self.rustdesk_id,
                "hostname": socket.gethostname(),
                "os_info": f"{platform.system()} {platform.release()}",
                "version": VERSION
            }
            encoded = urllib.parse.urlencode(data).encode()
            req = urllib.request.Request(f"{SERVER_URL}/api/agent/register", data=encoded, method="POST")
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            resp = urllib.request.urlopen(req, timeout=30)
            return json.loads(resp.read().decode())
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _show_success(self):
        self.progress.stop()
        self.progress.pack_forget()
        self.btn.set_gradient(("10b981", "34d399"))
        self.btn.set_text("✓ Ulangan")
        
        messagebox.showinfo("Muvaffaqiyat!", 
            f"🎉 Ro'yxatdan o'tdingiz!\n\n"
            f"🔑 RustDesk ID: {self.rustdesk_id}\n"
            f"🔐 Parol: {RUSTDESK_PASSWORD}\n\n"
            f"Mutaxassis tez orada ulanadi.\n"
            f"Dasturni yopmang!\n\n"
            f"📱 Telegram: @ustajonbot")
    
    def _reset(self):
        self.progress.stop()
        self.progress.pack_forget()
        self.btn.set_gradient(("6366f1", "8b5cf6"))
        self.btn.set_text("🚀 Yordam so'rash")
        self.btn.set_enabled(True)
    
    def _start_heartbeat(self):
        def loop():
            while self.is_connected:
                try:
                    data = urllib.parse.urlencode({
                        "client_id": self.client_id,
                        "rustdesk_id": self.rustdesk_id,
                        "status": "online"
                    }).encode()
                    req = urllib.request.Request(f"{SERVER_URL}/api/agent/heartbeat", data=data, method="POST")
                    req.add_header("Content-Type", "application/x-www-form-urlencoded")
                    resp = urllib.request.urlopen(req, timeout=10)
                    result = json.loads(resp.read().decode())
                    if result.get("deleted"):
                        self.is_connected = False
                        self.config.set("registered", False)
                        self.root.after(0, lambda: messagebox.showinfo("Ma'lumot", "Muammongiz hal qilindi!"))
                        self.root.after(0, self._reset)
                        break
                except:
                    pass
                time.sleep(30)
        threading.Thread(target=loop, daemon=True).start()
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()
    
    def _on_close(self):
        if self.is_connected:
            if messagebox.askyesno("Chiqish", "Dasturni yopmoqchimisiz?"):
                self.root.destroy()
        else:
            self.root.destroy()


def check_single():
    lock = os.path.join(os.environ.get("TEMP", "."), "ustajon.lock")
    try:
        if os.path.exists(lock):
            with open(lock) as f:
                pid = f.read().strip()
            try:
                result = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
                if pid in result.stdout:
                    messagebox.showwarning(APP_NAME, "Dastur allaqachon ishlamoqda!")
                    return False
            except:
                pass
        with open(lock, "w") as f:
            f.write(str(os.getpid()))
        return True
    except:
        return True


if __name__ == "__main__":
    if check_single():
        app = UstajonSupportApp()
        app.run()
