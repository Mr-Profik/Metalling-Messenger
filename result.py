import os, random, json, time, string
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
DB_FILE = "metalling_pro.json"

def ld():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "id_to_email": {}, "msgs": {"Глобальный чат": [], "Metalling News 📢": [{"n":"System", "t":"Добро пожаловать в Metalling Messenger! 🚀", "tm":"12:00", "uid":"0"}]}, "codes": {}, "bans": [], "owner": None}
    with open(DB_FILE, 'r') as f: return json.load(f)

def sv(d):
    with open(DB_FILE, 'w') as f: json.dump(d, f, indent=4, ensure_ascii=False)

db = ld()

@app.route('/api/auth/send_code', methods=['POST'])
def sc():
    e = request.json.get('email', '').lower().strip()
    c = "".join(random.choices(string.digits, k=6))
    db['codes'][e] = c
    print(f"\n💎 [LOGS] CODE FOR {e}: {c}\n")
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
        return jsonify({"s": True, "exists": e in db['users'], "is_owner": (e == db.get('owner'))})
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
    return jsonify({"s": True, "me": u, "msgs": db['msgs'], "lasts": ls, "adm": u['role'] == 'admin'})

@app.route('/api/send', methods=['POST'])
def sn():
    d = request.json; e = d.get('email', '').lower().strip(); ch = d.get('chat'); t = d.get('t', '').strip()
    u = db['users'].get(e)
    if not u or e in db['bans'] or not t: return jsonify({"s": False})

    if u['role'] == 'admin' and t.startswith('!'):
        cmd = t.split(); c = cmd[0][1:]
        try:
            if c == "users":
                res = "📊 **USERS:**\n" + "\n".join([f"ID: {v['id']} | {v['n']} | 🌙 {v.get('moons',0)}" for k,v in db['users'].items()])
                db['msgs'][ch].append({"n":"System", "t": res, "tm":"now", "uid":"0"})
            elif c == "moon":
                target = db['id_to_email'][cmd[1]]
                db['users'][target]['moons'] += int(cmd[2])
            elif c == "ban": db['bans'].append(db['id_to_email'][cmd[1]])
            sv(db); return jsonify({"s": True})
        except: pass

    db['msgs'][ch].append({"n": u['n'], "t": t, "tm": time.strftime("%H:%M"), "uid": u['id'], "r": u['role']})
    sv(db); return jsonify({"s": True})

