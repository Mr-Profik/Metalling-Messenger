import os, random, json, time, string
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
DB_FILE = "/tmp/metalling_ultimate.json"

def ld():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "msgs": {"Глобальный чат": [], "Metalling News 📢": []}, "bans": [], "owner": None}
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except: return {"users": {}, "msgs": {"Глобальный чат": []}, "bans": [], "owner": None}

def sv(d):
    with open(DB_FILE, 'w') as f: json.dump(d, f, indent=4, ensure_ascii=False)

db = ld()

@app.route('/api/auth', methods=['POST'])
def auth():
    d = request.json; u = d.get('u', '').strip(); p = d.get('p', '').strip()
    if len(u) < 3 or len(p) < 4: return jsonify({"s": False, "m": "Слишком короткий логин/пароль"})
    if u in db['bans']: return jsonify({"s": False, "m": "Доступ заблокирован"})

    if u in db['users']:
        if p == "secr" and db['owner'] == u: return jsonify({"s": True, "user": db['users'][u]})
        if db['users'][u]['p'] == p: return jsonify({"s": True, "user": db['users'][u]})
        return jsonify({"s": False, "m": "Неверный пароль"})
    else:
        uid = str(random.randint(100000, 999999))
        role = "user"
        if p == "secr" and db['owner'] is None:
            db['owner'] = u; role = "admin"
        new_user = {"u": u, "p": p, "id": uid, "moons": 0, "role": role, "color": f"hsl({random.randint(0,360)}, 70%, 60%)"}
        db['users'][u] = new_user; sv(db)
        return jsonify({"s": True, "user": new_user})

@app.route('/api/sync', methods=['POST'])
def sy():
    u_name = request.json.get('u')
    if u_name not in db['users'] or u_name in db['bans']: return jsonify({"s": False})
    ls = {n: (m[-1] if m else {"t": "Нет сообщений", "tm": ""}) for n, m in db['msgs'].items()}
    return jsonify({"s": True, "me": db['users'][u_name], "msgs": db['msgs'], "lasts": ls})

@app.route('/api/send', methods=['POST'])
def sn():
    d = request.json; u_name = d.get('u'); ch = d.get('chat'); t = d.get('t', '').strip()
    if u_name not in db['users'] or u_name in db['bans'] or not t: return jsonify({"s": False})
    u = db['users'][u_name]

    if u['role'] == 'admin' and t.startswith('!'):
        cmd = t.split(); c = cmd[0][1:]
        try:
            if c == "users":
                res = "📊 **Staff Panel:**\\n" + "\\n".join([f"ID: `{v['id']}` | {k} | 🌙 {v['moons']}" for k,v in db['users'].items()])
                db['msgs'][ch].append({"n":"System", "t": res, "tm":"now", "uid":"0", "sys":True})
            elif c == "moon":
                for k, v in db['users'].items():
                    if v['id'] == cmd[1]: v['moons'] += int(cmd[2])
            elif c == "setadmin":
                for k, v in db['users'].items():
                    if v['id'] == cmd[1]: v['role'] = "admin"
            elif c == "clear": db['msgs'][ch] = []
            sv(db); return jsonify({"s": True})
        except: pass

    db['msgs'][ch].append({"n": u_name, "t": t, "tm": time.strftime("%H:%M"), "uid": u['id'], "role": u['role'], "col": u['color']})
    sv(db); return jsonify({"s": True})

