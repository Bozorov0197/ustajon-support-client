#!/usr/bin/env python3
"""
UstajonSupport Client - Windows Desktop Application
Build: pyinstaller --onefile --windowed --name=UstajonSupport ustajon_support.py
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

# ============ SOZLAMALAR ============
SERVER_URL = "http://31.220.75.75"
RUSTDESK_KEY = "YHo+N4vp+ZWP7wedLh69zCGk3aFf4935hwDKX9OdFXE="
RUSTDESK_SERVER = "31.220.75.75"
RUSTDESK_PASSWORD = "ustajon2025"
RUSTDESK_URL = "https://github.com/rustdesk/rustdesk/releases/download/1.2.3/rustdesk-1.2.3-x86_64.exe"

class UstajonSupport:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("UstajonSupport")
        self.root.geometry("450x550")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")
        
        self.name_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.problem_var = tk.StringVar(value="Kompyuter sekin ishlayapti")
        self.status_var = tk.StringVar(value="Tayyor")
        self.rustdesk_id = None
        
        self.create_ui()
        
    def create_ui(self):
        main = tk.Frame(self.root, bg="#1a1a2e")
        main.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Title
        tk.Label(main, text="UstajonSupport", font=("Segoe UI", 24, "bold"),
                fg="#00d4ff", bg="#1a1a2e").pack(pady=(0, 5))
        tk.Label(main, text="Kompyuter yordam xizmati", font=("Segoe UI", 11),
                fg="#888", bg="#1a1a2e").pack(pady=(0, 25))
        
        form = tk.Frame(main, bg="#1a1a2e")
        form.pack(fill="x")
        
        # Name
        tk.Label(form, text="Ismingiz:", font=("Segoe UI", 10),
                fg="#fff", bg="#1a1a2e", anchor="w").pack(fill="x")
        tk.Entry(form, textvariable=self.name_var, font=("Segoe UI", 12),
                bg="#2d2d44", fg="#fff", insertbackground="#fff",
                relief="flat").pack(fill="x", pady=(5, 15), ipady=10)
        
        # Phone
        tk.Label(form, text="Telefon raqam:", font=("Segoe UI", 10),
                fg="#fff", bg="#1a1a2e", anchor="w").pack(fill="x")
        phone = tk.Entry(form, textvariable=self.phone_var, font=("Segoe UI", 12),
                        bg="#2d2d44", fg="#fff", insertbackground="#fff", relief="flat")
        phone.pack(fill="x", pady=(5, 15), ipady=10)
        phone.insert(0, "+998")
        
        # Problem
        tk.Label(form, text="Muammo turi:", font=("Segoe UI", 10),
                fg="#fff", bg="#1a1a2e", anchor="w").pack(fill="x")
        problems = ["Kompyuter sekin", "Virus tekshirish", "Dastur ornatish",
                   "Internet muammo", "Windows muammo", "Boshqa"]
        ttk.Combobox(form, textvariable=self.problem_var, values=problems,
                    font=("Segoe UI", 11), state="readonly").pack(fill="x", pady=(5, 25), ipady=8)
        
        # Button
        self.btn = tk.Button(form, text="Yordam olish", font=("Segoe UI", 14, "bold"),
                            bg="#00d4ff", fg="#000", relief="flat", cursor="hand2",
                            command=self.start_support)
        self.btn.pack(fill="x", pady=(10, 20), ipady=12)
        
        # Status
        self.status = tk.Label(main, textvariable=self.status_var,
                              font=("Segoe UI", 10), fg="#888", bg="#1a1a2e")
        self.status.pack(pady=(10, 0))
        
        self.progress = ttk.Progressbar(main, mode="indeterminate", length=300)
        
        tk.Label(main, text="2025 UstajonSupport", font=("Segoe UI", 8),
                fg="#555", bg="#1a1a2e").pack(side="bottom", pady=(20, 0))
        
    def update_status(self, text, color="#888"):
        self.status_var.set(text)
        self.status.config(fg=color)
        self.root.update()
        
    def start_support(self):
        name = self.name_var.get().strip()
        phone = self.phone_var.get().strip()
        
        if not name:
            messagebox.showerror("Xatolik", "Ismingizni kiriting!")
            return
        if len(phone) < 9:
            messagebox.showerror("Xatolik", "Telefon raqamni kiriting!")
            return
        
        self.btn.config(state="disabled", text="Kutib turing...")
        self.progress.pack(pady=(10, 0))
        self.progress.start(10)
        
        threading.Thread(target=self.setup, args=(name, phone), daemon=True).start()
        
    def setup(self, name, phone):
        try:
            self.update_status("RustDesk tekshirilmoqda...", "#ffaa00")
            rustdesk = self.find_rustdesk()
            
            if not rustdesk:
                self.update_status("RustDesk yuklanmoqda...", "#ffaa00")
                rustdesk = self.download_rustdesk()
            
            self.update_status("Sozlanmoqda...", "#ffaa00")
            self.configure_rustdesk(rustdesk)
            
            self.update_status("ID olinmoqda...", "#ffaa00")
            time.sleep(3)
            self.rustdesk_id = self.get_id()
            
            self.update_status("Serverga ulanmoqda...", "#ffaa00")
            self.register(name, phone)
            
            self.update_status("Tayyor! Admin tez orada ulanadi.", "#00ff00")
            self.progress.stop()
            self.progress.pack_forget()
            self.root.after(0, self.success)
            
        except Exception as e:
            self.update_status(f"Xatolik: {e}", "#ff0000")
            self.progress.stop()
            self.btn.config(state="normal", text="Yordam olish")
            
    def find_rustdesk(self):
        paths = [
            os.path.expandvars(r"%ProgramFiles%\RustDesk\rustdesk.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\RustDesk\rustdesk.exe"),
            r"C:\Program Files\RustDesk\rustdesk.exe"
        ]
        for p in paths:
            if os.path.exists(p):
                return p
        return None
        
    def download_rustdesk(self):
        path = os.path.join(os.environ.get("TEMP", "."), "rustdesk_setup.exe")
        urllib.request.urlretrieve(RUSTDESK_URL, path)
        subprocess.run([path, "--silent-install"], capture_output=True, timeout=120)
        time.sleep(5)
        return self.find_rustdesk()
        
    def configure_rustdesk(self, rustdesk):
        cfg_dir = os.path.join(os.environ.get("APPDATA", "."), "RustDesk", "config")
        os.makedirs(cfg_dir, exist_ok=True)
        
        cfg = f'rendezvous_server = "{RUSTDESK_SERVER}"\n'
        cfg += f'[options]\ncustom-rendezvous-server = "{RUSTDESK_SERVER}"\n'
        cfg += f'relay-server = "{RUSTDESK_SERVER}"\nkey = "{RUSTDESK_KEY}"\n'
        
        with open(os.path.join(cfg_dir, "RustDesk2.toml"), "w") as f:
            f.write(cfg)
        
        subprocess.run([rustdesk, "--password", RUSTDESK_PASSWORD], capture_output=True)
        subprocess.Popen([rustdesk], creationflags=0x08000000)
        
    def get_id(self):
        cfg = os.path.join(os.environ.get("APPDATA", "."), "RustDesk", "config", "RustDesk.toml")
        for _ in range(10):
            if os.path.exists(cfg):
                with open(cfg) as f:
                    for line in f:
                        if line.startswith("id"):
                            return line.split("=")[1].strip().strip("'\"")
            time.sleep(1)
        return str(uuid.uuid4())[:8].upper()
        
    def register(self, name, phone):
        data = urllib.parse.urlencode({
            "name": name, "phone": phone, "problem": self.problem_var.get(),
            "rustdesk_id": self.rustdesk_id, "computer_name": socket.gethostname(),
            "os_info": f"{platform.system()} {platform.release()}"
        }).encode()
        
        req = urllib.request.Request(f"{SERVER_URL}/api/agent/register", data=data)
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        urllib.request.urlopen(req, timeout=30)
        
    def success(self):
        self.btn.config(text="Ulangan", bg="#00aa00")
        messagebox.showinfo("Muvaffaqiyat!", 
            f"RustDesk ID: {self.rustdesk_id}\nParol: {RUSTDESK_PASSWORD}\n\n"
            "Admin tez orada ulanadi.\nTelegram: @ustajonbot")
        self.heartbeat()
        
    def heartbeat(self):
        def beat():
            while True:
                try:
                    data = urllib.parse.urlencode({"rustdesk_id": self.rustdesk_id}).encode()
                    req = urllib.request.Request(f"{SERVER_URL}/api/agent/heartbeat", data=data)
                    urllib.request.urlopen(req, timeout=10)
                except: pass
                time.sleep(60)
        threading.Thread(target=beat, daemon=True).start()
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    UstajonSupport().run()
