import os
import time
import uuid
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI()

# Единая База Данных Metalling
db = {
    "rooms": {"0000": []},
    "stories": [],
    "bots": {}, # Реестр токенов ботов
    "users": {
        "+79000000000": {"prem": True, "stars": 777, "last_story": 0} # ТВОЙ НОМЕР СЮДА
    }
}

class Msg(BaseModel):
    room_id: str
    user: str
    text: str

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Metalling Messenger Ultra</title>
        <style>
            :root { --bg: #0e1621; --header: #17212b; --wa: #25d366; --tg: #2b5278; --stars: #ffce44; --bomb: #ff4444; }
            body { margin: 0; background: var(--bg); color: #fff; font-family: -apple-system, sans-serif; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
            
            /* Stories */
            #stories { display: flex; gap: 10px; padding: 10px; background: var(--header); overflow-x: auto; border-bottom: 1px solid #000; }
            .st-circle { min-width: 65px; height: 65px; border-radius: 50%; border: 2px solid var(--wa); display: flex; align-items: center; justify-content: center; font-size: 10px; cursor: pointer; text-align: center; background: #242f3d; }
            .st-add { border: 2px dashed #808d97; }

            /* Auth */
            #auth { position: fixed; inset: 0; background: var(--bg); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 20px; }
            .box { background: var(--header); padding: 30px; border-radius: 20px; width: 100%; max-width: 320px; text-align: center; border: 1px solid #242f3d; }
            input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 12px; border: 1px solid #242f3d; background: #0e1621; color: #fff; outline: none; box-sizing: border-box; }
            .btn { width: 100%; padding: 12px; border-radius: 12px; border: none; background: var(--wa); color: #fff; font-weight: bold; cursor: pointer; }

            header { background: var(--header); padding: 15px; border-bottom: 1px solid #000; display: flex; justify-content: space-between; align-items: center; }
            #chat { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 10px; background-image: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png'); }
            .msg { max-width: 80%; padding: 10px; border-radius: 15px; background: #182533; font-size: 14px; position: relative; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }
            .me { align-self: flex-end; background: var(--tg); border-bottom-right-radius: 2px; }
            .bomb-msg { border: 2px solid var(--bomb); box-shadow: 0 0 10px var(--bomb); }
            .bot-msg { border: 1px solid var(--wa); }
            
            footer { background: var(--header); padding: 10px; display: flex; gap: 10px; border-top: 1px solid #000; }
        </style>
    </head>
    <body>
        <div id="auth">
            <div class="box" id="step1">
                <h2 style="color:var(--wa)">Metalling</h2>
                <input type="tel" id="phone" placeholder="+7 900 000 00 00">
                <button class="btn" onclick="next()">Get Code</button>
            </div>
            <div class="box" id="step2" style="display:none">
                <h2>Enter Code</h2>
                <input type="number" id="code" placeholder="Try 1234">
                <button class="btn" onclick="login()">Login</button>
            </div>
        </div>

        <div id="stories">
            <div class="st-circle st-add" onclick="postStory()">+<br>Story</div>
            <div id="st-list" style="display:flex; gap:10px;"></div>
        </div>

        <header>
            <b>Metalling Messenger</b>
            <div style="color:var(--stars)">⭐ <span id="stars-val">0</span></div>
        </header>

        <div id="chat"></div>

        <footer>
            <input type="number" id="rid" value="0000" style="width:70px; flex:none;">
            <input type="text" id="minp" placeholder="Message... (💣 for bomb)">
            <button onclick="send()" style="background:var(--wa); border:none; width:45px; height:45px; border-radius:50%; color:white; font-size:18px; cursor:pointer;">✈</button>
        </footer>

        <script>
            let myPhone = "";
            function next() {
                myPhone = document.getElementById('phone').value;
                document.getElementById('step1').style.display='none';
                document.getElementById('step2').style.display='block';
            }
            function login() {
                if(document.getElementById('code').value === "1234") {
                    document.getElementById('auth').style.display='none';
                    load();
                    setInterval(load, 2500);
                } else alert("Wrong code!");
            }
            async function load() {
                const r = await fetch('/get_all/' + document.getElementById('rid').value);
                const data = await r.json();
                document.getElementById('stars-val').innerText = data.stars;
                
                document.getElementById('chat').innerHTML = data.msgs.map(m => `
                    <div class="msg ${m.user==myPhone?'me':''} ${m.is_bomb?'bomb-msg':''} ${m.is_bot?'bot-msg':''}">
                        <div style="font-size:10px; color:var(--wa); font-weight:bold;">${m.user} ${m.is_prem?'⭐':''}</div>
                        ${m.text}
                    </div>`).join('');
                
                document.getElementById('st-list').innerHTML = data.stories.map(s => `
                    <div class="st-circle" onclick="alert('${s.text}')">${s.user.slice(-4)}</div>`).join('');
            }
            async function send() {
                const text = document.getElementById('minp').value;
                await fetch('/send', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({room_id: document.getElementById('rid').value, user: myPhone, text: text})
                });
                document.getElementById('minp').value = '';
                load();
            }
            async function postStory() {
                const t = prompt("Your Story Text:");
                if(!t) return;
                const r = await fetch('/story', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({user: myPhone, text: t})
                });
                const res = await r.json();
                if(!res.ok) alert(res.msg);
                load();
            }
        </script>
    </body>
    </html>
    """

@app.get("/get_all/{room_id}")
def get_all(room_id: str):
    now = time.time()
    # Чистим бомбы (10 сек)
    if room_id in db["rooms"]:
        db["rooms"][room_id] = [m for m in db["rooms"][room_id] if not (m.get("is_bomb") and now - m["time"] > 10)]
    
    user_data = db["users"].get("+79000000000", {"stars": 0}) # Пример для фронта
    return {
        "msgs": db["rooms"].get(room_id, [])[-40:],
        "stories": db["stories"][-15:],
        "stars": user_data.get("stars", 0)
    }

@app.post("/send")
def post_msg(m: Msg):
    if m.room_id not in db["rooms"]: db["rooms"][m.room_id] = []
    user_info = db["users"].get(m.user, {"prem": False})
    
    # Anti-Spam
    history = [x for x in db["rooms"][m.room_id] if x["user"] == m.user][-3:]
    if len(history) >= 3 and history[0]["text"] == m.text:
        db["rooms"][m.room_id].append({"user": "🛡 AntiSpam", "text": "Stop spamming!", "is_bot": True})
        return {"ok": False}

    msg_data = {
        "user": m.user, "text": m.text, "time": time.time(),
        "is_bomb": "💣" in m.text, "is_prem": user_info.get("prem", False), "is_bot": False
    }
    db["rooms"][m.room_id].append(msg_data)

    # BotMetalling (BotFather)
    if m.text == "/newbot":
        token = str(uuid.uuid4())[:12]
        db["bots"][token] = {"owner": m.user}
        db["rooms"][m.room_id].append({"user": "🤖 BotMetalling", "text": f"Token: {token}", "is_bot": True})
        
    return {"ok": True}

@app.post("/story")
def post_story(data: dict):
    u = data['user']
    now = time.time()
    if u not in db["users"]: db["users"][u] = {"prem": False, "last_story": 0}
    
    user_info = db["users"][u]
    limit = 600 if user_info["prem"] else 604800 # 10 мин для прем / 1 неделя для обычных
    
    if now - user_info["last_story"] < limit:
        return {"ok": False, "msg": "Limit reached! Buy Premium for more!"}
    
    db["stories"].append({"user": u, "text": data['text'], "time": now})
    db["users"][u]["last_story"] = now
    return {"ok": True}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
