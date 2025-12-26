#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        USTAJON SUPPORT AGENT v9.0                            ║
║                    Professional Remote Support System                         ║
║                         © 2025 Ustajon Technologies                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

Features:
    - Professional Windows GUI with modern design
    - RustDesk auto-configuration and management
    - Real-time heartbeat system
    - Remote command execution
    - System information collection
    - Automatic startup registration
    - Secure communication with server
    - Background service mode
    - System tray integration
    - Logging system
    - Auto-update capability
"""

import os
import sys
import json
import time
import uuid
import socket
import hashlib
import logging
import platform
import threading
import subprocess
import webbrowser
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List
import ctypes
from ctypes import wintypes

# ══════════════════════════════════════════════════════════════════════════════
#                              CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

VERSION = "9.0.0"
APP_NAME = "UstajonSupport"
APP_TITLE = "Ustajon Texnik Yordam"
COMPANY_NAME = "Ustajon Technologies"

# Server Configuration
SERVER_URL = "http://31.220.75.75"
API_ENDPOINT = f"{SERVER_URL}/api"

# RustDesk Configuration
RUSTDESK_SERVER = "31.220.75.75"
RUSTDESK_KEY = "YHo+N4vp+ZWP7wedLh69zCGk3aFf4935hwDKX9OdFXE="
RUSTDESK_PASSWORD = "ustajon2025"

# Timing Configuration
HEARTBEAT_INTERVAL = 10  # seconds
COMMAND_CHECK_INTERVAL = 5  # seconds
RUSTDESK_CHECK_INTERVAL = 30  # seconds
UPDATE_CHECK_INTERVAL = 3600  # 1 hour

# Paths
DATA_DIR = Path(os.environ.get('APPDATA', Path.home())) / APP_NAME
CONFIG_FILE = DATA_DIR / "config.json"
LOG_FILE = DATA_DIR / "agent.log"
CACHE_DIR = DATA_DIR / "cache"

# Windows Constants
SW_HIDE = 0
SW_SHOW = 5
CREATE_NO_WINDOW = 0x08000000
DETACHED_PROCESS = 0x00000008

# ══════════════════════════════════════════════════════════════════════════════
#                              LOGGING SETUP
# ══════════════════════════════════════════════════════════════════════════════

def setup_logging():
    """Configure logging system"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(APP_NAME)

logger = setup_logging()

# ══════════════════════════════════════════════════════════════════════════════
#                              UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource for PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def is_admin() -> bool:
    """Check if running with admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Restart the program with admin privileges"""
    if not is_admin():
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit(0)
        except:
            pass

def hide_console():
    """Hide console window"""
    try:
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), SW_HIDE
        )
    except:
        pass

def generate_machine_id() -> str:
    """Generate unique machine identifier"""
    try:
        components = [
            socket.gethostname(),
            str(uuid.getnode()),
            platform.machine(),
            platform.processor()
        ]
        combined = "-".join(components)
        return hashlib.sha256(combined.encode()).hexdigest()[:16].upper()
    except Exception as e:
        logger.error(f"Error generating machine ID: {e}")
        return uuid.uuid4().hex[:16].upper()

# ══════════════════════════════════════════════════════════════════════════════
#                           SYSTEM INFORMATION
# ══════════════════════════════════════════════════════════════════════════════

