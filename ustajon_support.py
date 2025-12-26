#!/usr/bin/env python3
"""
UstajonSupport Client Agent v5.0
- RustDesk auto-config with permanent password
- Remote command execution
- Auto-update support
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
import winreg
from pathlib import Path
from datetime import datetime

# Constants
VERSION = "5.0.0"
SERVER_URL = "http://31.220.75.75"
RUSTDESK_KEY = "YHo+N4vp+ZWP7wedLh69zCGk3aFf4935hwDKX9OdFXE="
RUSTDESK_PASSWORD = "ustajon2025"
HEARTBEAT_INTERVAL = 10  # seconds
COMMAND_CHECK_INTERVAL = 5  # seconds

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path.home() / "ustajon_support.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def is_admin():
    """Check if running as administrator"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_machine_id():
    """Generate unique machine ID"""
    try:
        machine_info = f"{socket.gethostname()}-{uuid.getnode()}"
        return hashlib.md5(machine_info.encode()).hexdigest()[:12].upper()
    except:
        return uuid.uuid4().hex[:12].upper()

def get_system_info():
    """Get system information"""
    try:
        hostname = socket.gethostname()
        
        # Get OS info
        try:
            result = subprocess.run(
                ['wmic', 'os', 'get', 'Caption', '/value'],
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            os_info = result.stdout.split('=')[1].strip() if '=' in result.stdout else "Windows"
        except:
            os_info = "Windows"
        
        return {
            "hostname": hostname,
            "os_info": os_info,
            "version": VERSION
        }
    except Exception as e:
        logger.error(f"System info error: {e}")
        return {"hostname": "Unknown", "os_info": "Windows", "version": VERSION}


class RustDeskManager:
    """Manage RustDesk installation and configuration"""
    
    RUSTDESK_PATHS = [
        Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / "RustDesk" / "rustdesk.exe",
        Path(os.environ.get('LOCALAPPDATA', '')) / "RustDesk" / "rustdesk.exe",
        Path.home() / "AppData" / "Local" / "RustDesk" / "rustdesk.exe",
    ]
    
    CONFIG_PATHS = [
        Path(os.environ.get('APPDATA', '')) / "RustDesk" / "config" / "RustDesk2.toml",
        Path.home() / "AppData" / "Roaming" / "RustDesk" / "config" / "RustDesk2.toml",
    ]
    
    def __init__(self):
        self.rustdesk_path = self._find_rustdesk()
        self.config_path = self._find_config_path()
        self.rustdesk_id = None
    
    def _find_rustdesk(self):
        """Find RustDesk executable"""
        for path in self.RUSTDESK_PATHS:
            if path.exists():
                logger.info(f"RustDesk found: {path}")
                return path
        
        # Search in PATH
        try:
            result = subprocess.run(
                ['where', 'rustdesk'],
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                path = Path(result.stdout.strip().split('\n')[0])
                if path.exists():
                    return path
        except:
            pass
        
        return None
    
    def _find_config_path(self):
        """Find RustDesk config path"""
        for path in self.CONFIG_PATHS:
            if path.parent.exists():
                return path
        
        # Create default path
        default = Path(os.environ.get('APPDATA', '')) / "RustDesk" / "config" / "RustDesk2.toml"
        default.parent.mkdir(parents=True, exist_ok=True)
        return default
    
    def configure(self):
        """Configure RustDesk with our server"""
        try:
            # Read existing config
            config_content = ""
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_content = f.read()
            
            # Parse existing values
            lines = config_content.split('\n') if config_content else []
            config_dict = {}
            for line in lines:
                if '=' in line:
                    key, value = line.split('=', 1)
                    config_dict[key.strip()] = value.strip()
            
            # Keep existing ID if present
            existing_id = config_dict.get('id', '').strip("'\"")
            
            # Update config
            config_dict['rendezvous_server'] = "'31.220.75.75'"
            config_dict['nat_type'] = '1'
            config_dict['serial'] = '0'
            config_dict['key'] = f"'{RUSTDESK_KEY}'"
            
            # Set permanent password
            config_dict['password'] = f"'{RUSTDESK_PASSWORD}'"
            config_dict['direct-server'] = "'Y'"
            config_dict['direct-access-port'] = "'21118'"
            
            # Write config
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                for key, value in config_dict.items():
                    f.write(f"{key} = {value}\n")
            
            logger.info(f"RustDesk configured: {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Config error: {e}")
            return False
    
    def get_id(self):
        """Get RustDesk ID"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip().startswith('id'):
                            parts = line.split('=', 1)
                            if len(parts) == 2:
                                self.rustdesk_id = parts[1].strip().strip("'\"")
                                return self.rustdesk_id
            
            # Try to get from registry
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\RustDesk")
                self.rustdesk_id, _ = winreg.QueryValueEx(key, "id")
                winreg.CloseKey(key)
                return self.rustdesk_id
            except:
                pass
                
        except Exception as e:
            logger.error(f"Get ID error: {e}")
        
        return None
    
    def ensure_running(self):
        """Ensure RustDesk service is running"""
        try:
            # Check if already running
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq rustdesk.exe'],
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if 'rustdesk.exe' in result.stdout.lower():
                logger.info("RustDesk already running")
                return True
            
            # Start RustDesk
            if self.rustdesk_path and self.rustdesk_path.exists():
                subprocess.Popen(
                    [str(self.rustdesk_path), '--service'],
                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
                )
                logger.info("RustDesk started")
                time.sleep(3)
                return True
            
        except Exception as e:
            logger.error(f"RustDesk start error: {e}")
        
        return False
    
    def restart(self):
        """Restart RustDesk to apply config"""
        try:
            # Kill existing
            subprocess.run(
                ['taskkill', '/F', '/IM', 'rustdesk.exe'],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(2)
            
            # Start again
            return self.ensure_running()
        except:
            return False


class RemoteCommand:
    """Execute remote commands"""
    
    @staticmethod
    def execute_cmd(command):
        """Execute CMD command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            output = result.stdout + result.stderr
            return True, output[:10000]  # Limit output
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def execute_powershell(command):
        """Execute PowerShell command"""
        try:
            result = subprocess.run(
                ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', command],
                capture_output=True,
                text=True,
                timeout=120,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            output = result.stdout + result.stderr
            return True, output[:10000]
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_system_info():
        """Get detailed system information"""
        try:
            info = []
            
            # Computer name
            info.append(f"Computer: {socket.gethostname()}")
            
            # OS
            result = subprocess.run(
                ['wmic', 'os', 'get', 'Caption,Version', '/value'],
                capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            for line in result.stdout.split('\n'):
                if '=' in line:
                    info.append(line.strip())
            
            # CPU
            result = subprocess.run(
                ['wmic', 'cpu', 'get', 'Name', '/value'],
                capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            for line in result.stdout.split('\n'):
                if '=' in line:
                    info.append(f"CPU: {line.split('=')[1].strip()}")
            
            # RAM
            result = subprocess.run(
                ['wmic', 'computersystem', 'get', 'TotalPhysicalMemory', '/value'],
                capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            for line in result.stdout.split('\n'):
                if 'TotalPhysicalMemory=' in line:
                    ram_bytes = int(line.split('=')[1].strip())
                    ram_gb = round(ram_bytes / (1024**3), 1)
                    info.append(f"RAM: {ram_gb} GB")
            
            # IP
            result = subprocess.run(
                ['ipconfig'],
                capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            for line in result.stdout.split('\n'):
                if 'IPv4' in line and '=' in line:
                    info.append(f"IP: {line.split(':')[1].strip()}")
                    break
            
            return True, '\n'.join(info)
        except Exception as e:
            return False, str(e)


class SupportAgent:
    """Main support agent class"""
    
    def __init__(self):
        self.client_id = get_machine_id()
        self.running = True
        self.registered = False
        self.user_info = {}
        
        self.rustdesk = RustDeskManager()
        
        logger.info(f"Agent v{VERSION} starting, ID: {self.client_id}")
    
    def setup_rustdesk(self):
        """Setup RustDesk"""
        # Configure
        self.rustdesk.configure()
        
        # Ensure running
        self.rustdesk.ensure_running()
        
        # Wait for ID
        for _ in range(10):
            rustdesk_id = self.rustdesk.get_id()
            if rustdesk_id:
                logger.info(f"RustDesk ID: {rustdesk_id}")
                return rustdesk_id
            time.sleep(1)
        
        return None
    
    def send_heartbeat(self):
        """Send heartbeat to server"""
        try:
            import urllib.request
            
            sys_info = get_system_info()
            rustdesk_id = self.rustdesk.get_id()
            
            data = {
                "client_id": self.client_id,
                "rustdesk_id": rustdesk_id,
                "hostname": sys_info.get("hostname", ""),
                "os_info": sys_info.get("os_info", ""),
                "version": VERSION,
                **self.user_info
            }
            
            req = urllib.request.Request(
                f"{SERVER_URL}/api/heartbeat",
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                if not self.registered and result.get('success'):
                    self.registered = True
                    logger.info("Registered with server")
                return True
                
        except Exception as e:
            logger.debug(f"Heartbeat error: {e}")
            return False
    
    def check_commands(self):
        """Check and execute pending commands"""
        try:
            import urllib.request
            
            url = f"{SERVER_URL}/api/agent/commands?client_id={self.client_id}"
            req = urllib.request.Request(url, method='GET')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                commands = json.loads(response.read().decode('utf-8'))
            
            for cmd in commands:
                if cmd.get('status') != 'pending':
                    continue
                
                cmd_id = cmd.get('id')
                cmd_type = cmd.get('type', 'cmd')
                command = cmd.get('command', '')
                
                logger.info(f"Executing command [{cmd_id}]: {cmd_type} - {command[:50]}...")
                
                # Execute based on type
                if cmd_type == 'powershell':
                    success, output = RemoteCommand.execute_powershell(command)
                elif cmd_type == 'system_info' or cmd_type == 'sysinfo':
                    success, output = RemoteCommand.get_system_info()
                else:  # cmd
                    success, output = RemoteCommand.execute_cmd(command)
                
                # Send result
                self.send_command_result(cmd_id, success, output)
                
        except Exception as e:
            logger.debug(f"Command check error: {e}")
    
    def send_command_result(self, cmd_id, success, output):
        """Send command result to server"""
        try:
            import urllib.request
            
            data = {
                "client_id": self.client_id,
                "command_id": cmd_id,
                "success": success,
                "output": output
            }
            
            req = urllib.request.Request(
                f"{SERVER_URL}/api/agent/command-result",
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                logger.info(f"Command result sent: {cmd_id} - {'Success' if success else 'Failed'}")
                return result.get('success', False)
                
        except Exception as e:
            logger.error(f"Result send error: {e}")
            return False
    
    def heartbeat_loop(self):
        """Heartbeat loop"""
        while self.running:
            self.send_heartbeat()
            time.sleep(HEARTBEAT_INTERVAL)
    
    def command_loop(self):
        """Command check loop"""
        while self.running:
            self.check_commands()
            time.sleep(COMMAND_CHECK_INTERVAL)
    
    def run(self):
        """Main run method"""
        # Setup RustDesk
        rustdesk_id = self.setup_rustdesk()
        if not rustdesk_id:
            logger.warning("RustDesk ID not found, will retry...")
        
        # Show GUI for user info
        self.show_gui()
        
        # Start background threads
        heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        command_thread = threading.Thread(target=self.command_loop, daemon=True)
        command_thread.start()
        
        logger.info("Agent running...")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            logger.info("Agent stopped")
    
    def show_gui(self):
        """Show registration GUI"""
        try:
            import tkinter as tk
            from tkinter import ttk, messagebox
            
            root = tk.Tk()
            root.title("UstajonSupport - Texnik Yordam")
            root.geometry("450x500")
            root.resizable(False, False)
            
            # Center window
            root.update_idletasks()
            x = (root.winfo_screenwidth() - 450) // 2
            y = (root.winfo_screenheight() - 500) // 2
            root.geometry(f"+{x}+{y}")
            
            # Dark theme
            root.configure(bg='#1a1a2e')
            
            style = ttk.Style()
            style.theme_use('clam')
            style.configure('TLabel', background='#1a1a2e', foreground='white', font=('Segoe UI', 11))
            style.configure('TEntry', fieldbackground='#16213e', foreground='white', font=('Segoe UI', 11))
            style.configure('TButton', background='#0f3460', foreground='white', font=('Segoe UI', 11, 'bold'))
            
            # Header
            header = tk.Label(root, text="🔧 Texnik Yordam", font=('Segoe UI', 20, 'bold'), 
                            bg='#1a1a2e', fg='#00d9ff')
            header.pack(pady=20)
            
            subtitle = tk.Label(root, text="Muammongizni hal qilishga yordam beramiz", 
                              font=('Segoe UI', 10), bg='#1a1a2e', fg='#888')
            subtitle.pack()
            
            # Form frame
            form = tk.Frame(root, bg='#1a1a2e')
            form.pack(pady=30, padx=40, fill='x')
            
            # Name
            tk.Label(form, text="👤 Ismingiz:", bg='#1a1a2e', fg='white', 
                    font=('Segoe UI', 11)).pack(anchor='w')
            name_entry = tk.Entry(form, font=('Segoe UI', 12), bg='#16213e', fg='white',
                                 insertbackground='white', relief='flat', bd=10)
            name_entry.pack(fill='x', pady=(5, 15))
            
            # Phone
            tk.Label(form, text="📱 Telefon raqami:", bg='#1a1a2e', fg='white',
                    font=('Segoe UI', 11)).pack(anchor='w')
            phone_entry = tk.Entry(form, font=('Segoe UI', 12), bg='#16213e', fg='white',
                                  insertbackground='white', relief='flat', bd=10)
            phone_entry.insert(0, "+998")
            phone_entry.pack(fill='x', pady=(5, 15))
            
            # Problem
            tk.Label(form, text="❓ Muammo:", bg='#1a1a2e', fg='white',
                    font=('Segoe UI', 11)).pack(anchor='w')
            problem_text = tk.Text(form, font=('Segoe UI', 11), bg='#16213e', fg='white',
                                  insertbackground='white', relief='flat', height=4, bd=10)
            problem_text.pack(fill='x', pady=(5, 15))
            
            # RustDesk ID display
            rustdesk_id = self.rustdesk.get_id() or "Yuklanmoqda..."
            id_frame = tk.Frame(form, bg='#0f3460', bd=0)
            id_frame.pack(fill='x', pady=10)
            
            tk.Label(id_frame, text="🔗 RustDesk ID:", bg='#0f3460', fg='#888',
                    font=('Segoe UI', 9)).pack(anchor='w', padx=10, pady=(10, 0))
            id_label = tk.Label(id_frame, text=rustdesk_id, bg='#0f3460', fg='#00d9ff',
                              font=('Consolas', 14, 'bold'))
            id_label.pack(anchor='w', padx=10, pady=(0, 10))
            
            def submit():
                name = name_entry.get().strip()
                phone = phone_entry.get().strip()
                problem = problem_text.get('1.0', 'end').strip()
                
                if not name:
                    messagebox.showwarning("Xatolik", "Ismingizni kiriting!")
                    return
                if not phone or len(phone) < 9:
                    messagebox.showwarning("Xatolik", "Telefon raqamini kiriting!")
                    return
                
                self.user_info = {
                    "name": name,
                    "phone": phone,
                    "problem": problem or "Belgilanmagan"
                }
                
                # Send immediately
                self.send_heartbeat()
                
                messagebox.showinfo("Muvaffaqiyat", 
                    "✅ Ma'lumotlar yuborildi!\n\n"
                    "Mutaxassis tez orada siz bilan bog'lanadi.\n"
                    "Dasturni yopmang!")
                root.destroy()
            
            # Submit button
            submit_btn = tk.Button(form, text="📤 Yuborish", font=('Segoe UI', 12, 'bold'),
                                  bg='#00d9ff', fg='#1a1a2e', relief='flat', 
                                  cursor='hand2', command=submit, height=2)
            submit_btn.pack(fill='x', pady=20)
            
            # Update ID periodically
            def update_id():
                new_id = self.rustdesk.get_id()
                if new_id:
                    id_label.config(text=new_id)
                else:
                    root.after(2000, update_id)
            
            root.after(2000, update_id)
            
            root.mainloop()
            
        except Exception as e:
            logger.error(f"GUI error: {e}")
            # Continue without GUI
            self.user_info = {
                "name": "Auto-client",
                "phone": "",
                "problem": ""
            }


def main():
    """Main entry point"""
    try:
        agent = SupportAgent()
        agent.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
