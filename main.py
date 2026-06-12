import os, random, threading, time, telebot
from flask import Flask, request, jsonify, render_template_string

# CONFIG
BOT_TOKEN = '8876807144:AAGU3Frf6LJsIxZxORZM1kS46W9iDRn23dU'
OWNER_PIN = "7777"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

db = {
    "users": {}, "messages": [], "codes": {}, "gift": None, "muted": [], "admins": []
}

@bot.message_handler(commands=['start'])
def st(m):
    kb = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    kb.add(telebot.types.KeyboardButton("🛡 ПОДТВЕРДИТЬ ЛИЧНОСТЬ", request_contact=True))
    bot.send_message(m.chat.id, "⚡️ **METALLING CORE**\nПройдите верификацию для доступа к сети.", reply_markup=kb, parse_mode='Markdown')

@bot.message_handler(content_types=['contact'])
def co(m):
    if m.contact:
        p = m.contact.phone_number.replace("+","")
        c = str(random.randint(111111, 999999))
        db["codes"][p] = c
        bot.send_message(m.chat.id, f"🔑 ВАШ КЛЮЧ ДОСТУПА: `{c}`", parse_mode='Markdown')

@app.route('/api/verify', methods=['POST'])
def ve():
    d = request.json
    p, c, pin = d.get('p').replace("+",""), str(d.get('c')), str(d.get('pin'))
    if p in db["codes"] and db["codes"][p] == c:
        role = "owner" if pin == OWNER_PIN else ("admin" if p in db["admins"] else "user")
        return jsonify({"s": True, "r": role, "u": db["users"].get(p)})
    return jsonify({"s": False, "m": "ОШИБКА: КЛЮЧ НЕ ВАЛИДЕН"})

@app.route('/api/reg', methods=['POST'])
def rg():
    d = request.json
    p = d.get('p').replace("+","")
    db["users"][p] = {"n": d.get('n'), "un": d.get('un'), "r": d.get('r'), "p": p}
    return jsonify({"s": True})

@app.route('/api/msg', methods=['GET', 'POST'])
def msg():
    if request.method == 'POST':
        d = request.json
        if d['f'] in db["muted"]: return jsonify({"s": False})
        db["messages"].append({"f": d['f'], "fn": d['fn'], "t": d['t'], "r": d['r'], "tm": time.strftime("%H:%M")})
        if len(db["messages"]) > 80: db["messages"].pop(0)
    return jsonify({"m": db["messages"], "g": db["gift"], "u": list(db["users"].values())})