class SystemInfo:
    """Collect and manage system information"""
    
    @staticmethod
    def get_hostname() -> str:
        try:
            return socket.gethostname()
        except:
            return "Unknown"
    
    @staticmethod
    def get_username() -> str:
        try:
            return os.environ.get('USERNAME', os.environ.get('USER', 'Unknown'))
        except:
            return "Unknown"
    
    @staticmethod
    def get_os_info() -> str:
        try:
            result = subprocess.run(
                ['wmic', 'os', 'get', 'Caption,Version', '/value'],
                capture_output=True, text=True, timeout=15,
                creationflags=CREATE_NO_WINDOW
            )
            info = {}
            for line in result.stdout.split('\n'):
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    info[key] = value
            caption = info.get('Caption', 'Windows')
            version = info.get('Version', '')
            return f"{caption} {version}".strip()
        except Exception as e:
            logger.error(f"Error getting OS info: {e}")
            return f"Windows {platform.release()}"
    
    @staticmethod
    def get_local_ip() -> str:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            sock.close()
            return ip
        except:
            return "127.0.0.1"
    
    @staticmethod
    def get_public_ip() -> str:
        try:
            response = urllib.request.urlopen("https://api.ipify.org", timeout=5)
            return response.read().decode('utf-8')
        except:
            return ""
    
    @staticmethod
    def get_cpu_info() -> str:
        try:
            result = subprocess.run(
                ['wmic', 'cpu', 'get', 'Name', '/value'],
                capture_output=True, text=True, timeout=15,
                creationflags=CREATE_NO_WINDOW
            )
            for line in result.stdout.split('\n'):
                if 'Name=' in line:
                    return line.split('=', 1)[1].strip()
        except:
            pass
        return platform.processor() or "Unknown"
    
    @staticmethod
    def get_ram_info() -> str:
        try:
            result = subprocess.run(
                ['wmic', 'computersystem', 'get', 'TotalPhysicalMemory', '/value'],
                capture_output=True, text=True, timeout=15,
                creationflags=CREATE_NO_WINDOW
            )
            for line in result.stdout.split('\n'):
                if 'TotalPhysicalMemory=' in line:
                    bytes_ram = int(line.split('=', 1)[1].strip())
                    gb_ram = bytes_ram / (1024**3)
                    return f"{gb_ram:.1f} GB"
        except:
            pass
        return "Unknown"
    
    @staticmethod
    def get_disk_info() -> str:
        try:
            result = subprocess.run(
                ['wmic', 'logicaldisk', 'where', 'DriveType=3', 'get', 'Size,FreeSpace', '/value'],
                capture_output=True, text=True, timeout=15,
                creationflags=CREATE_NO_WINDOW
            )
            total = 0
            free = 0
            for line in result.stdout.split('\n'):
                if 'Size=' in line:
                    try:
                        total += int(line.split('=', 1)[1].strip())
                    except:
                        pass
                elif 'FreeSpace=' in line:
                    try:
                        free += int(line.split('=', 1)[1].strip())
                    except:
                        pass
            if total > 0:
                total_gb = total / (1024**3)
                free_gb = free / (1024**3)
                return f"{free_gb:.0f} GB free / {total_gb:.0f} GB total"
        except:
            pass
        return "Unknown"
    
    @staticmethod
    def get_antivirus_info() -> str:
        try:
            result = subprocess.run(
                ['wmic', '/namespace:\\\\root\\SecurityCenter2', 'path', 
                 'AntiVirusProduct', 'get', 'displayName', '/value'],
                capture_output=True, text=True, timeout=15,
                creationflags=CREATE_NO_WINDOW
            )
            products = []
            for line in result.stdout.split('\n'):
                if 'displayName=' in line:
                    name = line.split('=', 1)[1].strip()
                    if name:
                        products.append(name)
            return ", ".join(products) if products else "Not detected"
        except:
            return "Unknown"
    
    @classmethod
    def get_full_info(cls) -> Dict[str, str]:
        return {
            "hostname": cls.get_hostname(),
            "username": cls.get_username(),
            "os_info": cls.get_os_info(),
            "local_ip": cls.get_local_ip(),
            "public_ip": cls.get_public_ip(),
            "cpu": cls.get_cpu_info(),
            "ram": cls.get_ram_info(),
            "disk": cls.get_disk_info(),
            "antivirus": cls.get_antivirus_info()
        }

# ══════════════════════════════════════════════════════════════════════════════
#                           CONFIGURATION MANAGER
# ══════════════════════════════════════════════════════════════════════════════

class ConfigManager:
    """Manage application configuration"""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> None:
        """Load configuration from file"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config = {}
    
    def save(self) -> None:
        """Save configuration to file"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self.config[key] = value
        self.save()
    
    def update(self, data: Dict[str, Any]) -> None:
        self.config.update(data)
        self.save()

# ══════════════════════════════════════════════════════════════════════════════
#                           RUSTDESK MANAGER
# ══════════════════════════════════════════════════════════════════════════════

