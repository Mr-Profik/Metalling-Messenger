import os, random, json, time, string
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# --- CONFIG ---
ADMIN_KEY = "7777"
# Путь для сохранения базы данных (адаптировано под Render)
DB_FILE = "metalling_db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "users": {}, # email: {data}
            "msgs": {"Global": [], "Metaling Bot": [], "NomadHost": [], "Geo STUDIO": []},
            "bots": {}, "bans": [], "mutes": [], "gifts": []
        }
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4, ensure_ascii=False)

db = load_db()

# --- ADMIN ACTIONS ---
def run_admin_cmd(cmd_text):
    p = cmd_text.split()
    if not p: return "No command"
    c = p[0].lower()
    try:
        target = p[1] if len(p) > 1 else None
        if c == "/add_moon" and len(p)>2:
            db['users'][target]['moons'] += int(p[2]); res = f"Added {p[2]} moons to {target}"
        elif c == "/set_prem":
            db['users'][target]['prem'] = True; res = f"Premium granted to {target}"
        elif c == "/ban":
            db['bans'].append(target); res = f"User {target} banned"
        elif c == "/set_admin":
            db['users'][target]['r'] = 'admin'; res = f"{target} is now Admin"
        elif c == "/clear_chat":
            db['msgs'][target] = []; res = f"Chat {target} cleared"
        else: res = "Unknown command"
        save_db(db); return res
    except: return "Error"

# --- API ---
@app.route('/api/sync', methods=['POST'])
def sync():
    d = request.json; e = d.get('e'); chat = d.get('chat', 'Global')
    u = db['users'].get(e)
    
    # Список чатов (как на скрине)
    chat_list = []
    for c_name in db['msgs'].keys():
        last = db['msgs'][c_name][-1] if db['msgs'][c_name] else {"t": "No messages", "tm": "00:00"}
        chat_list.append({"n": c_name, "l": last['t'][:25], "tm": last['tm'], "un": random.randint(1, 10)})

    return jsonify({
        "msgs": db['msgs'].get(chat, []),
        "me": u,
        "chats": chat_list,
        "admin_db": db['users'] if e == ADMIN_KEY else None 
    })

@app.route('/api/send', methods=['POST'])
def send():
    d = request.json; e = d.get('e'); chat = d.get('chat'); text = d.get('t')
    if e in db['bans'] or e in db['mutes']: return jsonify({"s": False})
    u = db['users'].get(e)
    msg = {"n": u['n'], "t": text, "tm": time.strftime("%H:%M"), "uid": u['id'], "p": u['prem']}
    db['msgs'][chat].append(msg)
    
    if chat == "Metaling Bot" and "/newbot" in text.lower():
        token = "MT-" + "".join(random.choices(string.digits, k=8))
        db['msgs'][chat].append({"n": "Metaling Bot", "t": f"🤖 Bot Created! Token: `{token}`", "tm": "Now", "uid": 0, "p": True})
            
    save_db(db); return jsonify({"s": True})

@app.route('/api/reg', methods=['POST'])
def reg():
    d = request.json; e = d.get('e')
    db['users'][e] = {
        "e": e, "ph": d.get('ph'), "n": d.get('n'), "id": random.randint(1000, 9999),
        "moons": 7777 if e == ADMIN_KEY else 100,
        "prem": True if e == ADMIN_KEY else False,
        "r": "owner" if e == ADMIN_KEY else "user"
    }
    save_db(db); return jsonify({"s": True})

@app.route('/api/admin_action', methods=['POST'])
def admin_action():
    d = request.json
    if d.get('e') != ADMIN_KEY: return jsonify({"s": False})
    return jsonify({"s": True, "res": run_admin_cmd(d.get('cmd'))})

