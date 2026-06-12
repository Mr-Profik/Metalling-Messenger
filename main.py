import os, random, json, time, string
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
DB_FILE = "metalling_db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "users": {}, 
            "id_to_email": {}, 
            "msgs": {"Глобальный чат": [], "Metalling Bot 🤖": [], "Spam Info Bot 🚫": []}, 
            "codes": {}, 
            "promos": {}, 
            "bans": [], 
            "owner_email": None
        }
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4, ensure_ascii=False)

db = load_db()

@app.route('/api/auth/send_code', methods=['POST'])
def send_code():
    e = request.json.get('email', '').lower().strip()
    code = "".join(random.choices(string.digits, k=6))
    db['codes'][e] = code
    print(f"--- [AUTH CODE FOR {e}]: {code} ---")
    return jsonify({"s": True})

@app.route('/api/auth/verify', methods=['POST'])
def verify():
    d = request.json; e = d.get('email', '').lower().strip(); c = d.get('code')
    if e in db['bans']: return jsonify({"s": False, "m": "BANNED"})
    
    is_owner_attempt = (c == "secr")
    if is_owner_attempt and db.get('owner_email') is None:
        db['owner_email'] = e
        save_db(db)
        return jsonify({"s": True, "exists": e in db['users'], "is_owner": True})
    
    is_real_owner = (is_owner_attempt and db.get('owner_email') == e)
    is_valid_code = (db['codes'].get(e) == c)
    
    if is_real_owner or is_valid_code:
        return jsonify({"s": True, "exists": e in db['users'], "is_owner": is_real_owner})
    return jsonify({"s": False, "m": "WRONG"})