class RustDeskManager:
    """Manage RustDesk installation and configuration"""
    
    CONFIG_PATHS = [
        Path(os.environ.get('APPDATA', '')) / "RustDesk" / "config" / "RustDesk2.toml",
        Path.home() / "AppData" / "Roaming" / "RustDesk" / "config" / "RustDesk2.toml",
        Path(os.environ.get('PROGRAMDATA', '')) / "RustDesk" / "config" / "RustDesk2.toml",
    ]
    
    EXE_PATHS = [
        Path(os.environ.get('PROGRAMFILES', '')) / "RustDesk" / "rustdesk.exe",
        Path(os.environ.get('PROGRAMFILES(X86)', '')) / "RustDesk" / "rustdesk.exe",
        Path(os.environ.get('LOCALAPPDATA', '')) / "RustDesk" / "rustdesk.exe",
        Path.home() / "AppData" / "Local" / "RustDesk" / "rustdesk.exe",
    ]
    
    DOWNLOAD_URL = "https://github.com/rustdesk/rustdesk/releases/download/1.2.3/rustdesk-1.2.3-x86_64.exe"
    
    def __init__(self):
        self.rustdesk_id: Optional[str] = None
        self.exe_path: Optional[Path] = None
        self.config_path: Optional[Path] = None
    
    def find_executable(self) -> Optional[Path]:
        """Find RustDesk executable"""
        for path in self.EXE_PATHS:
            if path.exists():
                self.exe_path = path
                logger.info(f"Found RustDesk at: {path}")
                return path
        logger.warning("RustDesk executable not found")
        return None
    
    def find_config(self) -> Optional[Path]:
        """Find RustDesk config file"""
        for path in self.CONFIG_PATHS:
            if path.exists():
                self.config_path = path
                logger.info(f"Found RustDesk config at: {path}")
                return path
        return None
    
    def get_id(self) -> Optional[str]:
        """Get RustDesk ID from config"""
        config_path = self.find_config()
        if not config_path:
            return None
        
        try:
            content = config_path.read_text(encoding='utf-8')
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('id') and '=' in line:
                    # Parse: id = 'value' or id = "value" or id = value
                    value = line.split('=', 1)[1].strip().strip("'\"")
                    if value and len(value) >= 6 and value.isdigit():
                        self.rustdesk_id = value
                        logger.info(f"Found RustDesk ID: {value}")
                        return value
        except Exception as e:
            logger.error(f"Error reading RustDesk config: {e}")
        
        return None
    
    def configure(self) -> bool:
        """Configure RustDesk with our server settings"""
        # Find or create config directory
        config_path = self.find_config()
        if not config_path:
            config_path = self.CONFIG_PATHS[0]
        
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read existing config
            existing_config = {}
            if config_path.exists():
                for line in config_path.read_text(encoding='utf-8').split('\n'):
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        existing_config[key.strip()] = value.strip()
            
            # Update with our settings
            existing_config['rendezvous_server'] = f"'{RUSTDESK_SERVER}'"
            existing_config['key'] = f"'{RUSTDESK_KEY}'"
            existing_config['password'] = f"'{RUSTDESK_PASSWORD}'"
            
            # Write config
            with open(config_path, 'w', encoding='utf-8') as f:
                for key, value in existing_config.items():
                    f.write(f"{key} = {value}\n")
            
            self.config_path = config_path
            logger.info("RustDesk configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error configuring RustDesk: {e}")
            return False
    
    def is_running(self) -> bool:
        """Check if RustDesk is running"""
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq rustdesk.exe'],
                capture_output=True, text=True, timeout=10,
                creationflags=CREATE_NO_WINDOW
            )
            return 'rustdesk.exe' in result.stdout.lower()
        except:
            return False
    
    def start(self) -> bool:
        """Start RustDesk"""
        if self.is_running():
            logger.info("RustDesk is already running")
            return True
        
        exe_path = self.find_executable()
        if not exe_path:
            logger.warning("Cannot start RustDesk - executable not found")
            return False
        
        try:
            subprocess.Popen(
                [str(exe_path)],
                creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS
            )
            logger.info("RustDesk started successfully")
            time.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Error starting RustDesk: {e}")
            return False
    
    def restart(self) -> bool:
        """Restart RustDesk"""
        self.stop()
        time.sleep(2)
        return self.start()
    
    def stop(self) -> bool:
        """Stop RustDesk"""
        try:
            subprocess.run(
                ['taskkill', '/F', '/IM', 'rustdesk.exe'],
                capture_output=True, timeout=10,
                creationflags=CREATE_NO_WINDOW
            )
            logger.info("RustDesk stopped")
            return True
        except:
            return False
    
    def download_and_install(self) -> bool:
        """Download and install RustDesk"""
        logger.info("Downloading RustDesk...")
        try:
            installer_path = CACHE_DIR / "rustdesk_installer.exe"
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            
            urllib.request.urlretrieve(self.DOWNLOAD_URL, installer_path)
            
            # Run installer silently
            subprocess.run(
                [str(installer_path), '--silent-install'],
                timeout=120,
                creationflags=CREATE_NO_WINDOW
            )
            
            logger.info("RustDesk installed successfully")
            return True
        except Exception as e:
            logger.error(f"Error installing RustDesk: {e}")
            return False
    
    def initialize(self) -> str:
        """Initialize RustDesk - configure, start, and get ID"""
        # Configure first
        self.configure()
        
        # Start RustDesk
        self.start()
        
        # Wait for ID to be generated
        for attempt in range(15):
            rustdesk_id = self.get_id()
            if rustdesk_id:
                return rustdesk_id
            time.sleep(1)
        
        return self.rustdesk_id or ""

