#!/usr/bin/env python3
"""Fix admin panel connect function"""

with open('/root/remote-support/templates/admin.html', 'r') as f:
    content = f.read()

old_connect = '''        function connectClient(rustdeskId) {
            if (!rustdeskId || rustdeskId === '-') {
                showToast('RustDesk ID mavjud emas', 'error');
                return;
            }
            window.location.href = 'rustdesk://' + rustdeskId;
            showToast('RustDesk ochilmoqda...');
        }'''

new_connect = '''        function connectClient(rustdeskId) {
            if (!rustdeskId || rustdeskId === '-') {
                showToast('RustDesk ID mavjud emas', 'error');
                return;
            }
            
            // Modal oyna
            const existingModal = document.getElementById('connectModal');
            if (existingModal) existingModal.remove();
            
            const modal = document.createElement('div');
            modal.className = 'modal active';
            modal.id = 'connectModal';
            modal.innerHTML = `
                <div class="modal-content" style="max-width: 420px;">
                    <h3 style="margin-bottom: 20px; color: #0a84ff;">
                        <i class="fas fa-desktop"></i> RustDesk Ulanish
                    </h3>
                    <div style="background: #1c1c1e; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                        <div style="margin-bottom: 15px;">
                            <label style="color: #8e8e93; font-size: 12px;">RustDesk ID</label>
                            <div style="display: flex; align-items: center; gap: 10px; margin-top: 5px;">
                                <code id="rdId" style="flex: 1; background: #2c2c2e; padding: 12px; border-radius: 8px; font-size: 18px; color: #fff; letter-spacing: 2px;">${rustdeskId}</code>
                                <button onclick="navigator.clipboard.writeText('${rustdeskId}'); showToast('ID nusxalandi!')" 
                                        style="background: #0a84ff; border: none; padding: 12px 16px; border-radius: 8px; cursor: pointer;">
                                    <i class="fas fa-copy" style="color: #fff;"></i>
                                </button>
                            </div>
                        </div>
                        <div>
                            <label style="color: #8e8e93; font-size: 12px;">Parol</label>
                            <div style="display: flex; align-items: center; gap: 10px; margin-top: 5px;">
                                <code style="flex: 1; background: #2c2c2e; padding: 12px; border-radius: 8px; font-size: 18px; color: #30d158;">ustajon2025</code>
                                <button onclick="navigator.clipboard.writeText('ustajon2025'); showToast('Parol nusxalandi!')" 
                                        style="background: #30d158; border: none; padding: 12px 16px; border-radius: 8px; cursor: pointer;">
                                    <i class="fas fa-copy" style="color: #fff;"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                    <div style="display: flex; gap: 10px;">
                        <button onclick="document.getElementById('connectModal').remove()" 
                                class="modal-btn cancel" style="flex: 1;">Yopish</button>
                        <button onclick="window.location.href='rustdesk://'+document.getElementById('rdId').textContent; showToast('RustDesk ochilmoqda...');" 
                                class="modal-btn confirm" style="flex: 1; background: #0a84ff;">
                            <i class="fas fa-external-link-alt"></i> RustDesk ochish
                        </button>
                    </div>
                    <p style="margin-top: 15px; font-size: 11px; color: #8e8e93; text-align: center;">
                        RustDesk dasturini oching va yuqoridagi ID va parolni kiriting
                    </p>
                </div>
            `;
            document.body.appendChild(modal);
        }'''

if old_connect in content:
    content = content.replace(old_connect, new_connect)
    with open('/root/remote-support/templates/admin.html', 'w') as f:
        f.write(content)
    print('OK: Admin panel yangilandi')
else:
    print('ERROR: Kod topilmadi')
