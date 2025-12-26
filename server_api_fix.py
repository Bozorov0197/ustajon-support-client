#!/usr/bin/env python3
"""Server API fix script"""
import re

with open('/root/remote-support/app.py', 'r') as f:
    content = f.read()

# New Register API
new_register = '''
@app.route("/api/agent/register", methods=["POST"])
def api_agent_register():
    """Agent tomonidan client royxatdan otkazish - telefon boyicha unikal"""
    try:
        if request.is_json:
            data = request.json
        else:
            data = request.form.to_dict()
        
        phone = data.get("phone", "").strip()
        name = data.get("name", "").strip()
        rustdesk_id = data.get("rustdesk_id", "")
        hostname = data.get("hostname", "Unknown")
        problem = data.get("problem", "")
        version = data.get("version", "unknown")
        ip = request.remote_addr
        
        if not phone:
            return jsonify({"error": "Telefon raqam kerak", "success": False}), 400
        
        import hashlib
        client_id = hashlib.md5(phone.encode()).hexdigest()[:12].upper()
        
        clients = load_clients()
        
        existing_id = None
        for cid, cdata in clients.items():
            if cdata.get("phone") == phone:
                existing_id = cid
                break
        
        is_new = existing_id is None
        
        if existing_id and existing_id != client_id:
            clients[client_id] = clients.pop(existing_id)
        
        now = datetime.now().isoformat()
        
        if client_id in clients:
            clients[client_id].update({
                "rustdesk_id": rustdesk_id,
                "hostname": hostname,
                "name": name if name else clients[client_id].get("name", hostname),
                "problem": problem if problem else clients[client_id].get("problem"),
                "last_seen": now,
                "status": "online",
                "active": True,
                "version": version,
                "ip": ip
            })
        else:
            clients[client_id] = {
                "id": client_id,
                "phone": phone,
                "name": name if name else hostname,
                "rustdesk_id": rustdesk_id,
                "hostname": hostname,
                "problem": problem,
                "registered": now,
                "last_seen": now,
                "status": "online",
                "active": True,
                "version": version,
                "ip": ip,
                "platform": "windows"
            }
        
        save_clients(clients)
        
        if is_new:
            try:
                import requests
                msg = "YANGI MIJOZ!\\n\\n"
                msg += f"Ism: {name}\\n"
                msg += f"Tel: {phone}\\n"
                msg += f"RustDesk: {rustdesk_id}\\n"
                msg += f"PC: {hostname}\\n"
                msg += f"Muammo: {problem}\\n"
                msg += "Parol: ustajon2025"
                
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    data={"chat_id": TELEGRAM_ADMIN_ID, "text": msg},
                    timeout=10
                )
            except Exception as e:
                logger.error(f"Telegram error: {e}")
        
        sio.emit("client_update", clients[client_id])
        
        logger.info(f"Client registered: {client_id}, phone={phone}")
        return jsonify({"success": True, "client_id": client_id, "is_new": is_new})
        
    except Exception as e:
        logger.error(f"Register error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
'''

# New Heartbeat API
new_heartbeat = '''
@app.route("/api/agent/heartbeat", methods=["POST"])
def api_agent_heartbeat():
    """Agent heartbeat"""
    try:
        if request.is_json:
            data = request.json
        else:
            data = request.form.to_dict()
        
        client_id = data.get("client_id", "")
        rustdesk_id = data.get("rustdesk_id", "")
        
        if not client_id and not rustdesk_id:
            return jsonify({"success": False, "error": "ID kerak"}), 400
        
        clients = load_clients()
        
        found_id = None
        if client_id and client_id in clients:
            found_id = client_id
        else:
            for cid, cdata in clients.items():
                if cdata.get("rustdesk_id") == rustdesk_id:
                    found_id = cid
                    break
        
        if not found_id:
            return jsonify({"success": False, "error": "Client topilmadi"}), 404
        
        if clients[found_id].get("status") == "deleted" or not clients[found_id].get("active", True):
            return jsonify({"success": True, "deleted": True})
        
        clients[found_id]["last_seen"] = datetime.now().isoformat()
        clients[found_id]["status"] = "online"
        save_clients(clients)
        
        return jsonify({"success": True})
        
    except Exception as e:
        logger.error(f"Heartbeat error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
'''

# New Check API
new_check = '''
@app.route("/api/client/check", methods=["POST"])
def api_client_check():
    """Telefon royicha client tekshirish"""
    try:
        if request.is_json:
            data = request.json
        else:
            data = request.form.to_dict()
        
        phone = data.get("phone", "").strip()
        
        if not phone:
            return jsonify({"exists": False})
        
        clients = load_clients()
        
        for client_id, client in clients.items():
            if client.get("phone") == phone:
                return jsonify({
                    "exists": True,
                    "active": client.get("active", True) and client.get("status") != "deleted",
                    "client_id": client_id,
                    "rustdesk_id": client.get("rustdesk_id")
                })
        
        return jsonify({"exists": False})
        
    except Exception as e:
        logger.error(f"Client check error: {e}")
        return jsonify({"exists": False, "error": str(e)})
'''

# Remove old APIs
content = re.sub(r'@app\.route\("/api/agent/register".*?(?=\n@app\.route|\nif __name__|$)', '', content, flags=re.DOTALL)
content = re.sub(r'@app\.route\("/api/agent/heartbeat".*?(?=\n@app\.route|\nif __name__|$)', '', content, flags=re.DOTALL)
content = re.sub(r'@app\.route\("/api/client/check".*?(?=\n@app\.route|\nif __name__|$)', '', content, flags=re.DOTALL)
content = re.sub(r'@app\.route\("/api/admin/delete_client.*?(?=\n@app\.route|\nif __name__|$)', '', content, flags=re.DOTALL)

# Clean multiple newlines
content = re.sub(r'\n{4,}', '\n\n\n', content)

# Add new APIs
if 'if __name__' in content:
    content = content.replace('if __name__', f'''
# ============ AGENT API (v3.0) ============
{new_register}
{new_heartbeat}
{new_check}


if __name__''')

with open('/root/remote-support/app.py', 'w') as f:
    f.write(content)

print('OK: API yangilandi')
