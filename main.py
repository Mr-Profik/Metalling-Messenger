import os, random, json, time, string
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
DB_FILE = "metalling_messenger_v5.json"
flood_tracker = {}

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "id_to_email": {}, "msgs": {"Глобальный чат": [], "Metalling Bot 🤖": [], "Spam Info Bot 🚫": []}, "mutes": {}, "codes": {}, "promos": {}, "bans": [], "owner_email": None}
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4, ensure_ascii=False)

db = load_db()

@app.route('/api/auth/send_code', methods=['POST'])
def send_code():
    e = request.json.get('email', '').lower().strip()
    code = "".join(random.choices(string.digits, k=6))
    db['codes'][e] = code
    print(f"--- [КОД ДЛЯ {e}]: {code} ---") # Код виден в логах сервера
    return jsonify({"s": True})

@app.route('/api/auth/verify', methods=['POST'])
def verify():
    d = request.json; e = d.get('email', '').lower().strip(); c = d.get('code')
    if e in db['bans']: return jsonify({"s": False, "m": "BANNED"})
    
    # ПРОВЕРКА НА ВЛАДЕЛЬЦА С НОВЫМ КОДОМ 'secr'
    is_owner_attempt = (c == "secr")
    
    # Если владельца еще нет — первый кто ввел 'secr' закрепляет за собой этот статус
    if is_owner_attempt and db.get('owner_email') is None:
        db['owner_email'] = e
        save_db(db)
        return jsonify({"s": True, "exists": e in db['users'], "is_owner": True})
    
    # Если владелец уже назначен, проверяем, совпадает ли его почта
    is_real_owner = (is_owner_attempt and db.get('owner_email') == e)
    
    # Если код обычный числовой из логов
    is_valid_code = (db['codes'].get(e) == c)
    
    if is_real_owner or is_valid_code:
        return jsonify({"s": True, "exists": e in db['users'], "is_owner": is_real_owner})
    return jsonify({"s": False, "m": "WRONG CODE"})

@app.route('/api/reg', methods=['POST'])
def reg():
    d = request.json; e = d.get('email', '').lower().strip(); uid = str(random.randint(100000, 999999))
    # Назначаем роль admin, если почта совпадает с почтой владельца
    role = "admin" if e == db.get('owner_email') else "user"
    db['users'][e] = {"e": e, "n": d.get('n'), "id": uid, "moons": 0, "prem": False, "role": role}
    db['id_to_email'][uid] = e; save_db(db); return jsonify({"s": True})

@app.route('/api/sync', methods=['POST'])
def sync():
    e = request.json.get('email', '').lower().strip(); u = db['users'].get(e)
    if not u or e in db['bans']: return jsonify({"s": False})
    lasts = {name: (msgs[-1] if msgs else {"t": "...", "tm": ""}) for name, msgs in db['msgs'].items()}
    return jsonify({"s": True, "me": u, "msgs": db['msgs'], "lasts": lasts})

@app.route('/api/send', methods=['POST'])
def send():
    d = request.json; e = d.get('email', '').lower().strip(); chat = d.get('chat'); txt = d.get('t', '').strip()
    u = db['users'].get(e)
    if not u or e in db['bans']: return jsonify({"s": False})

    # АДМИН-КОМАНДЫ
    if u['role'] == 'admin' and txt.startswith('!'):
        cmd = txt.split(); c = cmd[0][1:]
        try:
            if c == "users":
                u_list = "👥 БАЗА ПОЛЬЗОВАТЕЛЕЙ:\\n"
                for ue, ud in db['users'].items():
                    u_list += f"• {ud['n']} | ID: {ud['id']} | {ue} | 🌕 {ud['moons']}\\n"
                db['msgs'][chat].append({"n":"System", "t": u_list, "tm":"now", "uid":"0"})
            elif c == "moon": db['users'][db['id_to_email'][cmd[1]]]['moons'] += int(cmd[2])
            elif c == "ban": db['bans'].append(db['id_to_email'][cmd[1]])
            elif c == "promo": db['promos'][cmd[1]] = {"type": cmd[2], "val": cmd[3]}
            elif c == "clear": db['msgs'][chat] = []
            elif c == "broadcast":
                for ch in db['msgs']: db['msgs'][ch].append({"n":"📢 ОПОВЕЩЕНИЕ", "t": " ".join(cmd[1:]), "tm":"now", "uid":"0"})
            save_db(db); return jsonify({"s": True})
        except: return jsonify({"s": False})

    db['msgs'][chat].append({"n": u['n'], "t": txt, "tm": time.strftime("%H:%M"), "uid": u['id'], "p": u['prem'], "r": u['role']})
    save_db(db); return jsonify({"s": True})