@app.route('/api/admin', methods=['POST'])
def adm():
    d = request.json
    if d.get('r') not in ['owner', 'admin']: return jsonify({"s": False})
    cmd = d.get('cmd').split()
    c = cmd[0].lower()
    if c == '/gift': db["gift"] = cmd[1]
    elif c == '/gift_cls': db["gift"] = None
    elif c == '/clear': db["messages"] = []
    elif c == '/mute': db["muted"].append(cmd[1].replace("+",""))
    elif c == '/setadmin': db["admins"].append(cmd[1].replace("+",""))
    return jsonify({"s": True})

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Metalling Messenger</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=JetBrains+Mono:wght@300;500&display=swap');
        :root { --neon: #00ff41; --neon-p: #ff0055; --bg: #050505; }
        body { background: var(--bg); color: var(--neon); font-family: 'JetBrains Mono', monospace; margin: 0; overflow: hidden; background-image: linear-gradient(rgba(0,255,65,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,65,0.03) 1px, transparent 1px); background-size: 30px 30px; }
        .app { display: flex; height: 100vh; width: 100vw; border: 1px solid var(--neon); box-sizing: border-box; }
        .sidebar { width: 300px; background: rgba(10,10,10,0.9); border-right: 1px solid var(--neon); display: flex; flex-direction: column; }
        .chat-area { flex: 1; display: flex; flex-direction: column; background: rgba(5,5,5,0.8); backdrop-filter: blur(5px); }
        .overlay { position: fixed; inset: 0; background: var(--bg); z-index: 100; display: flex; align-items: center; justify-content: center; flex-direction: column; text-align: center; }
        .user-item { padding: 15px; border-bottom: 1px solid rgba(0,255,65,0.2); cursor: pointer; transition: 0.3s; }
        .user-item:hover { background: rgba(0,255,65,0.1); box-shadow: inset 0 0 10px var(--neon); }
        .msg-b { max-width: 80%; padding: 10px; margin: 10px; border: 1px solid var(--neon); position: relative; clip-path: polygon(0 0, 100% 0, 100% 70%, 95% 100%, 0 100%); }
        .msg-in { align-self: flex-start; border-left: 4px solid var(--neon); background: rgba(0,255,65,0.05); }
        .msg-out { align-self: flex-end; border-right: 4px solid var(--neon-p); border-color: var(--neon-p); background: rgba(255,0,85,0.05); color: #fff; }
        .input-box { padding: 20px; border-top: 1px solid var(--neon); display: flex; gap: 10px; background: #000; }
        input { background: transparent; border: 1px solid var(--neon); color: var(--neon); padding: 12px; outline: none; flex: 1; font-family: inherit; }
        button { background: var(--neon); color: #000; border: none; padding: 10px 20px; cursor: pointer; font-family: 'Orbitron'; font-weight: bold; transition: 0.3s; }
        button:hover { background: #fff; box-shadow: 0 0 15px #fff; }
        .hidden { display: none !important; }
        .adm-btn { background: var(--neon-p); color: #fff; padding: 5px; text-align: center; font-size: 10px; cursor: pointer; font-family: 'Orbitron'; letter-spacing: 2px; }
        .gift-alert { background: var(--neon-p); padding: 15px; text-align: center; border: 2px solid #fff; margin: 10px; animation: glitch 1s infinite; cursor: pointer; }
        @keyframes glitch { 0% { transform: translate(0); } 20% { transform: translate(-2px, 2px); } 40% { transform: translate(-2px, -2px); } 60% { transform: translate(2px, 2px); } 80% { transform: translate(2px, -2px); } 100% { transform: translate(0); } }
    </style>
</head>
<body>
    <div id="auth_scr" class="overlay">
        <h1 style="font-family:'Orbitron'; letter-spacing:5px; text-shadow: 0 0 10px var(--neon);">METALLING CORE</h1>
        <div style="width: 300px; padding: 20px; border: 1px solid var(--neon); background: rgba(0,255,65,0.05);">
            <input id="ph" placeholder="НОМЕР ТЕЛЕФОНА"><br>
            <input id="cd" placeholder="КОД ИЗ ТЕРМИНАЛА (ТГ)"><br>
            <input type="password" id="pn" placeholder="ROOT PIN (SECRET)"><br>
            <button onclick="login()" style="width: 100%;">ESTABLISH CONNECTION</button>
            <p><a href="https://t.me/bot8876807144" target="_blank" style="color:#fff; font-size:10px;">[ ПОЛУЧИТЬ КЛЮЧ ]</a></p>
        </div>
    </div>

    <div id="reg_scr" class="overlay hidden">
        <h2 style="font-family:'Orbitron';">IDENTITY REGISTRATION</h2>
        <div style="width: 300px; padding: 20px; border: 1px solid var(--neon);">
            <input id="nm" placeholder="ИМЯ В СЕТИ"><br>
            <input id="unm" placeholder="@IDENTIFIER"><br>
            <button onclick="register()" style="width: 100%;">SAVE TO CORE</button>
        </div>
    </div>

    <div class="app">
        <div class="sidebar">
            <div style="padding:20px; border-bottom:1px solid var(--neon); font-family:'Orbitron'; font-size:12px; color: #fff;">ОПЕРАТИВНИКИ</div>
            <div id="user_list" style="flex:1; overflow-y:auto;">
                <div class="user-item" onclick="selectChat('all')">
                    <b style="color:var(--neon-p)">[ ГЛОБАЛЬНЫЙ КАНАЛ ]</b><br>
                    <small>Broadcast Active</small>
                </div>
            </div>
        </div>
        <div class="chat-area">
            <div id="adm_bar" class="hidden adm-btn" onclick="runAdm()">[ ADMIN OS TERMINAL ACTIVE ]</div>
            <div id="g_box"></div>
            <div id="msgs" style="flex:1; overflow-y:auto; padding:20px; display:flex; flex-direction:column;"></div>
            <div class="input-box">
                <input id="mi" placeholder="Введите пакет данных...">
                <button onclick="send()">SEND</button>
            </div>
        </div>
    </div>

    <script>
        let u = JSON.parse(localStorage.getItem('m_u'));
        if(u) start();

        async function login() {
            const p = document.getElementById('ph').value;
            const c = document.getElementById('cd').value;
            const pin = document.getElementById('pn').value;
            const res = await fetch('/api/verify', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({p, c, pin})});
            const d = await res.json();
            if(d.s) {
                u = {p, r: d.r};
                if(d.u) { u = {...u, ...d.u}; save(); }
                else { document.getElementById('auth_scr').classList.add('hidden'); document.getElementById('reg_scr').classList.remove('hidden'); }
            } else alert(d.m);
        }

        async function register() {
            u.n = document.getElementById('nm').value; u.un = document.getElementById('unm').value;
            await fetch('/api/reg', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(u)});
            save();
        }

        function save() { localStorage.setItem('m_u', JSON.stringify(u)); start(); }

        function start() {
            document.getElementById('auth_scr').classList.add('hidden');
            document.getElementById('reg_scr').classList.add('hidden');
            if(u.r === 'owner' || u.r === 'admin') document.getElementById('adm_bar').classList.remove('hidden');
            setInterval(load, 2000);
        }

        async function load() {
            const r = await fetch('/api/msg'); const d = await r.json();
            const list = document.getElementById('msgs');
            list.innerHTML = d.m.map(m => `
                <div class="msg-b ${m.f === u.p ? 'msg-out' : 'msg-in'}">
                    <div style="font-size:10px; color:${m.r==='owner'?'var(--neon-p)':'var(--neon)'}; margin-bottom:5px;"><b>${m.fn}</b> <span style="opacity:0.5">${m.tm}</span></div>
                    <div style="font-size:14px; line-height:1.4;">${m.t}</div>
                </div>
            `).join('');
            list.scrollTop = list.scrollHeight;
            document.getElementById('g_box').innerHTML = d.g ? `<div class="gift-alert" onclick="window.open('${d.g}')">🎁 ПОЛУЧЕН СЕКРЕТНЫЙ ПОДАРОК [ОТКРЫТЬ]</div>` : '';
            
            const ul = document.getElementById('user_list');
            d.u.forEach(user => {
                if(!document.getElementById('u_'+user.p) && user.p !== u.p) {
                    ul.innerHTML += `<div class="user-item" id="u_${user.p}"><b>${user.n}</b><br><small style="opacity:0.5">${user.un}</small></div>`;
                }
            });
        }

        async function send() {
            const i = document.getElementById('mi');
            if(!i.value) return;
            await fetch('/api/msg', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({f:u.p, fn:u.n, t:i.value, r:u.r})});
            i.value = '';
        }

        function runAdm() {
            const cmd = prompt("ADMIN COMMAND: /gift [url], /clear, /mute [phone], /setadmin [phone]");
            if(cmd) fetch('/api/admin', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({r:u.r, cmd})});
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML)

if __name__ == '__main__':
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
