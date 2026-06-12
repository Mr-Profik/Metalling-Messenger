import os, random, json, time, string
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
DB_FILE = "metalling_database.json"

def ld():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "id_to_email": {}, "msgs": {"Глобальный чат": [], "Metalling News 📢": []}, "codes": {}, "bans": [], "owner": None}
    with open(DB_FILE, 'r') as f: return json.load(f)

def sv(d):
    with open(DB_FILE, 'w') as f: json.dump(d, f, indent=4, ensure_ascii=False)

db = ld()

@app.route('/api/auth/send_code', methods=['POST'])
def sc():
    e = request.json.get('email', '').lower().strip()
    c = "".join(random.choices(string.digits, k=6))
    db['codes'][e] = c
    print(f"\n🌙 [METALLING AUTH] КОД ДЛЯ {e}: {c}\n") 
    return jsonify({"s": True})

@app.route('/api/auth/verify', methods=['POST'])
def vc():
    d = request.json; e = d.get('email', '').lower().strip(); c = d.get('code')
    if e in db['bans']: return jsonify({"s": False, "m": "BAN"})
    is_o = (c == "secr")
    if is_o and db['owner'] is None:
        db['owner'] = e; sv(db); return jsonify({"s": True, "exists": e in db['users'], "is_owner": True})
    is_ro = (is_o and db['owner'] == e)
    if is_ro or db['codes'].get(e) == c:
        return jsonify({"s": True, "exists": e in db['users'], "is_owner": is_ro})
    return jsonify({"s": False})

@app.route('/api/reg', methods=['POST'])
def rg():
    d = request.json; e = d.get('email', '').lower().strip(); uid = str(random.randint(100000, 999999))
    r = "admin" if e == db['owner'] else "user"
    db['users'][e] = {"e": e, "n": d.get('n'), "id": uid, "moons": 0, "role": r}
    db['id_to_email'][uid] = e; sv(db); return jsonify({"s": True})

@app.route('/api/sync', methods=['POST'])
def sy():
    e = request.json.get('email', '').lower().strip(); u = db['users'].get(e)
    if not u or e in db['bans']: return jsonify({"s": False})
    ls = {n: (m[-1] if m else {"t": "...", "tm": ""}) for n, m in db['msgs'].items()}
    return jsonify({"s": True, "me": u, "msgs": db['msgs'], "lasts": ls})

@app.route('/api/send', methods=['POST'])
def sn():
    d = request.json; e = d.get('email', '').lower().strip(); ch = d.get('chat'); t = d.get('t', '').strip()
    u = db['users'].get(e)
    if not u or e in db['bans']: return jsonify({"s": False})

    if u['role'] == 'admin' and t.startswith('!'):
        cmd = t.split(); c = cmd[0][1:]
        try:
            if c == "users":
                res = "📊 **METALLING USERS:**\n" + "\n".join([f"ID: `{v['id']}` | {v['n']} | 🌙 {v.get('moons',0)}" for k,v in db['users'].items()])
                db['msgs'][ch].append({"n":"System", "t": res, "tm":"now", "uid":"0"})
            elif c == "moon": 
                target_email = db['id_to_email'][cmd[1]]
                db['users'][target_email]['moons'] = db['users'][target_email].get('moons', 0) + int(cmd[2])
            elif c == "ban": db['bans'].append(db['id_to_email'][cmd[1]])
            elif c == "setadmin": db['users'][db['id_to_email'][cmd[1]]]['role'] = "admin"
            sv(db); return jsonify({"s": True})
        except: pass

    db['msgs'][ch].append({"n": u['n'], "t": t, "tm": time.strftime("%H:%M"), "uid": u['id'], "role": u['role']})
    sv(db); return jsonify({"s": True})

