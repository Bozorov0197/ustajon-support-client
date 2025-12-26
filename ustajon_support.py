#!/usr/bin/env python3
"""
UstajonSupport Client v3.0 - Professional Windows Application
Modern glassmorphism UI with full functionality
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
from tkinter import ttk, messagebox, font as tkfont
import uuid
import hashlib
import logging
from datetime import datetime
import ctypes

# ============ CONSTANTS ============
VERSION = "3.0.0"
APP_NAME = "UstajonSupport"
SERVER_URL = "http://31.220.75.75"
RUSTDESK_KEY = "YHo+N4vp+ZWP7wedLh69zCGk3aFf4935hwDKX9OdFXE="
RUSTDESK_SERVER = "31.220.75.75"
RUSTDESK_PASSWORD = "ustajon2025"
RUSTDESK_URL = "https://github.com/rustdesk/rustdesk/releases/download/1.2.3/rustdesk-1.2.3-x86_64.exe"

# Colors - Modern Dark Theme
COLORS = {
    "bg_dark": "#0a0a0f",
    "bg_card": "#12121a",
    "bg_input": "#1a1a25",
    "bg_hover": "#252535",
    "accent": "#6366f1",
    "accent_light": "#818cf8",
    "accent_glow": "#4f46e5",
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "text": "#ffffff",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "border": "#2d2d3d",
    "border_focus": "#6366f1"
}

# App Data Directory
APP_DATA = os.path.join(os.environ.get("APPDATA", "."), APP_NAME)
os.makedirs(APP_DATA, exist_ok=True)
CONFIG_FILE = os.path.join(APP_DATA, "config.json")
LOG_FILE = os.path.join(APP_DATA, "app.log")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Config:
    """Local configuration manager"""
    def __init__(self):
        self.data = self._load()
    
    def _load(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Config load error: {e}")
        return {}
    
    def save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Config save error: {e}")
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def set(self, key, value):
        self.data[key] = value
        self.save()


class GradientButton(tk.Canvas):
    """Modern gradient button with hover effects"""
    def __init__(self, parent, text, command, width=360, height=52, 
                 gradient=("6366f1", "8b5cf6"), **kwargs):
        super().__init__(parent, width=width, height=height, 
                        bg=COLORS["bg_card"], highlightthickness=0, **kwargs)
        self.text = text
        self.command = command
        self.width = width
        self.height = height
        self.gradient = gradient
        self.enabled = True
        self.hover = False
        
        self._draw()
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<ButtonRelease-1>", self._on_release)
        
    def _draw(self):
        self.delete("all")
        
        # Draw gradient background
        r = 14  # border radius
        if self.enabled:
            c1, c2 = self.gradient if not self.hover else ("818cf8", "a78bfa")
        else:
            c1, c2 = ("4b5563", "6b7280")
        
        # Simple gradient simulation with two colors
        self.create_polygon(
            r, 0, self.width-r, 0,
            self.width, r, self.width, self.height-r,
            self.width-r, self.height, r, self.height,
            0, self.height-r, 0, r,
            fill=f"#{c1}", outline="", smooth=True
        )
        
        # Add glow effect on hover
        if self.hover and self.enabled:
            self.create_polygon(
                r+2, 2, self.width-r-2, 2,
                self.width-2, r+2, self.width-2, self.height-r-2,
                self.width-r-2, self.height-2, r+2, self.height-2,
                2, self.height-r-2, 2, r+2,
                fill="", outline=f"#{c2}", width=2, smooth=True
            )
        
        # Text
        self.create_text(
            self.width//2, self.height//2,
            text=self.text, fill="#ffffff",
            font=("Segoe UI", 13, "bold")
        )
        
    def _on_enter(self, e):
        if self.enabled:
            self.hover = True
            self._draw()
            self.config(cursor="hand2")
    
    def _on_leave(self, e):
        self.hover = False
        self._draw()
        self.config(cursor="")
    
    def _on_click(self, e):
        if self.enabled:
            self.config(cursor="hand2")
    
    def _on_release(self, e):
        if self.enabled and self.command:
            self.command()
    
    def set_text(self, text):
        self.text = text
        self._draw()
    
    def set_enabled(self, enabled):
        self.enabled = enabled
        self._draw()
    
    def set_gradient(self, gradient):
        self.gradient = gradient
        self._draw()


class ModernEntry(tk.Frame):
    """Modern entry with icon and floating label effect"""
    def __init__(self, parent, label, icon="", placeholder="", **kwargs):
        super().__init__(parent, bg=COLORS["bg_card"])
        
        self.label_text = label
        self.placeholder = placeholder
        
        # Label
        tk.Label(self, text=f"{icon} {label}" if icon else label,
                font=("Segoe UI", 10, "bold"), fg=COLORS["text_secondary"],
                bg=COLORS["bg_card"]).pack(anchor="w", pady=(0, 6))
        
        # Entry container
        self.entry_frame = tk.Frame(self, bg=COLORS["bg_input"], 
                                   highlightthickness=2,
                                   highlightbackground=COLORS["border"],
                                   highlightcolor=COLORS["accent"])
        self.entry_frame.pack(fill="x")
        
        # Entry
        self.var = tk.StringVar()
        self.entry = tk.Entry(
            self.entry_frame, textvariable=self.var,
            font=("Segoe UI", 12), bg=COLORS["bg_input"],
            fg=COLORS["text"], insertbackground=COLORS["accent"],
            relief="flat", bd=12
        )
        self.entry.pack(fill="x", padx=2, pady=2)
        
        # Placeholder
        if placeholder:
            self.var.set(placeholder)
            self.entry.bind("<FocusIn>", self._on_focus_in)
            self.entry.bind("<FocusOut>", self._on_focus_out)
    
    def _on_focus_in(self, e):
        if self.var.get() == self.placeholder:
            self.var.set("")
            self.entry.config(fg=COLORS["text"])
    
    def _on_focus_out(self, e):
        if not self.var.get():
            self.var.set(self.placeholder)
            self.entry.config(fg=COLORS["text_muted"])
    
    def get(self):
        val = self.var.get()
        return "" if val == self.placeholder else val
    
    def set(self, value):
        self.var.set(value)
        if value and value != self.placeholder:
            self.entry.config(fg=COLORS["text"])


class ModernCombobox(tk.Frame):
    """Modern styled combobox"""
    def __init__(self, parent, label, values, icon=""):
        super().__init__(parent, bg=COLORS["bg_card"])
        
        # Label
        tk.Label(self, text=f"{icon} {label}" if icon else label,
                font=("Segoe UI", 10, "bold"), fg=COLORS["text_secondary"],
                bg=COLORS["bg_card"]).pack(anchor="w", pady=(0, 6))
        
        # Combobox container
        container = tk.Frame(self, bg=COLORS["bg_input"],
                           highlightthickness=2,
                           highlightbackground=COLORS["border"],
                           highlightcolor=COLORS["accent"])
        container.pack(fill="x")
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Modern.TCombobox",
                       fieldbackground=COLORS["bg_input"],
                       background=COLORS["bg_input"],
                       foreground=COLORS["text"],
                       arrowcolor=COLORS["accent"],
                       borderwidth=0,
                       relief="flat")
        style.map("Modern.TCombobox",
                 fieldbackground=[("readonly", COLORS["bg_input"])],
                 selectbackground=[("readonly", COLORS["accent"])],
                 selectforeground=[("readonly", "#ffffff")])
        
        self.var = tk.StringVar(value=values[0] if values else "")
        self.combo = ttk.Combobox(
            container, textvariable=self.var, values=values,
            font=("Segoe UI", 11), style="Modern.TCombobox",
            state="readonly"
        )
        self.combo.pack(fill="x", padx=8, pady=10)
    
    def get(self):
        return self.var.get()


class ProgressIndicator(tk.Canvas):
    """Animated progress indicator"""
    def __init__(self, parent, width=300, height=4):
        super().__init__(parent, width=width, height=height,
                        bg=COLORS["bg_card"], highlightthickness=0)
        self.width = width
        self.height = height
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
        
        # Background
        self.create_rectangle(0, 0, self.width, self.height,
                            fill=COLORS["bg_input"], outline="")
        
        # Moving gradient bar
        bar_width = 100
        x = (self.pos % (self.width + bar_width)) - bar_width
        
        # Create gradient effect
        for i in range(bar_width):
            alpha = 1 - abs(i - bar_width/2) / (bar_width/2)
            color = self._blend_color(COLORS["bg_input"], COLORS["accent"], alpha)
            self.create_line(x + i, 0, x + i, self.height, fill=color)
        
        self.pos += 4
        self.after(20, self._animate)
    
    def _blend_color(self, c1, c2, alpha):
        c1 = c1.lstrip('#')
        c2 = c2.lstrip('#')
        r = int(int(c1[0:2], 16) * (1-alpha) + int(c2[0:2], 16) * alpha)
        g = int(int(c1[2:4], 16) * (1-alpha) + int(c2[2:4], 16) * alpha)
        b = int(int(c1[4:6], 16) * (1-alpha) + int(c2[4:6], 16) * alpha)
        return f"#{r:02x}{g:02x}{b:02x}"


class StatusBadge(tk.Frame):
    """Status indicator badge"""
    def __init__(self, parent, text="Tayyor", status="default"):
        super().__init__(parent, bg=COLORS["bg_card"])
        
        self.dot = tk.Canvas(self, width=10, height=10, 
                            bg=COLORS["bg_card"], highlightthickness=0)
        self.dot.pack(side="left", padx=(0, 8))
        
        self.label = tk.Label(self, text=text, font=("Segoe UI", 10),
                             fg=COLORS["text_secondary"], bg=COLORS["bg_card"])
        self.label.pack(side="left")
        
        self.set_status(status, text)
    
    def set_status(self, status, text=None):
        colors = {
            "default": COLORS["text_muted"],
            "loading": COLORS["warning"],
            "success": COLORS["success"],
            "error": COLORS["error"],
            "online": COLORS["success"]
        }
        color = colors.get(status, COLORS["text_muted"])
        
        self.dot.delete("all")
        self.dot.create_oval(1, 1, 9, 9, fill=color, outline="")
        
        if text:
            self.label.config(text=text, fg=color)


class UstajonSupportApp:
    """Main Application"""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{VERSION}")
        self.root.geometry("520x720")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS["bg_dark"])
        
        # Center window
        self._center_window()
        
        # Try to set DPI awareness on Windows
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        
        # Config
        self.config = Config()
        
        # State
        self.client_id = None
        self.rustdesk_id = self.config.get("rustdesk_id")
        self.is_registered = self.config.get("registered", False)
        self.is_connected = False
        self.heartbeat_thread = None
        
        # Build UI
        self._build_ui()
        
        logger.info(f"{APP_NAME} v{VERSION} started")
        
        # Check existing registration
        if self.is_registered:
            self._check_existing()
    
    def _center_window(self):
        self.root.update_idletasks()
        w, h = 520, 720
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
    
    def _build_ui(self):
        # Main container
        main = tk.Frame(self.root, bg=COLORS["bg_dark"])
        main.pack(fill="both", expand=True, padx=30, pady=25)
        
        # === HEADER ===
        header = tk.Frame(main, bg=COLORS["bg_dark"])
        header.pack(fill="x", pady=(0, 20))
        
        # Logo
        logo_frame = tk.Frame(header, bg=COLORS["bg_dark"])
        logo_frame.pack()
        
        logo = tk.Canvas(logo_frame, width=90, height=90, 
                        bg=COLORS["bg_dark"], highlightthickness=0)
        logo.pack()
        
        # Draw logo with gradient effect
        logo.create_oval(5, 5, 85, 85, fill=COLORS["accent"], outline="")
        logo.create_oval(10, 10, 80, 80, fill=COLORS["bg_dark"], outline="")
        logo.create_oval(15, 15, 75, 75, fill=COLORS["accent"], outline="")
        logo.create_text(45, 45, text="U", font=("Segoe UI", 32, "bold"),
                        fill="#ffffff")
        
        # Title
        tk.Label(header, text=APP_NAME, font=("Segoe UI", 28, "bold"),
                fg=COLORS["text"], bg=COLORS["bg_dark"]).pack(pady=(15, 4))
        tk.Label(header, text="Professional kompyuter xizmati",
                font=("Segoe UI", 11), fg=COLORS["text_muted"],
                bg=COLORS["bg_dark"]).pack()
        
        # === REGISTERED BANNER ===
        if self.is_registered and self.rustdesk_id:
            banner = tk.Frame(main, bg="#1a2e1a", padx=16, pady=12)
            banner.pack(fill="x", pady=(0, 15))
            
            tk.Label(banner, text="✓ Siz ro'yxatdan o'tgansiz",
                    font=("Segoe UI", 11, "bold"), fg=COLORS["success"],
                    bg="#1a2e1a").pack(anchor="w")
            tk.Label(banner, text=f"RustDesk ID: {self.rustdesk_id}",
                    font=("Segoe UI", 10), fg="#86efac",
                    bg="#1a2e1a").pack(anchor="w")
        
        # === FORM CARD ===
        card = tk.Frame(main, bg=COLORS["bg_card"], padx=25, pady=25)
        card.pack(fill="x")
        
        # Name input
        self.name_entry = ModernEntry(card, "Ismingiz", icon="👤", 
                                      placeholder="To'liq ismingiz")
        self.name_entry.pack(fill="x", pady=(0, 18))
        
        # Load saved name
        if self.config.get("name"):
            self.name_entry.set(self.config.get("name"))
        
        # Phone input
        self.phone_entry = ModernEntry(card, "Telefon raqam", icon="📱",
                                       placeholder="+998")
        self.phone_entry.pack(fill="x", pady=(0, 18))
        
        # Load saved phone
        if self.config.get("phone"):
            self.phone_entry.set(self.config.get("phone"))
        else:
            self.phone_entry.set("+998")
        
        # Problem selector
        problems = [
            "💻 Kompyuter sekin ishlayapti",
            "🦠 Virus tekshirish",
            "📦 Dastur o'rnatish",
            "🌐 Internet muammosi",
            "🪟 Windows muammosi",
            "📄 Office dasturlari",
            "🖨️ Printer sozlash",
            "❓ Boshqa muammo"
        ]
        self.problem_combo = ModernCombobox(card, "Muammo turi", problems, icon="🔧")
        self.problem_combo.pack(fill="x", pady=(0, 25))
        
        # Submit button
        btn_text = "🔄 Qayta ulanish" if self.is_registered else "🚀 Yordam so'rash"
        self.submit_btn = GradientButton(card, btn_text, self._on_submit)
        self.submit_btn.pack()
        
        # Progress
        self.progress = ProgressIndicator(card, width=360)
        
        # Status
        status_frame = tk.Frame(card, bg=COLORS["bg_card"])
        status_frame.pack(fill="x", pady=(20, 0))
        self.status = StatusBadge(status_frame, "Tayyor", "default")
        self.status.pack()
        
        # === INFO SECTION ===
        info = tk.Frame(main, bg=COLORS["bg_card"], padx=20, pady=18)
        info.pack(fill="x", pady=(20, 0))
        
        tk.Label(info, text="ℹ️ Qanday ishlaydi?", font=("Segoe UI", 11, "bold"),
                fg=COLORS["accent_light"], bg=COLORS["bg_card"]).pack(anchor="w")
        
        steps = [
            "1. Ma'lumotlaringizni kiriting",
            "2. \"Yordam so'rash\" tugmasini bosing",
            "3. RustDesk avtomatik sozlanadi",
            "4. Mutaxassis kompyuteringizga ulanadi"
        ]
        for step in steps:
            tk.Label(info, text=step, font=("Segoe UI", 9),
                    fg=COLORS["text_muted"], bg=COLORS["bg_card"]).pack(anchor="w", pady=1)
        
        # === FOOTER ===
        footer = tk.Frame(main, bg=COLORS["bg_dark"])
        footer.pack(side="bottom", fill="x", pady=(20, 0))
        
        tk.Label(footer, text=f"v{VERSION} • Telegram: @ustajonbot",
                font=("Segoe UI", 9), fg=COLORS["text_muted"],
                bg=COLORS["bg_dark"]).pack()
    
    def _check_existing(self):
        """Check if still registered on server"""
        def check():
            try:
                phone = self.config.get("phone", "")
                if not phone:
                    return
                
                data = urllib.parse.urlencode({"phone": phone}).encode()
                req = urllib.request.Request(f"{SERVER_URL}/api/client/check",
                                            data=data, method="POST")
                req.add_header("Content-Type", "application/x-www-form-urlencoded")
                
                resp = urllib.request.urlopen(req, timeout=10)
                result = json.loads(resp.read().decode())
                
                if result.get("exists") and result.get("active"):
                    self.is_connected = True
                    self.root.after(0, lambda: self.status.set_status("online", "Online"))
                    self._start_heartbeat()
                elif result.get("exists") and not result.get("active"):
                    self.config.set("registered", False)
                    self.is_registered = False
                    self.root.after(0, lambda: messagebox.showinfo("Ma'lumot",
                        "Oldingi so'rovingiz yakunlangan.\nYangi muammo bo'lsa qayta murojaat qiling."))
                    
            except Exception as e:
                logger.warning(f"Check existing error: {e}")
        
        threading.Thread(target=check, daemon=True).start()
    
    def _on_submit(self):
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        
        # Validation
        if not name or len(name) < 2:
            messagebox.showerror("Xatolik", "Ismingizni kiriting!")
            return
        
        if not phone or len(phone) < 12 or not phone.startswith("+998"):
            messagebox.showerror("Xatolik", 
                "Telefon raqamni to'g'ri kiriting!\nMasalan: +998901234567")
            return
        
        # Generate client_id from phone (consistent)
        self.client_id = hashlib.md5(phone.encode()).hexdigest()[:12].upper()
        
        # Disable button
        self.submit_btn.set_enabled(False)
        self.submit_btn.set_text("⏳ Kutib turing...")
        self.progress.pack(pady=(15, 0))
        self.progress.start()
        
        logger.info(f"Starting support request: {name}, {phone}, client_id={self.client_id}")
        
        # Start setup in background
        threading.Thread(target=self._setup_process, args=(name, phone), daemon=True).start()
    
    def _update_status(self, status, text):
        self.root.after(0, lambda: self.status.set_status(status, text))
    
    def _setup_process(self, name, phone):
        try:
            # Step 1: Find RustDesk
            self._update_status("loading", "RustDesk tekshirilmoqda...")
            rustdesk_path = self._find_rustdesk()
            was_installed = rustdesk_path is not None
            
            # Step 2: Download if needed
            if not rustdesk_path:
                self._update_status("loading", "RustDesk yuklanmoqda...")
                rustdesk_path = self._download_rustdesk()
                if not rustdesk_path:
                    raise Exception("RustDesk yuklab bo'lmadi")
            else:
                self._update_status("loading", "RustDesk topildi, sozlanmoqda...")
            
            # Step 3: Configure
            self._update_status("loading", "Sozlanmoqda...")
            self._configure_rustdesk(rustdesk_path)
            
            # Step 4: Get ID
            self._update_status("loading", "ID olinmoqda...")
            time.sleep(3 if was_installed else 5)
            self.rustdesk_id = self._get_rustdesk_id()
            logger.info(f"RustDesk ID: {self.rustdesk_id}")
            
            # Step 5: Register
            self._update_status("loading", "Serverga ulanmoqda...")
            result = self._register(name, phone)
            
            if result.get("success"):
                # Save config
                self.config.set("name", name)
                self.config.set("phone", phone)
                self.config.set("client_id", self.client_id)
                self.config.set("rustdesk_id", self.rustdesk_id)
                self.config.set("registered", True)
                self.config.set("registered_at", datetime.now().isoformat())
                
                self._update_status("success", "Muvaffaqiyatli ulandi!")
                self.is_registered = True
                self.is_connected = True
                
                self.root.after(0, self._show_success)
                self._start_heartbeat()
            else:
                raise Exception(result.get("message", "Server xatoligi"))
                
        except Exception as e:
            logger.error(f"Setup error: {e}")
            self._update_status("error", f"Xatolik: {str(e)[:50]}")
            self.root.after(0, self._reset_button)
    
    def _find_rustdesk(self):
        paths = [
            os.path.expandvars(r"%ProgramFiles%\RustDesk\rustdesk.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\RustDesk\rustdesk.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\RustDesk\rustdesk.exe"),
            r"C:\Program Files\RustDesk\rustdesk.exe",
        ]
        for p in paths:
            if os.path.exists(p):
                logger.info(f"RustDesk found: {p}")
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
            subprocess.run([path, "--password", RUSTDESK_PASSWORD], 
                          capture_output=True, timeout=30,
                          creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except:
            pass
        
        subprocess.Popen([path], creationflags=0x08000000)
        logger.info("RustDesk configured and started")
    
    def _get_rustdesk_id(self):
        cfg = os.path.join(os.environ.get("APPDATA", "."), "RustDesk", "config", "RustDesk.toml")
        
        for _ in range(15):
            try:
                if os.path.exists(cfg):
                    with open(cfg, "r") as f:
                        for line in f:
                            if line.strip().startswith("id"):
                                id_val = line.split("=")[1].strip().strip("'\"")
                                if id_val and len(id_val) >= 6:
                                    return id_val
            except:
                pass
            time.sleep(1)
        
        return str(uuid.uuid4())[:9].upper()
    
    def _register(self, name, phone):
        try:
            data = {
                "client_id": self.client_id,
                "name": name,
                "phone": phone,
                "problem": self.problem_combo.get(),
                "rustdesk_id": self.rustdesk_id,
                "hostname": socket.gethostname(),
                "os_info": f"{platform.system()} {platform.release()}",
                "version": VERSION,
                "ip": self._get_local_ip()
            }
            
            encoded = urllib.parse.urlencode(data).encode()
            req = urllib.request.Request(f"{SERVER_URL}/api/agent/register",
                                        data=encoded, method="POST")
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            req.add_header("User-Agent", f"{APP_NAME}/{VERSION}")
            
            resp = urllib.request.urlopen(req, timeout=30)
            return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return {"success": False, "message": f"HTTP {e.code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "Unknown"
    
    def _show_success(self):
        self.progress.stop()
        self.progress.pack_forget()
        self.submit_btn.set_gradient(("10b981", "34d399"))
        self.submit_btn.set_text("✓ Ulangan")
        
        messagebox.showinfo("Muvaffaqiyat!", 
            f"🎉 Ro'yxatdan o'tdingiz!\n\n"
            f"🔑 RustDesk ID: {self.rustdesk_id}\n"
            f"🔐 Parol: {RUSTDESK_PASSWORD}\n\n"
            f"Mutaxassis tez orada ulanadi.\n"
            f"Dasturni yopmang!\n\n"
            f"📱 Telegram: @ustajonbot")
    
    def _reset_button(self):
        self.progress.stop()
        self.progress.pack_forget()
        self.submit_btn.set_gradient(("6366f1", "8b5cf6"))
        self.submit_btn.set_text("🚀 Yordam so'rash")
        self.submit_btn.set_enabled(True)
    
    def _start_heartbeat(self):
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            return
        
        def heartbeat_loop():
            while self.is_connected:
                try:
                    data = urllib.parse.urlencode({
                        "client_id": self.client_id,
                        "rustdesk_id": self.rustdesk_id,
                        "status": "online",
                        "version": VERSION
                    }).encode()
                    
                    req = urllib.request.Request(f"{SERVER_URL}/api/agent/heartbeat",
                                                data=data, method="POST")
                    req.add_header("Content-Type", "application/x-www-form-urlencoded")
                    
                    resp = urllib.request.urlopen(req, timeout=10)
                    result = json.loads(resp.read().decode())
                    
                    if result.get("deleted"):
                        self.is_connected = False
                        self.config.set("registered", False)
                        self.root.after(0, self._handle_deletion)
                        break
                        
                except Exception as e:
                    logger.warning(f"Heartbeat error: {e}")
                
                time.sleep(30)
        
        self.heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        logger.info("Heartbeat started")
    
    def _handle_deletion(self):
        self.is_registered = False
        self._reset_button()
        self.status.set_status("default", "Tayyor")
        messagebox.showinfo("Ma'lumot",
            "Muammongiz hal qilingan!\n\n"
            "Yangi muammo bo'lsa qayta murojaat qiling.")
    
    def _on_close(self):
        if self.is_connected:
            if messagebox.askyesno("Chiqish",
                "Dasturni yopmoqchimisiz?\n"
                "Mutaxassis ulanishi mumkin bo'lmaydi."):
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()


def check_single_instance():
    lock = os.path.join(os.environ.get("TEMP", "."), "ustajon.lock")
    try:
        if os.path.exists(lock):
            with open(lock) as f:
                pid = f.read().strip()
            try:
                result = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"],
                                       capture_output=True, text=True)
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
    if check_single_instance():
        app = UstajonSupportApp()
        app.run()