# ══════════════════════════════════════════════════════════════════════════════
#                           HTTP CLIENT
# ══════════════════════════════════════════════════════════════════════════════

class HTTPClient:
    """HTTP client for API communication"""
    
    @staticmethod
    def post(url: str, data: Dict[str, Any], timeout: int = 15) -> Optional[Dict]:
        """Send POST request"""
        try:
            json_data = json.dumps(data).encode('utf-8')
            request = urllib.request.Request(
                url,
                data=json_data,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': f'{APP_NAME}/{VERSION}'
                },
                method='POST'
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP Error: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            logger.error(f"URL Error: {e.reason}")
        except Exception as e:
            logger.error(f"Request error: {e}")
        return None
    
    @staticmethod
    def get(url: str, timeout: int = 15) -> Optional[Dict]:
        """Send GET request"""
        try:
            request = urllib.request.Request(
                url,
                headers={'User-Agent': f'{APP_NAME}/{VERSION}'}
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            logger.error(f"GET request error: {e}")
        return None

# ══════════════════════════════════════════════════════════════════════════════
#                           COMMAND EXECUTOR
# ══════════════════════════════════════════════════════════════════════════════

class CommandExecutor:
    """Execute remote commands safely"""
    
    BLOCKED_COMMANDS = [
        'format', 'del /s', 'rd /s', 'rmdir /s',
        'reg delete', 'bcdedit', 'diskpart'
    ]
    
    @classmethod
    def is_safe(cls, command: str) -> bool:
        """Check if command is safe to execute"""
        cmd_lower = command.lower()
        for blocked in cls.BLOCKED_COMMANDS:
            if blocked in cmd_lower:
                return False
        return True
    
    @classmethod
    def execute(cls, command: str, timeout: int = 120) -> Tuple[bool, str]:
        """Execute command and return result"""
        if not cls.is_safe(command):
            return False, "Command blocked for security reasons"
        
        logger.info(f"Executing command: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=CREATE_NO_WINDOW
            )
            
            output = result.stdout + result.stderr
            output = output[:10000]  # Limit output size
            
            success = result.returncode == 0
            logger.info(f"Command completed with return code: {result.returncode}")
            
            return success, output
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Command timed out: {command}")
            return False, f"Command timed out after {timeout} seconds"
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return False, str(e)

# ══════════════════════════════════════════════════════════════════════════════
#                           STARTUP MANAGER
# ══════════════════════════════════════════════════════════════════════════════

class StartupManager:
    """Manage Windows startup registration"""
    
    REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    @classmethod
    def add_to_startup(cls) -> bool:
        """Add application to Windows startup"""
        try:
            import winreg
            
            # Get executable path
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
            else:
                exe_path = f'pythonw.exe "{os.path.abspath(__file__)}"'
            
            # Open registry key
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                cls.REGISTRY_PATH,
                0,
                winreg.KEY_SET_VALUE
            )
            
            # Set value
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            
            logger.info("Added to Windows startup")
            return True
            
        except Exception as e:
            logger.error(f"Error adding to startup: {e}")
            return False
    
    @classmethod
    def remove_from_startup(cls) -> bool:
        """Remove application from Windows startup"""
        try:
            import winreg
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                cls.REGISTRY_PATH,
                0,
                winreg.KEY_SET_VALUE
            )
            
            winreg.DeleteValue(key, APP_NAME)
            winreg.CloseKey(key)
            
            logger.info("Removed from Windows startup")
            return True
            
        except Exception as e:
            logger.error(f"Error removing from startup: {e}")
            return False
    
    @classmethod
    def is_in_startup(cls) -> bool:
        """Check if application is in Windows startup"""
        try:
            import winreg
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                cls.REGISTRY_PATH,
                0,
                winreg.KEY_READ
            )
            
            try:
                winreg.QueryValueEx(key, APP_NAME)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
                
        except:
            return False

# ══════════════════════════════════════════════════════════════════════════════
#                           AGENT CORE
# ══════════════════════════════════════════════════════════════════════════════