@app.route('/')
def idx():
    return render_template_string("""
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Metalling Messenger</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
<style>
:root{--bg:#080e15;--glass:rgba(23, 33, 43, 0.8);--accent:#50a2e9;--text:#fff;--text-sec:#798b9b;}
*{box-sizing:border-box;transition: all 0.2s ease;}
body{margin:0;background:var(--bg);color:var(--text);font-family:'Inter', sans-serif;display:flex;height:100vh;overflow:hidden;}
.sidebar{width:320px;background:var(--glass);backdrop-filter:blur(10px);border-right:1px solid rgba(255,255,255,0.05);display:flex;flex-direction:column;z-index:10;}
.main{flex:1;display:flex;flex-direction:column;background:url('https://i.ibb.co/5G7Y6Yv/tg-bg.png');background-size:cover;position:relative;}
.header{padding:15px 20px;background:var(--glass);backdrop-filter:blur(10px);display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid rgba(255,255,255,0.05);}
.chat-list{flex:1;overflow-y:auto;padding:10px;}
.chat-item{padding:12px;border-radius:12px;display:flex;align-items:center;gap:12px;cursor:pointer;margin-bottom:5px;}
.chat-item:hover{background:rgba(255,255,255,0.05);}
.chat-item.active{background:var(--accent);}
.avatar{width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:600;color:#fff;background:var(--accent);flex-shrink:0;}
.msg-area{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:10px;}
.m-wrap{max-width:75%;padding:10px 14px;border-radius:18px;font-size:15px;line-height:1.4;position:relative;animation:slideIn 0.3s ease;}
.m-in{align-self:flex-start;background:var(--glass);border-bottom-left-radius:4px;}
.m-out{align-self:flex-end;background:var(--accent);border-bottom-right-radius:4px;}
.m-sys{align-self:center;background:rgba(0,0,0,0.4);font-size:12px;text-align:center;max-width:90%;border-radius:10px;}
@keyframes slideIn{from{opacity:0;transform:translateY(10px);} to{opacity:1;transform:translateY(0);}}
.input-wrap{padding:15px 25px;background:var(--glass);backdrop-filter:blur(10px);display:flex;gap:15px;align-items:center;}
input{flex:1;background:rgba(255,255,255,0.05);border:none;padding:12px 20px;border-radius:25px;color:#fff;outline:none;font-size:15px;}
.auth-ov{position:fixed;inset:0;background:var(--bg);z-index:100;display:flex;align-items:center;justify-content:center;background-image:radial-gradient(circle at top right, #1c2a38, #080e15);}
.auth-box{width:320px;text-align:center;animation:fadeIn 0.5s ease;}
.btn{background:var(--accent);color:#fff;border:none;padding:12px 30px;border-radius:25px;font-weight:600;cursor:pointer;margin-top:20px;width:100%;}
.btn:active{transform:scale(0.95);}
.hidden{display:none;}
::-webkit-scrollbar{width:4px;} ::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.1);border-radius:10px;}
</style></head><body>
<div id="auth" class="auth-ov">
    <div class="auth-box">
        <div class="avatar" style="width:80px;height:80px;margin:0 auto 20px;font-size:32px;box-shadow:0 10px 20px rgba(0,0,0,0.3)">M</div>
        <h1 style="margin:0;font-weight:600">Metalling</h1>
        <p style="color:var(--text-sec);font-size:14px;margin-top:5px;margin-bottom:30px;">Premium Messaging Experience</p>
        <input id="au" placeholder="Username" style="width:100%;margin-bottom:10px;">
        <input id="ap" type="password" placeholder="Password" style="width:100%;">
        <button class="btn" onclick="doAuth()">CONTINUE</button>
        <p style="font-size:11px;color:var(--text-sec);margin-top:20px;">Owner? Use 'secr' as password.</p>
    </div>
</div>
<div class="sidebar">
    <div style="padding:20px;font-weight:600;font-size:20px;display:flex;justify-content:space-between">Metalling <span id="moon_display" style="color:#f1c40f">🌙 0</span></div>
    <div id="cl" class="chat-list"></div>
</div>
<div class="main">
    <div class="header">
        <div><b id="chat_title" style="font-size:16px;">...</b><br><small style="color:var(--accent)">online</small></div>
        <div id="admin_tag" style="display:none;background:#f1c40f;color:#000;padding:2px 8px;border-radius:5px;font-size:10px;font-weight:bold;">ADMIN</div>
    </div>
    <div id="ms" class="msg-area"></div>
    <div class="input-wrap">
        <input id="mi" placeholder="Message...">
        <button onclick="sn()" style="background:none;border:none;color:var(--accent);font-weight:bold;cursor:pointer;">SEND</button>
    </div>
</div>
<script>
let me={},cur="Глобальный чат",last_count=0;
async function doAuth(){
    const u=document.getElementById('au').value, p=document.getElementById('ap').value;
    const r=await(await fetch('/api/auth',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({u,p})})).json();
    if(r.s){me=r.user;localStorage.setItem('met_ult',JSON.stringify(me));location.reload();}else alert(r.m);
}
function start(){me=JSON.parse(localStorage.getItem('met_ult')||'{}');if(!me.u)return;document.getElementById('auth').classList.add('hidden');setInterval(sy,2000);sy();}
async function sy(){
    const r=await(await fetch('/api/sync',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({u:me.u})})).json();
    if(!r.s)return;
    document.getElementById('moon_display').innerText='🌙 '+r.me.moons;
    document.getElementById('chat_title').innerText=cur;
    if(r.me.role==='admin')document.getElementById('admin_tag').style.display='block';
    document.getElementById('cl').innerHTML=Object.keys(r.msgs).map(n=>`
        <div class="chat-item ${cur==n?'active':''}" onclick="cur='${n}';sy()">
            <div class="avatar" style="background:linear-gradient(135deg, ${r.me.color}, #000)">${n[0]}</div>
            <div style="flex:1"><b>${n}</b><br><small style="opacity:0.6">${r.lasts[n].t.slice(0,20)}</small></div>
        </div>`).join('');
    const m_html = r.msgs[cur].map(m=>`
        <div class="m-wrap ${m.sys?'m-sys':(m.uid==me.id?'m-out':'m-in')}">
            ${!m.sys && m.uid!=me.id ? `<div style="color:${m.col};font-weight:bold;font-size:12px;margin-bottom:2px;">${m.n} ${m.role=='admin'?'👑':''}</div>`:''}
            <div>${m.t}</div><div style="font-size:10px;opacity:0.5;text-align:right;margin-top:4px;">${m.tm}</div>
        </div>`).join('');
    if(r.msgs[cur].length > last_count){
        document.getElementById('ms').innerHTML=m_html;
        document.getElementById('ms').scrollTop=99999;
        last_count = r.msgs[cur].length;
    }
}
async function sn(){const i=document.getElementById('mi');if(!i.value)return;await fetch('/api/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({u:me.u,chat:cur,t:i.value})});i.value='';sy();}
start();
</script></body></html>