@app.route('/')
def idx():
    return render_template_string("""
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Metalling Messenger</title><style>
:root{--bg:#0e1621;--side:#17212b;--acc:#2b5278;--txt:#fff;--msg-in:#182533;--msg-out:#2b5278;--blue:#50a2e9;}
body{margin:0;background:var(--bg);color:var(--txt);font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;display:flex;height:100vh;overflow:hidden;}
.side{width:300px;background:var(--side);border-right:1px solid #000;display:flex;flex-direction:column;}
.chat-list{flex:1;overflow-y:auto;}
.chat-item{padding:10px 15px;display:flex;align-items:center;gap:12px;cursor:pointer;}
.chat-item:hover{background:#232e3c;}
.chat-item.active{background:var(--blue);}
.avatar{width:45px;height:45px;border-radius:50%;background:#50a2e9;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:16px;}
.main{flex:1;display:flex;flex-direction:column;background:#0e1621;}
.msgs{flex:1;overflow-y:auto;padding:15px;display:flex;flex-direction:column;gap:8px;background:url('https://i.ibb.co/5G7Y6Yv/tg-bg.png');}
.m-wrap{max-width:80%;padding:6px 12px;border-radius:12px;font-size:14px;position:relative;color:#fff;}
.m-in{align-self:flex-start;background:var(--msg-in);border-bottom-left-radius:2px;}
.m-out{align-self:flex-end;background:var(--msg-out);border-bottom-right-radius:2px;}
.m-name{font-size:12px;font-weight:bold;color:var(--blue);margin-bottom:2px;}
.m-time{font-size:10px;text-align:right;opacity:0.5;margin-top:4px;}
.input-area{padding:10px;background:var(--side);display:flex;gap:10px;align-items:center;}
input{flex:1;background:transparent;border:none;padding:10px;color:#fff;outline:none;font-size:16px;}
.ov{position:fixed;inset:0;background:var(--bg);z-index:99;display:flex;align-items:center;justify-content:center;} .hidden{display:none;}
button{background:transparent;color:var(--blue);border:none;padding:10px;cursor:pointer;font-weight:bold;font-size:16px;}
.moon-count{font-size:11px;color:#f1c40f;margin-left:5px;}
</style></head><body>
<div id="auth" class="ov"><div style="width:100%;max-width:300px;text-align:center;">
<img src="https://i.ibb.co/hV79G8L/logo.png" width="80" style="border-radius:20px;margin-bottom:20px;">
<h2 style="margin-bottom:30px;">Metalling</h2>
<div id="s1"><input id="e" placeholder="Ваш Email" style="border-bottom:2px solid var(--blue);width:100%"><br><br><button onclick="sc()">ДАЛЕЕ</button></div>
<div id="s2" class="hidden"><input id="c" placeholder="Код из логов" style="border-bottom:2px solid var(--blue);width:100%"><br><br><button onclick="vc()">ВОЙТИ</button></div>
<div id="s3" class="hidden"><input id="n" placeholder="Ваше имя" style="border-bottom:2px solid var(--blue);width:100%"><br><br><button onclick="fr()">НАЧАТЬ</button></div>
</div></div>
<div class="side"><div style="padding:15px;font-weight:bold;font-size:16px;display:flex;justify-content:space-between;">Metalling <span id="my_moons" style="color:#f1c40f">🌙 0</span></div><div id="cl" class="chat-list"></div></div>
<div class="main"><div id="ms" class="msgs"></div><div class="input-area"><input id="mi" placeholder="Сообщение..."><button onclick="sn()">ОТПР.</button></div></div>
<script>
let me={},cur="Глобальный чат";
async function sc(){await fetch('/api/auth/send_code',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('e').value})});document.getElementById('s1').classList.add('hidden');document.getElementById('s2').classList.remove('hidden');}
async function vc(){
    const e=document.getElementById('e').value,c=document.getElementById('c').value;
    const r=await(await fetch('/api/auth/verify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:e,code:c})})).json();
    if(r.s){me.e=e;if(r.exists)fn();else{document.getElementById('s2').classList.add('hidden');document.getElementById('s3').classList.remove('hidden');}}else alert('Неверный код!');
}
async function fr(){await fetch('/api/reg',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:me.e,n:document.getElementById('n').value})});fn();}
function fn(){localStorage.setItem('met_v7',JSON.stringify(me));location.reload();}
function start(){me=JSON.parse(localStorage.getItem('met_v7')||'{}');if(!me.e)return;document.getElementById('auth').classList.add('hidden');setInterval(sy,2000);sy();}
async function sy(){
    const r=await(await fetch('/api/sync',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:me.e})})).json();
    if(!r.s)return;
    document.getElementById('my_moons').innerText = '🌙 ' + r.me.moons;
    document.getElementById('cl').innerHTML=Object.keys(r.msgs).map(n=>`<div class="chat-item ${cur==n?'active':''}" onclick="cur='${n}';sy()">
    <div class="avatar">${n[0]}</div><div style="flex:1"><div style="display:flex;justify-content:space-between"><b>${n.slice(0,15)}</b></div><small style="opacity:0.6;font-size:12px;">${r.lasts[n].t.slice(0,20)}...</small></div></div>`).join('');
    document.getElementById('ms').innerHTML=r.msgs[cur].map(m=>`<div class="m-wrap ${m.uid==r.me.id?'m-out':'m-in'}">
    <div class="m-name">${m.n} ${m.role=='admin'?'<span style="color:#f1c40f">★</span>':''}</div><div>${m.t}</div><div class="m-time">${m.tm}</div></div>`).join('');
}
async function sn(){const i=document.getElementById('mi');if(!i.value)return;await fetch('/api/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:me.e,chat:cur,t:i.value})});i.value='';sy();document.getElementById('ms').scrollTo(0,99999);}
start();
</script></body></html>
""")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)