class Agent:
    """Main agent class"""
    
    def __init__(self):
        self.client_id = generate_machine_id()
        self.config = ConfigManager()
        self.rustdesk = RustDeskManager()
        self.system_info = SystemInfo()
        
        self.running = True
        self.connected = False
        self.registered = self.config.get('registered', False)
        self.last_heartbeat = 0
        self.last_command_check = 0
        
        logger.info(f"Agent initialized - ID: {self.client_id}, Version: {VERSION}")
    
    def initialize_rustdesk(self) -> str:
        """Initialize RustDesk and return ID"""
        logger.info("Initializing RustDesk...")
        return self.rustdesk.initialize()
    
    def send_heartbeat(self) -> bool:
        """Send heartbeat to server"""
        try:
            # Get RustDesk ID if not already set
            if not self.rustdesk.rustdesk_id:
                self.rustdesk.get_id()
            
            # Prepare heartbeat data
            data = {
                "client_id": self.client_id,
                "rustdesk_id": self.rustdesk.rustdesk_id or "",
                "hostname": self.system_info.get_hostname(),
                "username": self.system_info.get_username(),
                "os_info": self.system_info.get_os_info(),
                "local_ip": self.system_info.get_local_ip(),
                "version": VERSION,
                "name": self.config.get('name', ''),
                "phone": self.config.get('phone', ''),
                "problem": self.config.get('problem', ''),
                "registered": self.registered
            }
            
            # Send heartbeat
            response = HTTPClient.post(f"{API_ENDPOINT}/heartbeat", data)
            
            if response:
                self.connected = True
                self.last_heartbeat = time.time()
                return True
            else:
                self.connected = False
                return False
                
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            self.connected = False
            return False
    
    def check_commands(self) -> None:
        """Check for pending commands from server"""
        try:
            response = HTTPClient.get(
                f"{API_ENDPOINT}/agent/commands?client_id={self.client_id}"
            )
            
            if not response:
                return
            
            for cmd in response:
                if cmd.get('status') != 'pending':
                    continue
                
                command = cmd.get('command', '')
                command_id = cmd.get('id')
                
                logger.info(f"Executing command {command_id}: {command}")
                
                success, output = CommandExecutor.execute(command)
                
                # Send result back
                HTTPClient.post(f"{API_ENDPOINT}/agent/command-result", {
                    "client_id": self.client_id,
                    "command_id": command_id,
                    "success": success,
                    "output": output
                })
                
                self.last_command_check = time.time()
                
        except Exception as e:
            logger.error(f"Command check error: {e}")
    
    def register_client(self, name: str, phone: str, problem: str) -> bool:
        """Register client with server"""
        try:
            self.config.update({
                'name': name,
                'phone': phone,
                'problem': problem,
                'registered': True,
                'registered_at': datetime.now().isoformat()
            })
            
            self.registered = True
            
            # Send immediate heartbeat
            self.send_heartbeat()
            
            # Add to startup
            StartupManager.add_to_startup()
            
            logger.info(f"Client registered: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False
    
    def heartbeat_loop(self) -> None:
        """Background heartbeat loop"""
        while self.running:
            try:
                self.send_heartbeat()
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
            time.sleep(HEARTBEAT_INTERVAL)
    
    def command_loop(self) -> None:
        """Background command check loop"""
        while self.running:
            try:
                self.check_commands()
            except Exception as e:
                logger.error(f"Command loop error: {e}")
            time.sleep(COMMAND_CHECK_INTERVAL)
    
    def rustdesk_monitor_loop(self) -> None:
        """Monitor RustDesk status"""
        while self.running:
            try:
                # Check if RustDesk is running
                if not self.rustdesk.is_running():
                    logger.warning("RustDesk not running, restarting...")
                    self.rustdesk.start()
                
                # Update ID if needed
                if not self.rustdesk.rustdesk_id:
                    self.rustdesk.get_id()
                    
            except Exception as e:
                logger.error(f"RustDesk monitor error: {e}")
            time.sleep(RUSTDESK_CHECK_INTERVAL)
    
    def start_background_services(self) -> None:
        """Start all background services"""
        # Heartbeat thread
        heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        # Command thread
        command_thread = threading.Thread(target=self.command_loop, daemon=True)
        command_thread.start()
        
        # RustDesk monitor thread
        rustdesk_thread = threading.Thread(target=self.rustdesk_monitor_loop, daemon=True)
        rustdesk_thread.start()
        
        logger.info("Background services started")
    
    def stop(self) -> None:
        """Stop agent"""
        self.running = False
        logger.info("Agent stopped")
    
    def run_gui(self) -> None:
        """Run GUI application"""
        app = AgentGUI(self)
        app.run()
    
    def run_background(self) -> None:
        """Run in background mode without GUI"""
        hide_console()
        self.start_background_services()
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def run(self) -> None:
        """Main entry point"""
        # Initialize RustDesk
        self.initialize_rustdesk()
        
        # Check if already registered
        if self.registered and '--background' in sys.argv:
            self.run_background()
        else:
            self.run_gui()

# ══════════════════════════════════════════════════════════════════════════════
#                           GUI APPLICATION
# ══════════════════════════════════════════════════════════════════════════════

class AgentGUI:
    """Modern GUI for agent"""
    
    # Color scheme
    COLORS = {
        'bg_dark': '#0d1117',
        'bg_secondary': '#161b22',
        'bg_tertiary': '#21262d',
        'border': '#30363d',
        'text_primary': '#ffffff',
        'text_secondary': '#8b949e',
        'accent_green': '#238636',
        'accent_green_hover': '#2ea043',
        'accent_blue': '#58a6ff',
        'accent_yellow': '#d29922',
        'accent_red': '#f85149'
    }
    
    def __init__(self, agent: Agent):
        self.agent = agent
        self.root = None
        self.id_var = None
        self.status_var = None
        self.connection_var = None
    
    def create_window(self) -> None:
        """Create main window"""
        import tkinter as tk
        from tkinter import ttk, messagebox
        
        self.root = tk.Tk()
        self.root.title(f"{APP_TITLE} v{VERSION}")
        self.root.configure(bg=self.COLORS['bg_dark'])
        self.root.resizable(False, False)
        
        # Window size and position
        width, height = 520, 780
        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Icon (if available)
        try:
            icon_path = get_resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        self.create_widgets()
    
    def create_widgets(self) -> None:
        """Create all GUI widgets"""
        import tkinter as tk
        from tkinter import messagebox
        
        # Main container with padding
        main = tk.Frame(self.root, bg=self.COLORS['bg_dark'])
        main.pack(fill='both', expand=True, padx=40, pady=30)
        
        # ═══════════ HEADER ═══════════
        header = tk.Frame(main, bg=self.COLORS['bg_dark'])
        header.pack(fill='x', pady=(0, 20))
        
        # Logo/Icon
        tk.Label(
            header, 
            text="🔧", 
            font=('Segoe UI Emoji', 56),
            bg=self.COLORS['bg_dark'], 
            fg=self.COLORS['accent_green']
        ).pack()
        
        # Title
        tk.Label(
            header,
            text=APP_TITLE,
            font=('Segoe UI', 26, 'bold'),
            bg=self.COLORS['bg_dark'],
            fg=self.COLORS['text_primary']
        ).pack(pady=(5, 0))
        
        # Subtitle
        tk.Label(
            header,
            text="Professional masofaviy yordam xizmati",
            font=('Segoe UI', 11),
            bg=self.COLORS['bg_dark'],
            fg=self.COLORS['text_secondary']
        ).pack(pady=(3, 0))
        
        # ═══════════ STATUS CARD ═══════════
        status_card = tk.Frame(
            main,
            bg=self.COLORS['bg_secondary'],
            highlightbackground=self.COLORS['border'],
            highlightthickness=1
        )
        status_card.pack(fill='x', pady=(0, 20))
        
        status_inner = tk.Frame(status_card, bg=self.COLORS['bg_secondary'])
        status_inner.pack(fill='x', padx=20, pady=15)
        
        # RustDesk ID Section
        tk.Label(
            status_inner,
            text="🖥  RustDesk ID",
            font=('Segoe UI', 11),
            bg=self.COLORS['bg_secondary'],
            fg=self.COLORS['text_secondary']
        ).pack(anchor='w')
        
        self.id_var = tk.StringVar(value="Yuklanmoqda...")
        tk.Label(
            status_inner,
            textvariable=self.id_var,
            font=('Consolas', 24, 'bold'),
            bg=self.COLORS['bg_secondary'],
            fg=self.COLORS['accent_blue']
        ).pack(anchor='w', pady=(3, 8))
        
        # Status indicators
        status_frame = tk.Frame(status_inner, bg=self.COLORS['bg_secondary'])
        status_frame.pack(fill='x')
        
        self.status_var = tk.StringVar(value="⏳ RustDesk tekshirilmoqda...")
        self.status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            font=('Segoe UI', 10),
            bg=self.COLORS['bg_secondary'],
            fg=self.COLORS['accent_yellow']
        )
        self.status_label.pack(side='left')
        
        # Connection status
        self.connection_var = tk.StringVar(value="")
        tk.Label(
            status_frame,
            textvariable=self.connection_var,
            font=('Segoe UI', 10),
            bg=self.COLORS['bg_secondary'],
            fg=self.COLORS['text_secondary']
        ).pack(side='right')
        
        # ═══════════ FORM ═══════════
        form = tk.Frame(main, bg=self.COLORS['bg_dark'])
        form.pack(fill='x')
        
        # Name field
        tk.Label(
            form,
            text="👤  Ismingiz",
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['bg_dark'],
            fg=self.COLORS['text_primary'],
            anchor='w'
        ).pack(fill='x')
        
        self.name_entry = tk.Entry(
            form,
            font=('Segoe UI', 14),
            bg=self.COLORS['bg_tertiary'],
            fg=self.COLORS['text_primary'],
            insertbackground=self.COLORS['text_primary'],
            relief='flat',
            highlightthickness=2,
            highlightbackground=self.COLORS['border'],
            highlightcolor=self.COLORS['accent_green']
        )
        self.name_entry.pack(fill='x', ipady=12, pady=(5, 15))
        
        # Phone field
        tk.Label(
            form,
            text="📞  Telefon raqam",
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['bg_dark'],
            fg=self.COLORS['text_primary'],
            anchor='w'
        ).pack(fill='x')
        
        self.phone_entry = tk.Entry(
            form,
            font=('Segoe UI', 14),
            bg=self.COLORS['bg_tertiary'],
            fg=self.COLORS['text_primary'],
            insertbackground=self.COLORS['text_primary'],
            relief='flat',
            highlightthickness=2,
            highlightbackground=self.COLORS['border'],
            highlightcolor=self.COLORS['accent_green']
        )
        self.phone_entry.insert(0, "+998 ")
        self.phone_entry.pack(fill='x', ipady=12, pady=(5, 15))
        
        # Problem field
        tk.Label(
            form,
            text="📝  Muammo tavsifi",
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['bg_dark'],
            fg=self.COLORS['text_primary'],
            anchor='w'
        ).pack(fill='x')
        
        self.problem_text = tk.Text(
            form,
            font=('Segoe UI', 12),
            bg=self.COLORS['bg_tertiary'],
            fg=self.COLORS['text_primary'],
            insertbackground=self.COLORS['text_primary'],
            relief='flat',
            height=3,
            highlightthickness=2,
            highlightbackground=self.COLORS['border'],
            highlightcolor=self.COLORS['accent_green']
        )
        self.problem_text.pack(fill='x', pady=(5, 25))
        
        # ═══════════ SUBMIT BUTTON ═══════════
        self.submit_btn = tk.Button(
            form,
            text="✅   YORDAM SO'RASH",
            font=('Segoe UI', 16, 'bold'),
            bg=self.COLORS['accent_green'],
            fg='white',
            activebackground=self.COLORS['accent_green_hover'],
            activeforeground='white',
            relief='flat',
            cursor='hand2',
            command=self.on_submit
        )
        self.submit_btn.pack(fill='x', ipady=18)
        
        # Button hover effects
        self.submit_btn.bind('<Enter>', lambda e: self.submit_btn.config(bg=self.COLORS['accent_green_hover']))
        self.submit_btn.bind('<Leave>', lambda e: self.submit_btn.config(bg=self.COLORS['accent_green']))
        
        # ═══════════ FOOTER ═══════════
        footer = tk.Frame(main, bg=self.COLORS['bg_dark'])
        footer.pack(side='bottom', fill='x', pady=(20, 0))
        
        tk.Label(
            footer,
            text=f"v{VERSION} • {COMPANY_NAME}",
            font=('Segoe UI', 9),
            bg=self.COLORS['bg_dark'],
            fg=self.COLORS['text_secondary']
        ).pack()
        
        # Start background updates
        self.start_updates()
    
    def start_updates(self) -> None:
        """Start periodic UI updates"""
        self.update_rustdesk_status()
        self.update_connection_status()
    
    def update_rustdesk_status(self) -> None:
        """Update RustDesk ID and status"""
        if not self.root or not self.root.winfo_exists():
            return
        
        # Try to get RustDesk ID
        if not self.agent.rustdesk.rustdesk_id:
            self.agent.rustdesk.get_id()
        
        if self.agent.rustdesk.rustdesk_id:
            self.id_var.set(self.agent.rustdesk.rustdesk_id)
            self.status_var.set("✅ Tayyor ulanishga")
            self.status_label.config(fg=self.COLORS['accent_green'])
        else:
            self.id_var.set("Aniqlanmoqda...")
            self.status_var.set("⏳ RustDesk tekshirilmoqda...")
            self.status_label.config(fg=self.COLORS['accent_yellow'])
        
        # Schedule next update
        if self.root.winfo_exists():
            self.root.after(2000, self.update_rustdesk_status)
    
    def update_connection_status(self) -> None:
        """Update server connection status"""
        if not self.root or not self.root.winfo_exists():
            return
        
        # Send heartbeat in background
        def check():
            success = self.agent.send_heartbeat()
            if self.root and self.root.winfo_exists():
                if success:
                    self.connection_var.set("🟢 Server: Ulangan")
                else:
                    self.connection_var.set("🔴 Server: Ulanmagan")
        
        threading.Thread(target=check, daemon=True).start()
        
        # Schedule next update
        if self.root.winfo_exists():
            self.root.after(10000, self.update_connection_status)
    
    def on_submit(self) -> None:
        """Handle form submission"""
        from tkinter import messagebox
        
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        problem = self.problem_text.get('1.0', 'end').strip()
        
        # Validation
        if len(name) < 2:
            messagebox.showwarning("Xatolik", "Iltimos, ismingizni kiriting!")
            self.name_entry.focus()
            return
        
        if len(phone) < 9:
            messagebox.showwarning("Xatolik", "Iltimos, telefon raqamingizni kiriting!")
            self.phone_entry.focus()
            return
        
        if not problem:
            problem = "Belgilanmagan"
        
        # Register
        self.submit_btn.config(text="⏳  Yuborilmoqda...", state='disabled')
        self.root.update()
        
        success = self.agent.register_client(name, phone, problem)
        
        if success:
            rustdesk_id = self.agent.rustdesk.rustdesk_id or "Yuklanmoqda"
            messagebox.showinfo(
                "Muvaffaqiyat! ✅",
                f"Ma'lumotlaringiz yuborildi!\n\n"
                f"📋 RustDesk ID: {rustdesk_id}\n"
                f"🔐 Parol: {RUSTDESK_PASSWORD}\n\n"
                f"Mutaxassis tez orada siz bilan bog'lanadi.\n"
                f"Dastur fon rejimida ishlashda davom etadi."
            )
            
            # Start background services and minimize
            self.agent.start_background_services()
            self.root.iconify()  # Minimize to taskbar
        else:
            self.submit_btn.config(text="✅   YORDAM SO'RASH", state='normal')
            messagebox.showerror(
                "Xatolik",
                "Ma'lumotlarni yuborishda xatolik yuz berdi.\n"
                "Iltimos, internet ulanishingizni tekshiring va qayta urinib ko'ring."
            )
    
    def run(self) -> None:
        """Run GUI application"""
        self.create_window()
        
        # Handle window close
        def on_close():
            from tkinter import messagebox
            if self.agent.registered:
                if messagebox.askyesno(
                    "Chiqish",
                    "Dastur fon rejimida ishlashda davom etadimi?\n\n"
                    "Ha - Fon rejimida ishlash\n"
                    "Yo'q - Butunlay chiqish"
                ):
                    self.root.iconify()
                else:
                    self.agent.stop()
                    self.root.destroy()
            else:
                self.root.destroy()
        
        self.root.protocol("WM_DELETE_WINDOW", on_close)
        self.root.mainloop()

