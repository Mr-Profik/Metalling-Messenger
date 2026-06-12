import os
import random
import threading
import time
from flask import Flask, request, jsonify, render_template_string
from telebot import types
import telebot

# ==========================================
# METALLING MESSENGER CONFIG
# ==========================================
BOT_TOKEN = '8876807144:AAGU3Frf6LJsIxZxORZM1kS46W9iDRn23dU'
OWNER_PIN = "7777"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

db = {
    "users": {},
    "messages": [],
    "valid_codes": {},
    "owner_phone": None
}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button = types.KeyboardButton("🛡 VERIFY IDENTITY", request_contact=True)
    markup.add(button)
    bot.send_message(message.chat.id, "⚡️ **METALLING CORE ACCESS**\n\nConfirm your phone to receive the access key.", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(content_types=['contact'])
def contact(message):
    if message.contact is not None:
        phone = message.contact.phone_number.replace("+", "").strip()
        code = str(random.randint(111111, 999999))
        db["valid_codes"][phone] = code
        bot.send_message(message.chat.id, f"🔑 ACCESS_KEY: `{code}`", parse_mode='Markdown', reply_markup=types.KeyboardRemove())

@app.route('/api/verify', methods=['POST'])
def verify():
    data = request.json
    phone = data.get('phone', '').replace("+", "").strip()
    code = str(data.get('code', ''))
    pin = str(data.get('pin', ''))
    if phone in db["valid_codes"] and db["valid_codes"][phone] == code:
        if pin == OWNER_PIN:
            if db["owner_phone"] is None or db["owner_phone"] == phone:
                db["owner_phone"] = phone
                del db["valid_codes"][phone]
                return jsonify({"success": True, "step": "register", "role": "owner"})
        del db["valid_codes"][phone]
        if phone in db["users"]:
            return jsonify({"success": True, "step": "main", "role": "user", "data": db["users"][phone]})
        return jsonify({"success": True, "step": "register", "role": "user"})
    return jsonify({"success": False, "message": "ACCESS_DENIED: INVALID_TOKEN"})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    phone = data.get('phone').replace("+", "").strip()
    username = data.get('username') or f"User_{random.randint(1000, 9999)}"
    if not username.startswith("@"): username = "@" + username
    db["users"][phone] = {
        "name": data.get('name'),
        "username": username,
        "role": data.get('role'),
        "balance": 999999 if data.get('role') == 'owner' else 100
    }
    return jsonify({"success": True})

@app.route('/api/messages', methods=['GET', 'POST'])
def handle_messages():
    if request.method == 'POST':
        data = request.json
        db["messages"].append({
            "u": data['name'],
            "un": data['username'],
            "t": data['text'],
            "r": data['role'],
            "tm": time.strftime("%H:%M")
        })
        if len(db["messages"]) > 50: db["messages"].pop(0)
    return jsonify(db["messages"])

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Metalling Messenger</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=JetBrains+Mono:wght@300;500&display=swap');
        
        :root {
            --neon-green: #00ff41;
            --neon-pink: #ff0055;
            --bg-dark: #050505;
            --panel-bg: rgba(15, 15, 15, 0.9);
        }

        body { 
            background: var(--bg-dark); 
            color: var(--neon-green); 
            font-family: 'JetBrains Mono', monospace; 
            margin: 0; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh;
            background-image: linear-gradient(rgba(0, 255, 65, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 255, 65, 0.05) 1px, transparent 1px);
            background-size: 30px 30px;
        }

        .app-container { 
            background: var(--panel-bg); 
            border: 2px solid var(--neon-green); 
            width: 380px; 
            height: 650px; 
            border-radius: 20px; 
            display: flex; 
            flex-direction: column; 
            position: relative; 
            box-shadow: 0 0 20px rgba(0, 255, 65, 0.2), inset 0 0 10px rgba(0, 255, 65, 0.1);
            overflow: hidden;
            backdrop-filter: blur(10px);
        }

        .header { 
            padding: 20px; 
            border-bottom: 2px solid var(--neon-green); 
            text-align: center; 
            font-family: 'Orbitron', sans-serif;
            font-size: 16px; 
            letter-spacing: 4px; 
            text-shadow: 0 0 10px var(--neon-green);
        }

        .content { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; }

        input { 
            background: rgba(0,0,0,0.7); 
            border: 1px solid #333; 
            color: var(--neon-green); 
            padding: 15px; 
            margin-bottom: 15px; 
            border-radius: 8px; 
            outline: none; 
            transition: 0.3s;
            font-size: 14px;
        }
        input:focus { border-color: var(--neon-green); box-shadow: 0 0 10px rgba(0, 255, 65, 0.3); }

        button { 
            background: var(--neon-green); 
            color: #000; 
            border: none; 
            padding: 15px; 
            font-weight: bold; 
            cursor: pointer; 
            border-radius: 8px; 
            text-transform: uppercase; 
            font-family: 'Orbitron', sans-serif;
            transition: 0.3s;
        }
        button:hover { background: #fff; box-shadow: 0 0 20px #fff; transform: translateY(-2px); }

        .hidden { display: none; }

        /* CHAT STYLES */
        .chat-msg { 
            margin-bottom: 15px; 
            padding: 12px; 
            border-radius: 10px; 
            background: rgba(255,255,255,0.03); 
            border-left: 3px solid var(--neon-green);
            animation: fadeIn 0.5s ease;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateX(-10px); } to { opacity: 1; transform: translateX(0); } }

        .msg-header { display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 5px; }
        .u-name { font-weight: bold; color: #fff; }
        .u-root { color: var(--neon-pink); text-shadow: 0 0 5px var(--neon-pink); }
        .msg-text { font-size: 14px; color: #ccc; line-height: 1.4; }
        
        .footer { padding: 15px; background: rgba(0,0,0,0.5); display: flex; gap: 10px; border-top: 1px solid #222; }

        /* SCROLLBAR */
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background: var(--neon-green); border-radius: 10px; }
    </style>
</head>
<body>
    <div class="app-container">
        <div class="header" id="h_title">METALLING CORE</div>
        
        <div id="scr_auth" class="content">
            <div style="text-align:center; margin-bottom:30px;">
                <div style="font-size:40px; margin-bottom:10px;">⛓</div>
                <div style="font-size:10px; color:#555;">ENCRYPTED PROTOCOL V2.4</div>
            </div>
            <input type="text" id="phone" placeholder="PHONE_ID">
            <input type="text" id="code" placeholder="ACCESS_KEY (FROM BOT)">
            <input type="password" id="pin" placeholder="ROOT_PIN (OPTIONAL)">
            <button onclick="auth()">ESTABLISH CONNECTION</button>
            <p style="text-align: center; margin-top: 20px;">
                <a href="https://t.me/bot8876807144" target="_blank" style="color: var(--neon-green); text-decoration: none; font-size: 11px;">[ GET KEY VIA TELEGRAM ]</a>
            </p>
        </div>

        <div id="scr_reg" class="content hidden">
            <h3>CREATE IDENTITY</h3>
            <input type="text" id="name" placeholder="DISPLAY NAME">
            <input type="text" id="uname" placeholder="@USERNAME">
            <button onclick="register()">SAVE_TO_CORE</button>
        </div>

        <div id="scr_chat" class="content hidden" style="padding:0;">
            <div id="messages_list" style="flex: 1; overflow-y: auto; padding: 20px;"></div>
            <div class="footer">
                <input type="text" id="msg_input" placeholder="Enter command..." style="margin-bottom: 0; flex:1;">
                <button onclick="sendMsg()" style="padding: 10px 20px;">EXE</button>
            </div>
        </div>
    </div>

    <script>
        let session = { phone: "", name: "", username: "", role: "" };

        async function auth() {
            session.phone = document.getElementById('phone').value.trim();
            const code = document.getElementById('code').value;
            const pin = document.getElementById('pin').value;
            const res = await fetch('/api/verify', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone: session.phone, code, pin })
            });
            const data = await res.json();
            if(data.success) {
                session.role = data.role;
                document.getElementById('scr_auth').classList.add('hidden');
                if(data.step === 'register') document.getElementById('scr_reg').classList.remove('hidden');
                else { session.name = data.data.name; session.username = data.data.username; startChat(); }
            } else alert(data.message);
        }

        async function register() {
            session.name = document.getElementById('name').value;
            session.username = document.getElementById('uname').value;
            await fetch('/api/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone: session.phone, name: session.name, username: session.username, role: session.role })
            });
            document.getElementById('scr_reg').classList.add('hidden');
            startChat();
        }

        function startChat() {
            document.getElementById('scr_chat').classList.remove('hidden');
            const h = document.getElementById('h_title');
            h.innerText = session.role === 'owner' ? "SYSTEM ROOT" : "CORE MEMBER";
            if(session.role === 'owner') h.style.color = "var(--neon-pink)";
            
            setInterval(async () => {
                const res = await fetch('/api/messages');
                const msgs = await res.json();
                const list = document.getElementById('messages_list');
                list.innerHTML = msgs.map(m => `
                    <div class="chat-msg" style="${m.r === 'owner' ? 'border-left-color: var(--neon-pink)' : ''}">
                        <div class="msg-header">
                            <span class="${m.r === 'owner' ? 'u-root' : 'u-name'}">${m.u} ${m.un}</span>
                            <span style="color:#444">${m.tm}</span>
                        </div>
                        <div class="msg-text">${m.t}</div>
                    </div>
                `).join('');
                list.scrollTop = list.scrollHeight;
            }, 2000);
        }

        async function sendMsg() {
            const input = document.getElementById('msg_input');
            if(!input.value) return;
            await fetch('/api/messages', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name: session.name, username: session.username, text: input.value, role: session.role })
            });
            input.value = "";
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

if __name__ == '__main__':
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
