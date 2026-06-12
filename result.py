import os, random, json, time, string
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# --- DATABASE & STATE ---
DB_FILE = "metalling_ultimate.json"
user_flood_history = {} # {uid: [timestamps]}

def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "users": {}, "id_to_email": {}, 
            "msgs": {"Глобальный чат": [], "Bot Father 🤖": []}, 
            "codes": {}, "bots": {}, "mutes": {}
        }
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4, ensure_ascii=False)

db = load_db()

# --- ANTI-SPAM LOGIC ---
def check_spam(u):
    if u['role'] == 'admin' or u['e'] == 'admin': return "ok"
    uid = u['id']
    now = time.time()
    if uid not in user_flood_history: user_flood_history[uid] = []
    user_flood_history[uid] = [t for t in user_flood_history[uid] if now - t < 10]
    user_flood_history[uid].append(now)
    
    if len(user_flood_history[uid]) > 15:
        if not u.get('sw'):
            u['sw'] = True
            save_db(db)
            return "warn"
        else:
            db['mutes'][u['e']] = now + 86400
            u['sw'] = False
            save_db(db)
            return "mute"
    return "ok"

# --- BOT LOGIC ---
def bot_father(uid, chat, text):
    if chat != "Bot Father 🤖": return None
    t = text.lower()
    if "/newbot" in t:
        token = "MT-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
        bid = str(random.randint(5000, 9999))
        db['bots'][token] = {"owner": uid, "name": f"Bot_{bid}"}
        save_db(db)
        return f"🤖 Бот создан! Токен: `{token}`"
    return "Я Bot Father. Используй /newbot для создания бота."

# --- API ---
@app.route('/api/auth/send_code', methods=['POST'])
def send_code():
    e = request.json.get('email').lower().strip()
    code = "".join(random.choices(string.digits, k=6))
    db['codes'][e] = code
    print(f"--- [CODE FOR {e}]: {code} ---")
    return jsonify({"s": True})

@app.route('/api/auth/verify', methods=['POST'])
def verify():
    d = request.json; e = d.get('email').lower().strip(); c = d.get('code')
    is_owner = (c == "7777")
    return jsonify({"s": True, "exists": e in db['users'], "is_owner": is_owner})

@app.route('/api/reg', methods=['POST'])
def reg():
    d = request.json; e = d.get('email').lower().strip()
    uid = str(random.randint(100000, 999999))
    db['users'][e] = {
        "e": e, "n": d.get('n'), "id": uid, "moons": 0, "prem": False, 
        "role": "user", "banned": False, "sw": False
    }
    db['id_to_email'][uid] = e
    save_db(db); return jsonify({"s": True})

@app.route('/api/sync', methods=['POST'])
def sync():
    e = request.json.get('email', '').lower().strip()
    u = db['users'].get(e)
    if not u: return jsonify({"s": False})
    is_m = db['mutes'].get(e, 0) > time.time()
    return jsonify({
        "s": True, "me": u, "msgs": db['msgs'], "is_muted": is_m,
        "admin_data": list(db['users'].values()) if (u['role'] == 'admin' or e == 'admin') else None
    })

@app.route('/api/send', methods=['POST'])
def send():
    d = request.json; e = d.get('email').lower().strip(); chat = d.get('chat')
    u = db['users'].get(e)
    if db['mutes'].get(e, 0) > time.time(): return jsonify({"s": False, "m": "Spam Block!"})
    
    spam_res = check_spam(u)
    if spam_res == "warn": 
        db['msgs'][chat].append({"n": "System", "t": "⚠️ Не спамьте!", "tm": "Now", "uid": "0"})
        return jsonify({"s": False})
    if spam_res == "mute": return jsonify({"s": False, "m": "Вы получили Spam Block!"})

    msg = {"n": u['n'], "t": d.get('t'), "tm": time.strftime("%H:%M"), "uid": u['id'], "p": u['prem']}
    db['msgs'][chat].append(msg)
    
    br = bot_father(u['id'], chat, d.get('t'))
    if br: db['msgs'][chat].append({"n": "Bot Father 🤖", "t": br, "tm": "Now", "uid": "0", "p": True})
    
    save_db(db); return jsonify({"s": True})

@app.route('/api/admin/action', methods=['POST'])
def admin_action():
    d = request.json; tid = str(d.get('tid'))
    target_email = db['id_to_email'].get(tid)
    if not target_email: return jsonify({"s": False})
    u = db['users'][target_email]
    c = d.get('cmd')
    if c == "moon": u['moons'] += int(d.get('val', 0))
    if c == "prem": u['prem'] = True
    if c == "admin": u['role'] = 'admin'
    if c == "ban": u['banned'] = True
    save_db(db); return jsonify({"s": True})