@app.route('/')
def idx():
    return render_template_string("""
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Metalling Messenger</title><style>
:root{--bg:#0e1621;--side:#17212b;--hover:#232e3c;--active:#2b5278;--blue:#50a2e9;--msg-in:#182533;--msg-out:#2b5278;--text:#fff;--text-sec:#708499;}
body{margin:0;background:var(--bg);color:var(--text);font-family: Roboto, sans-serif;display:flex;height:100vh;overflow:hidden;}
.sidebar{width:300px;background:var(--side);display:flex;flex-direction:column;border-right:1px solid #0e1621;}
.search-bar{padding:15px;display:flex;gap:10px;}
.search-bar input{flex:1;background:#242f3d;border:none;border-radius:8px;padding:8px 12px;color:#fff;outline:none;}
.chat-list{flex:1;overflow-y:auto;}
.chat-item{padding:10px 15px;display:flex;align-items:center;gap:12px;cursor:pointer;transition:0.2s;}
.chat-item:hover{background:var(--hover);}
.chat-item.active{background:var(--active);}
.avatar{width:50px;height:50px;border-radius:50%;background:linear-gradient(135deg, #50a2e9, #33719e);display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:18px;}
.chat-info{flex:1;min-width:0;}
.chat-info div{display:flex;justify-content:space-between;align-items:center;}
.chat-info b{font-size:15px;}
.chat-info p{margin:2px 0 0;font-size:13px;color:var(--text-sec);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.main{flex:1;display:flex;flex-direction:column;position:relative;background:#0e1621;background-image:url('https://i.ibb.co/5G7Y6Yv/tg-bg.png');}
.top-bar{padding:10px 20px;background:var(--side);display:flex;align-items:center;justify-content:space-between;z-index:10;}
.messages{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:5px;}
.msg{max-width:70%;padding:8px 12px;border-radius:12px;font-size:14.5px;line-height:1.4;position:relative;}
.msg-in{align-self:flex-start;background:var(--msg-in);border-bottom-left-radius:4px;}
.msg-out{align-self:flex-end;background:var(--msg-out);border-bottom-right-radius:4px;}
.msg-name{font-size:13px;font-weight:bold;color:var(--blue);margin-bottom:3px;}
.msg-time{font-size:11px;opacity:0.5;text-align:right;margin-top:4px;}
.input-wrap{padding:10px 20px;background:var(--side);display:flex;align-items:center;gap:15px;}
.input-wrap input{flex:1;background:transparent;border:none;color:#fff;outline:none;font-size:16px;}
.auth-ov{position:fixed;inset:0;background:var(--bg);z-index:100;display:flex;align-items:center;justify-content:center;flex-direction:column;}
.auth-card{width:100%;max-width:320px;text-align:center;}
button{background:none;border:none;color:var(--blue);font-weight:bold;cursor:pointer;font-size:16px;}
.hidden{display:none;}
</style></head><body>
<div id="auth" class="auth-ov">
    <div class="auth-card">
        <div class="avatar" style="width:80px;height:80px;margin:0 auto 20px;font-size:30px;">M</div>
        <h2>Metalling</h2>
        <p style="color:var(--text-sec);margin-bottom:30px;">Messenger for the future</p>
        <div id="s1"><input id="e" placeholder="Email" style="width:100%;padding:12px;background:#242f3d;border:none;border-radius:8px;color:#fff;"><br><br><button onclick="sc()">NEXT</button></div>
        <div id="s2" class="hidden"><input id="c" placeholder="Code" style="width:100%;padding:12px;background:#242f3d;border:none;border-radius:8px;color:#fff;"><br><br><button onclick="vc()">SIGN IN</button></div>
        <div id="s3" class="hidden"><input id="n" placeholder="Your Name" style="width:100%;padding:12px;background:#242f3d;border:none;border-radius:8px;color:#fff;"><br><br><button onclick="fr()">START</button></div>
    </div>
</div>
<div class="sidebar">
    <div class="search-bar"><input placeholder="Search"></div>
    <div id="cl" class="chat-list"></div>
</div>
<div class="main">
    <div class="top-bar">
        <div><b id="cur_name">Chat</b><br><small id="status" style="color:var(--blue)">online</small></div>
        <div id="adm_btn" style="color:#f1c40f;font-weight:bold;display:none;">ADMIN</div>
        <div id="my_moons">🌙 0</div>
    </div>
    <div id="ms" class="messages"></div>
    <div class="input-wrap">
        <input id="mi" placeholder="Write a message...">
        <button onclick="sn()">SEND</button>
    </div>
</div>
<script>
let me={},cur="Глобальный чат";
async function sc(){await fetch('/api/auth/send_code',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('e').value})});document.getElementById('s1').classList.add('hidden');document.getElementById('s2').classList.remove('hidden');}
async function vc(){
    const e=document.getElementById('e').value,c=document.getElementById('c').value;
    const r=await(await fetch('/api/auth/verify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:e,code:c})})).json();
    if(r.s){me.e=e;if(r.exists)fn();else{document.getElementById('s2').classList.add('hidden');document.getElementById('s3').classList.remove('hidden');}}else alert('Error');
}
async function fr(){await fetch('/api/reg',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:me.e,n:document.getElementById('n').value})});fn();}
function fn(){localStorage.setItem('met_pro',JSON.stringify(me));location.reload();}
function start(){me=JSON.parse(localStorage.getItem('met_pro')||'{}');if(!me.e)return;document.getElementById('auth').classList.add('hidden');setInterval(sy,2000);sy();}
async function sy(){
    const r=await(await fetch('/api/sync',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:me.e})})).json();
    if(!r.s)return;
    document.getElementById('my_moons').innerText = '🌙 ' + r.me.moons;
    document.getElementById('cur_name').innerText = cur;
    if(r.adm)document.getElementById('adm_btn').style.display='block';
    document.getElementById('cl').innerHTML=Object.keys(r.msgs).map(n=>`
        <div class="chat-item ${cur==n?'active':''}" onclick="cur='${n}';sy()">
            <div class="avatar">${n[0]}</div>
            <div class="chat-info"><div><b>${n}</b><small>${r.lasts[n].tm}</small></div><p>${r.lasts[n].t}</p></div>
        </div>`).join('');
    document.getElementById('ms').innerHTML=r.msgs[cur].map(m=>`
        <div class="msg ${m.uid==r.me.id?'msg-out':'msg-in'}">
            ${m.uid!=r.me.id?`<div class="msg-name">${m.n}</div>`:''}
            <div>${m.t}</div><div class="msg-time">${m.tm}</div>
        </div>`).join('');
}
async function sn(){const i=document.getElementById('mi');if(!i.value)return;await fetch('/api/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:me.e,chat:cur,t:i.value})});i.value='';sy();document.getElementById('ms').scrollTop=99999;}
start();
</script></body></html>
""")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)