# --- UI ---
HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <title>Metalling Messenger</title>
    <style>
        :root { --bg: #000; --side: #000; --accent: #007aff; --text: #fff; --sub: #8e8e93; --divider: #1c1c1e; }
        body { margin: 0; background: var(--bg); color: var(--text); font-family: -apple-system, sans-serif; overflow: hidden; }
        .sidebar { width: 100%; max-width: 400px; border-right: 1px solid var(--divider); display: flex; flex-direction: column; height: 100vh; }
        .chat-item { display: flex; align-items: center; padding: 12px 15px; cursor: pointer; border-bottom: 0.5px solid var(--divider); }
        .avatar { width: 52px; height: 52px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 12px; font-size: 20px; }
        .chat-name { font-weight: 600; font-size: 16px; }
        .badge { background: var(--accent); color: #fff; font-size: 12px; padding: 2px 7px; border-radius: 10px; }
        .chat-window { flex: 1; display: none; flex-direction: column; background: #000; position: fixed; inset: 0; z-index: 100; }
        .chat-window.active { display: flex; }
        .messages { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 10px; background: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png'); background-size: cover; }
        .msg { padding: 8px 12px; border-radius: 15px; max-width: 75%; background: #1c1c1e; }
        .msg.mine { align-self: flex-end; background: #005a9e; }
        .admin-os { position: fixed; inset: 10px; background: #050505; border: 1px solid #333; z-index: 1000; border-radius: 15px; padding: 15px; display: none; overflow-y: auto; }
        .hidden { display: none !important; }
        .bottom-nav { height: 60px; border-top: 1px solid var(--divider); display: flex; justify-content: space-around; align-items: center; position: fixed; bottom: 0; width: 100%; background: #000; }
    </style>
</head>
<body>

<div id="auth_scr" style="position:fixed; inset:0; z-index:2000; background:#000; display:flex; align-items:center; justify-content:center; flex-direction:column;">
    <h1 style="color:var(--accent); letter-spacing:4px;">METALLING</h1>
    <input id="ae" placeholder="Email (7777 for Owner)" style="width:250px; padding:12px; margin:5px; background:#111; border:1px solid #333; color:#fff; border-radius:8px;">
    <input id="an" placeholder="Name" style="width:250px; padding:12px; margin:5px; background:#111; border:1px solid #333; color:#fff; border-radius:8px;">
    <button onclick="doReg()" style="width:250px; padding:12px; background:var(--accent); border:none; color:#fff; border-radius:8px; font-weight:bold;">ENTER</button>
</div>

<div class="sidebar">
    <div style="padding:15px; display:flex; justify-content:space-between; align-items:center;">
        <span style="color:var(--accent)">Изм.</span>
        <b>Чаты</b>
        <span id="adm_icon" onclick="openAdmin()" class="hidden" style="cursor:pointer;">⚙️</span>
    </div>
    <div id="chat_list_view"></div>
</div>

<div id="chat_win" class="chat-window">
    <div style="padding:10px; border-bottom:1px solid var(--divider); display:flex; align-items:center;">
        <span onclick="closeChat()" style="color:var(--accent); cursor:pointer;">❮ Назад</span>
        <b id="win_title" style="margin-left:20px;"></b>
    </div>
    <div id="msg_box" class="messages"></div>
    <div style="padding:10px; display:flex; gap:10px; background:#000;">
        <input id="mi" placeholder="Сообщение" style="flex:1; padding:10px; background:#1c1c1e; border:none; color:#fff; border-radius:20px;">
        <button onclick="send()" style="background:var(--accent); border:none; color:#fff; border-radius:50%; width:35px; height:35px;">↑</button>
    </div>
</div>

<div id="admin_os" class="admin-os">
    <div style="display:flex; justify-content:space-between;">
        <h2 style="color:red;">OWNER OS</h2>
        <button onclick="document.getElementById('admin_os').style.display='none'">EXIT</button>
    </div>
    <input id="acmd" placeholder="Command..." style="width:70%; padding:10px; background:#000; color:lime; border:1px solid #444;">
    <button onclick="runAdmin()">RUN</button>
    <div id="db_view" style="font-size:10px; margin-top:10px; color:lime; font-family:monospace;"></div>
</div>

<div class="bottom-nav">
    <div style="text-align:center; color:var(--sub); font-size:10px;">👤<br>Контакты</div>
    <div style="text-align:center; color:var(--accent); font-size:10px;">💬<br>Чаты</div>
    <div style="text-align:center; color:var(--sub); font-size:10px;">⚙️<br>Настройки</div>
</div>

<script>
    let me = JSON.parse(localStorage.getItem('mt_u')) || {};
    let cur = "";

    if(me.e) { document.getElementById('auth_scr').classList.add('hidden'); start(); }

    async function doReg() {
        me = {e: document.getElementById('ae').value, n: document.getElementById('an').value};
        await fetch('/api/reg', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(me)});
        localStorage.setItem('mt_u', JSON.stringify(me)); location.reload();
    }

    function start() { 
        if(me.e === '7777') document.getElementById('adm_icon').classList.remove('hidden');
        setInterval(sync, 2000); sync(); 
    }

    async function sync() {
        const res = await (await fetch('/api/sync', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({e:me.e, chat:cur})})).json();
        document.getElementById('chat_list_view').innerHTML = res.chats.map(c => `
            <div class="chat-item" onclick="openChat('${c.n}')">
                <div class="avatar" style="background:${getClr(c.n)}">${c.n[0]}</div>
                <div style="flex:1">
                    <div style="display:flex; justify-content:space-between;"><span class="chat-name">${c.n}</span><span style="color:var(--sub); font-size:12px;">${c.tm}</span></div>
                    <div style="display:flex; justify-content:space-between;"><span style="color:var(--sub); font-size:14px;">${c.l}</span><span class="badge">${c.un}</span></div>
                </div>
            </div>
        `).join('');

        if(cur) {
            document.getElementById('msg_box').innerHTML = res.msgs.map(m => `
                <div class="msg ${m.uid == res.me.id ? 'mine' : ''}">
                    <div style="font-size:11px; color:var(--accent); font-weight:bold;">${m.n} ${m.p?'🌙':''} (ID-${m.uid})</div>
                    ${m.t}
                </div>
            `).join('');
        }
        if(res.admin_db) document.getElementById('db_view').innerText = JSON.stringify(res.admin_db, null, 2);
    }

    function openChat(n) { cur = n; document.getElementById('win_title').innerText = n; document.getElementById('chat_win').classList.add('active'); sync(); }
    function closeChat() { cur = ""; document.getElementById('chat_win').classList.remove('active'); }
    async function send() {
        const i = document.getElementById('mi'); if(!i.value) return;
        await fetch('/api/send', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({e:me.e, chat:cur, t:i.value})});
        i.value = ''; sync();
    }
    function openAdmin() { document.getElementById('admin_os').style.display='block'; }
    async function runAdmin() {
        const res = await (await fetch('/api/admin_action', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({e:me.e, cmd:document.getElementById('acmd').value})})).json();
        alert(res.res); sync();
    }
    function getClr(s) { const c = ['#FF3B30', '#4CD964', '#007AFF', '#5856D6', '#FF9500']; return c[s.length % c.length]; }
</script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))