# --- UI (iMe/Telegram Clone) ---
HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <title>Metalling Messenger</title>
    <style>
        :root { --bg: #0e0e0e; --side: #171717; --accent: #0088cc; --text: #fff; }
        body { margin: 0; background: var(--bg); color: var(--text); font-family: sans-serif; overflow: hidden; }
        .app { display: flex; height: 100vh; }
        .sidebar { width: 320px; background: var(--side); border-right: 1px solid #000; }
        .chat-area { flex: 1; display: flex; flex-direction: column; background: #000; }
        .msg-list { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 8px; background: #050505; }
        .bubble { padding: 10px 14px; border-radius: 16px; max-width: 75%; background: #212121; font-size: 15px; }
        .bubble.mine { align-self: flex-end; background: #2b5278; }
        .input-bar { padding: 10px; background: var(--side); display: flex; gap: 8px; }
        input { flex: 1; padding: 12px; background: #242424; border: 1px solid #333; border-radius: 20px; color: #fff; outline: none; }
        .hidden { display: none !important; }
        .screen { position: fixed; inset: 0; background: #000; z-index: 5000; display: flex; align-items: center; justify-content: center; }
        .card { background: #1c1c1c; padding: 30px; border-radius: 20px; width: 280px; text-align: center; }
        button { padding: 10px 20px; background: var(--accent); border: none; color: #fff; border-radius: 20px; cursor: pointer; font-weight: bold; }
        .admin-db { position: fixed; right: 10px; top: 10px; bottom: 80px; width: 320px; background: #111; border: 1px solid red; padding: 15px; display: none; z-index: 6000; overflow-y: auto; font-size: 10px; color: lime; }
    </style>
</head>
<body>

<div id="auth_scr" class="screen">
    <div class="card">
        <h2 style="color:var(--accent)">METALLING</h2>
        <div id="s1"><input id="ae" placeholder="Email"><button onclick="sendCode()" style="width:100%; margin-top:10px;">Далее</button></div>
        <div id="s2" class="hidden"><input id="ac" placeholder="Код (Владелец: 7777)"><button onclick="verify()" style="width:100%; margin-top:10px;">Войти</button></div>
        <div id="s3" class="hidden"><input id="an" placeholder="Имя"><button onclick="register()" style="width:100%; margin-top:10px;">Начать</button></div>
    </div>
</div>

<div class="app">
    <div class="sidebar">
        <div style="padding:20px; border-bottom:1px solid #222;">
            <b>Metalling iMe</b><br>
            <small id="me_id" style="color:var(--accent)"></small><br>
            <small style="color:#888;">Премка: 100р/мес (ЛС Владельцу)</small>
        </div>
        <div onclick="curChat='Глобальный чат';sync()" style="padding:15px; cursor:pointer;">🌍 Глобальный чат</div>
        <div onclick="curChat='Bot Father 🤖';sync()" style="padding:15px; cursor:pointer;">🤖 Bot Father</div>
        <div id="adm_btn" class="hidden" style="padding:20px;"><button onclick="toggleAdm()" style="background:red; width:100%;">БАЗА ДАННЫХ</button></div>
    </div>
    <div class="chat-area">
        <div id="spam_banner" style="background:#cf3c3c; color:#fff; padding:5px; text-align:center; display:none;">Вы в Spam Block!</div>
        <div id="msgs" class="msg-list"></div>
        <div class="input-bar" id="input_panel">
            <input id="mi" placeholder="Сообщение...">
            <button onclick="send()">-></button>
        </div>
    </div>
</div>

<div id="adm_panel" class="admin-db">
    <h3 style="color:red">OWNER DATABASE</h3>
    <input id="atid" placeholder="User ID">
    <input id="aval" placeholder="Value">
    <select id="acmd" style="width:100%; padding:10px; background:#222; color:#fff;">
        <option value="moon">Выдать Луны</option>
        <option value="prem">Выдать Premium</option>
        <option value="admin">Сделать Админом</option>
        <option value="ban">Бан</option>
    </select>
    <button onclick="admDo()" style="background:red; width:100%; margin-top:10px;">EXECUTE</button>
    <div id="adm_raw" style="margin-top:10px;"></div>
</div>

<script>
    let me = JSON.parse(localStorage.getItem('mt_u')) || {};
    let curChat = "Глобальный чат";

    if(me.email) { document.getElementById('auth_scr').classList.add('hidden'); start(); }

    async function sendCode() {
        await fetch('/api/auth/send_code', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:document.getElementById('ae').value})});
        document.getElementById('s1').classList.add('hidden'); document.getElementById('s2').classList.remove('hidden');
    }

    async function verify() {
        const e = document.getElementById('ae').value, c = document.getElementById('ac').value;
        const res = await (await fetch('/api/auth/verify', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:e, code:c})})).json();
        if(res.s) {
            me.email = e; if(c === '7777') me.owner = true;
            if(res.exists) login();
            else { document.getElementById('s2').classList.add('hidden'); document.getElementById('s3').classList.remove('hidden'); }
        } else alert("Ошибка");
    }

    async function register() {
        await fetch('/api/reg', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:me.email, n:document.getElementById('an').value})});
        login();
    }

    function login() { localStorage.setItem('mt_u', JSON.stringify(me)); location.reload(); }
    function start() { setInterval(sync, 2000); sync(); }

    async function sync() {
        const res = await (await fetch('/api/sync', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:me.email})})).json();
        if(!res.s) return;
        
        document.getElementById('me_id').innerText = `ID: ${res.me.id} | Луны: ${res.me.moons}`;
        if(res.me.role === 'admin' || me.owner) document.getElementById('adm_btn').classList.remove('hidden');
        
        const banner = document.getElementById('spam_banner');
        if(res.is_muted) { banner.style.display='block'; document.getElementById('mi').disabled=true; }
        else { banner.style.display='none'; document.getElementById('mi').disabled=false; }

        const chatMsgs = res.msgs[curChat] || [];
        document.getElementById('msgs').innerHTML = chatMsgs.map(m => `
            <div class="bubble ${m.uid == res.me.id ? 'mine' : ''}">
                <div style="font-size:10px; color:var(--accent)">${m.n} (ID:${m.uid}) ${m.p?'🌙':''}</div>
                ${m.t}
            </div>
        `).join('');
        if(res.admin_data) document.getElementById('adm_raw').innerText = JSON.stringify(res.admin_data, null,