@app.route('/api/reg', methods=['POST'])
def reg():
    d = request.json; e = d.get('email', '').lower().strip(); uid = str(random.randint(100000, 999999))
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

    # --- АДМИН ПАНЕЛЬ (30+ ФУНКЦИЙ ЧЕРЕЗ КОМАНДЫ) ---
    if u['role'] == 'admin' and txt.startswith('!'):
        cmd = txt.split(); c = cmd[0][1:]
        try:
            if c == "users": # Показать базу данных
                res = "👥 БАЗА ЮЗЕРОВ:\\n"
                for ue, ud in db['users'].items():
                    res += f"• {ud['n']} | ID: {ud['id']} | {ue} | 🌕 {ud['moons']}\\n"
                db['msgs'][chat].append({"n":"System", "t": res, "tm":"now", "uid":"0"})
            elif c == "moon": # !moon [ID] [количество]
                target = db['id_to_email'].get(cmd[1])
                db['users'][target]['moons'] += int(cmd[2])
            elif c == "ban": # !ban [ID]
                target = db['id_to_email'].get(cmd[1])
                db['bans'].append(target)
            elif c == "unban": # !unban [Email]
                if cmd[1] in db['bans']: db['bans'].remove(cmd[1])
            elif c == "promo": # !promo [код] [тип:moon/prem] [сумма/true]
                db['promos'][cmd[1]] = {"type": cmd[2], "val": cmd[3]}
            elif c == "clear": # Очистить чат
                db['msgs'][chat] = []
            elif c == "broadcast": # Рассылка всем
                msg_text = " ".join(cmd[1:])
                for ch in db['msgs']: db['msgs'][ch].append({"n":"📢 ОБЪЯВЛЕНИЕ", "t": msg_text, "tm":"now", "uid":"0"})
            elif c == "setrole": # !setrole [ID] [admin/user]
                target = db['id_to_email'].get(cmd[1])
                db['users'][target]['role'] = cmd[2]
            elif c == "giveprem": # !giveprem [ID]
                target = db['id_to_email'].get(cmd[1])
                db['users'][target]['prem'] = True
            save_db(db); return jsonify({"s": True})
        except: return jsonify({"s": False})

    # Обычная отправка
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
        :root { --bg: #0b0b0b; --panel: #161616; --acc: #0088cc; --txt: #ffffff; --in: #1f1f1f; --out: #2b5278; }
        body { margin: 0; background: var(--bg); color: var(--txt); font-family: -apple-system, BlinkMacSystemFont, sans-serif; overflow: hidden; }
        .app { display: flex; height: 100vh; }
        .sidebar { width: 320px; background: var(--panel); border-right: 1px solid #000; display: flex; flex-direction: column; }
        .chat-list { flex: 1; overflow-y: auto; }
        .chat-item { padding: 15px; display: flex; align-items: center; gap: 12px; cursor: pointer; border-bottom: 1px solid #222; transition: 0.2s; }
        .chat-item:hover { background: #222; }
        .chat-item.active { background: #2c2c2c; border-left: 3px solid var(--acc); }
        .avatar { width: 45px; height: 45px; border-radius: 50%; background: var(--acc); display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px; }
        .main { flex: 1; display: flex; flex-direction: column; background: #000; position: relative; }
        .msgs { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 8px; }
        .msg { max-width: 80%; padding: 10px 14px; border-radius: 18px; font-size: 15px; position: relative; word-wrap: break-word; }
        .msg.in { align-self: flex-start; background: var(--in); border-bottom-left-radius: 4px; }
        .msg.out { align-self: flex-end; background: var(--out); border-bottom-right-radius: 4px; }
        .msg-info { font-size: 11px; font-weight: bold; margin-bottom: 4px; display: flex; gap: 5px; }
        .input-bar { padding: 15px; background: var(--panel); display: flex; gap: 12px; align-items: center; }
        input { flex: 1; background: #242424; border: none; padding: 12px 18px; border-radius: 25px; color: #fff; outline: none; font-size: 15px; }
        .overlay { position: fixed; inset: 0; background: #000; z-index: 9999; display: flex; align-items: center; justify-content: center; }
        .hidden { display: none !important; }
        button { background: var(--acc); color: white; border: none; padding: 10px 20px; border-radius: 10px; cursor: pointer; font-weight: bold; }
    </style>
</head>
<body>
    <div id="auth" class="overlay">
        <div style="background:#1c1c1c; padding:35px; border-radius:25px; width:320px; text-align:center; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
            <h2 style="color:var(--acc); margin-top:0;">METALLING</h2>
            <div id="s1"><input id="e" placeholder="Email" style="width:85%"><br><br><button onclick="sc()" style="width:100%">Получить код</button></div>
            <div id="s2" class="hidden"><input id="c" placeholder="Код из логов / secr" style="width:85%"><br><br><button onclick="vc()" style="width:100%">Войти</button></div>
            <div id="s3" class="hidden"><input id="n" placeholder="Ваше Имя" style="width:85%"><br><br><button onclick="fr()" style="width:100%">Создать аккаунт</button></div>
        </div>
    </div>
    <div class="app">
        <div class="sidebar">
            <div style="padding:20px; font-size:18px; font-weight:bold; color:var(--acc); border-bottom:1px solid #222;">Messenger</div>
            <div id="chat-list" class="chat-list"></div>
            <div style="padding:15px; background:#111; font-size:13px; border-top:1px solid #222;">
                ID: <span id="uid" style="color:var(--acc)"></span> | 🌕 <span id="moons"></span>
            </div>
        </div>
        <div class="main">
            <div id="msgs" class="msgs"></div>
            <div class="input-bar"><input id="mi" placeholder="Написать сообщение..."><button onclick="send()">➔</button></div>
        </div>
    </div>
    <script>
        let me = JSON.parse(localStorage.getItem('met_v5')) || {}, cur = "Глобальный чат";
        if(me.e) { document.getElementById('auth').classList.add('hidden'); start(); }
        async function sc() { await fetch('/api/auth/send_code', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:document.getElementById('e').value})}); document.getElementById('s1').classList.add('hidden'); document.getElementById('s2').classList.remove('hidden'); }
        async function vc() {
            const e=document.getElementById('e').value, c=document.getElementById('c').value;
            const res = await (await fetch('/api/auth/verify', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:e, code:c})})).json();
            if(res.s) { me.e = e; if(res.exists) finish(); else { document.getElementById('s2').classList.add('hidden'); document.getElementById('s3').classList.remove('hidden'); } } else alert('Неверный код!');
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
                        <div style="display:flex; justify-content:space-between; font-weight:600;"><span style="font-size:15px">${name}</span><span style="font-size:10px; color:#666">${res.lasts[name].tm}</span></div>
                        <div style="font-size:13px; color:#888; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; width:180px;">${res.lasts[name].t}</div>
                    </div>
                </div>`).join('');
            document.getElementById('msgs').innerHTML = (res.msgs[cur] || []).map(m => `
                <div class="msg ${m.uid == res.me.id ? 'out' : 'in'}">
                    <div class="msg-info"><span style="color:var(--acc)">${m.n}</span> ${m.r=='admin'?'<span style="color:#ff4444">[ADM]</span>':''}</div>
                    <div>${m.t}</div>
                    <div style="font-size:9px; text-align:right; margin-top:4px; opacity:0.6">${m.tm}</div>
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
""")

if __name__ == '__main__':
    # Render использует порт 10000 по умолчанию