# ══════════════════════════════════════════════════════════════════════════════
#                           SYSTEM TRAY (Optional)
# ══════════════════════════════════════════════════════════════════════════════

class SystemTray:
    """System tray integration (requires pystray)"""
    
    def __init__(self, agent: Agent):
        self.agent = agent
        self.icon = None
    
    def create(self):
        """Create system tray icon"""
        try:
            import pystray
            from PIL import Image, ImageDraw
            
            # Create icon image
            image = Image.new('RGB', (64, 64), color='#238636')
            draw = ImageDraw.Draw(image)
            draw.ellipse([8, 8, 56, 56], fill='white')
            draw.text((20, 18), "U", fill='#238636')
            
            # Create menu
            menu = pystray.Menu(
                pystray.MenuItem("Ochish", self.on_open),
                pystray.MenuItem("Haqida", self.on_about),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Chiqish", self.on_exit)
            )
            
            self.icon = pystray.Icon(APP_NAME, image, APP_TITLE, menu)
            return True
            
        except ImportError:
            logger.warning("pystray not available - system tray disabled")
            return False
    
    def on_open(self, icon, item):
        pass
    
    def on_about(self, icon, item):
        pass
    
    def on_exit(self, icon, item):
        self.agent.stop()
        if self.icon:
            self.icon.stop()

# ══════════════════════════════════════════════════════════════════════════════
#                           MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point"""
    logger.info(f"Starting {APP_NAME} v{VERSION}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    
    # Create data directory
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize and run agent
    agent = Agent()
    
    try:
        agent.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