@app.route('/')
def index():
    return render_template_string("""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Metalling Messenger</title>
    <style>
        :root { --bg: #0e0e0e; --panel: #171717; --acc: #0088cc; --txt: #fff; --in: #212121; --out: #2b5278; }
        body { margin: 0; background: var(--bg); color: var(--txt); font-family: -apple-system, sans-serif; overflow: hidden; }
        .app { display: flex; height: 100vh; }
        .sidebar { width: 350px; background: var(--panel); border-right: 1px solid #000; display: flex; flex-direction: column; }
        .chat-list { flex: 1; overflow-y: auto; }
        .chat-item { padding: 12px 15px; display: flex; align-items: center; gap: 12px; cursor: pointer; border-bottom: 1px solid #222; }
        .chat-item.active { background: #2c2c2c; border-left: 4px solid var(--acc); }
        .avatar { width: 48px; height: 48px; border-radius: 50%; background: var(--acc); display: flex; align-items: center; justify-content: center; font-weight: bold; }
        .main { flex: 1; display: flex; flex-direction: column; background: #000; }
        .msgs { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 10px; }
        .msg { max-width: 75%; padding: 8px 12px; border-radius: 16px; font-size: 15px; white-space: pre-wrap; }
        .msg.in { align-self: flex-start; background: var(--in); }
        .msg.out { align-self: flex-end; background: var(--out); }
        .input-bar { padding: 12px; background: var(--panel); display: flex; gap: 10px; }
        input { flex: 1; background: #242424; border: 1px solid #333; padding: 12px; border-radius: 20px; color: #fff; outline: none; }
        .overlay { position: fixed; inset: 0; background: #000; z-index: 9999; display: flex; align-items: center; justify-content: center; }
        .hidden { display: none !important; }
    </style>
</head>
<body>
    <div id="auth" class="overlay">
        <div style="background:#1c1c1c; padding:40px; border-radius:30px; width:300px; text-align:center;">
            <h2 style="color:var(--acc)">METALLING</h2>
            <div id="s1"><input id="e" placeholder="Email"><br><br><button onclick="sc()" style="width:100%; padding:12px; background:var(--acc); color:#fff; border:none; border-radius:10px;">Далее</button></div>
            <div id="s2" class="hidden"><input id="c" placeholder="Код"><br><br><button onclick="vc()" style="width:100%; padding:12px; background:var(--acc); color:#fff; border:none; border-radius:10px;">Войти</button></div>
            <div id="s3" class="hidden"><input id="n" placeholder="Имя"><br><br><button onclick="fr()" style="width:100%; padding:12px; background:var(--acc); color:#fff; border:none; border-radius:10px;">Начать</button></div>
        </div>
    </div>
    <div class="app">
        <div class="sidebar">
            <div style="padding:15px; font-weight:bold; color:var(--acc);">Metalling Messenger</div>
            <div id="chat-list" class="chat-list"></div>
            <div style="padding:15px; border-top:1px solid #222; font-size:12px;">ID: <b id="uid"></b> | 🌕 <b id="moons"></b></div>
        </div>
        <div class="main">
            <div id="msgs" class="msgs"></div>
            <div class="input-bar"><input id="mi" placeholder="Сообщение..."><button onclick="send()" style="background:var(--acc); color:#fff; border:none; border-radius:50%; width:40px; height:40px;">➔</button></div>
        </div>
    </div>
    <script>
        let me = JSON.parse(localStorage.getItem('met_v5')) || {}, cur = "Глобальный чат";
        if(me.e) { document.getElementById('auth').classList.add('hidden'); start(); }
        async function sc() { await fetch('/api/auth/send_code', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:document.getElementById('e').value})}); document.getElementById('s1').classList.add('hidden'); document.getElementById('s2').classList.remove('hidden'); }
        async function vc() {
            const e=document.getElementById('e').value, c=document.getElementById('c').value;
            const res = await (await fetch('/api/auth/verify', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:e, code:c})})).json();
            if(res.s) { me.e = e; if(res.exists) finish(); else { document.getElementById('s2').classList.add('hidden'); document.getElementById('s3').classList.remove('hidden'); } } else { alert('Ошибка кода'); }
        }
        async function fr() { await fetch('/api/reg', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:me.e, n:document.getElementById('n').value})}); finish(); }
        function finish() { localStorage.setItem('met_v5', JSON.stringify(me)); location.reload(); }
        function start() { setInterval(sync, 2000); sync(); }
        function sw(n) { cur = n; sync(); }
        async function sync() {
            const res = await (await fetch('/api/sync', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:me.e})})).json();
            if(!res.s) return;
            document.getElementById('uid').innerText = res.me.id;
            document.getElementById('moons').innerText = res.me.moons;
            document.getElementById('chat-list').innerHTML = Object.keys(res.msgs).map(name => `
                <div class="chat-item ${cur==name?'active':''}" onclick="sw('${name}')">
                    <div class="avatar">${name[0]}</div>
                    <div style="flex:1">
                        <div style="display:flex; justify-content:space-between; font-weight:bold;"><span>${name}</span><span style="font-size:10px">${res.lasts[name].tm}</span></div>
                        <div style="font-size:13px; color:#888">${res.lasts[name].t.substring(0,25)}...</div>
                    </div>
                </div>`).join('');
            document.getElementById('msgs').innerHTML = (res.msgs[cur] || []).map(m => `
                <div class="msg ${m.uid == res.me.id ? 'out' : 'in'}">
                    <div style="font-size:11px; color:var(--acc); font-weight:bold">${m.n}</div>
                    ${m.t}
                    <div style="font-size:9px; text-align:right; opacity:0.5">${m.tm}</div>
                </div>`).join('');
        }
        async function send() {
            const i = document.getElementById('mi'); if(!i.value) return;
            await fetch('/api/send', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:me.e, chat:cur, t:i.value})});
            i.value = ''; sync();
        }
    </script>
</body>
</html>
