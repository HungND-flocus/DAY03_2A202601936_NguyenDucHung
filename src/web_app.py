"""
🌐 MINIMAL CHAT UI — Đề tài 7: Trợ Lý Tư Vấn Khóa Học Sinh Viên
Giao diện chat tối giản để test Chatbot Baseline vs ReAct Agent.
Chạy: python src/web_app.py  →  http://localhost:7860
"""

import json, os, re, sys, time, ast
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

provider = get_llm_provider()
IS_LIVE = provider.__class__.__name__ != "MockProvider"


def execute_tool(action_str):
    m = re.search(r"(\w+)\[(.*)\]", action_str)
    if not m:
        return f"LỖI: Format không hợp lệ: {action_str}"
    name, raw = m.group(1).strip(), m.group(2).strip()
    if name not in AVAILABLE_TOOLS:
        return f"LỖI: Tool '{name}' không tồn tại."
    try:
        if not raw:
            args = []
        else:
            try:
                p = ast.literal_eval(f"[{raw}]")
                args = [str(x) for x in p] if isinstance(p, list) else [str(p)]
            except Exception:
                args = [a.strip().strip("'\"") for a in raw.split(",") if a.strip()]
        return str(AVAILABLE_TOOLS[name](*args))
    except Exception as e:
        return f"LỖI: {e}"


def run_pipeline(query, mode):
    steps = []
    if mode == "baseline":
        r = provider.generate(query, system_prompt=CHATBOT_BASELINE_PROMPT)
        steps.append({"type": "answer", "text": r})
        return steps

    history = f"Câu hỏi của sinh viên: {query}"
    for i in range(MAX_ITERATIONS):
        out = provider.generate(history, system_prompt=REACT_SYSTEM_PROMPT)
        if IS_LIVE:
            time.sleep(13)
        if not out:
            break

        th = re.search(r"Thought:\s*(.*?)(?=Action:|Final Answer:|$)", out, re.DOTALL)
        if th and th.group(1).strip():
            steps.append({"type": "thought", "text": th.group(1).strip()})

        if "Final Answer:" in out:
            steps.append({"type": "answer", "text": out.split("Final Answer:", 1)[-1].strip()})
            break

        am = re.search(r"Action:\s*(.+)", out)
        if am:
            action_str = am.group(1).strip()
            obs = execute_tool(action_str)
            steps.append({"type": "action", "text": action_str})
            steps.append({"type": "observation", "text": obs})
            history += f"\n{out}\nObservation: {obs}"
        else:
            history += f"\n{out}"
    else:
        steps.append({"type": "guardrail", "text": f"Đã đạt giới hạn {MAX_ITERATIONS} bước suy luận."})
    return steps


def steps_to_html(steps):
    parts = []
    for s in steps:
        t, c = s["type"], s["text"].replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        if t == "thought":
            parts.append(f'<div class="trace thought"><span class="tag">Thought</span>{c}</div>')
        elif t == "action":
            parts.append(f'<div class="trace action"><span class="tag">Action</span><code>{c}</code></div>')
        elif t == "observation":
            parts.append(f'<div class="trace obs"><span class="tag">Observation</span><pre>{c}</pre></div>')
        elif t == "answer":
            parts.append(f'<div class="trace final"><span class="tag">Answer</span>{c}</div>')
        elif t == "guardrail":
            parts.append(f'<div class="trace guard"><span class="tag">Guardrail</span>{c}</div>')
    return "".join(parts)


provider_label = f"{provider.__class__.__name__.replace('Provider','')} · {getattr(provider, 'model_name', 'Mock')}"

PAGE = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VinUni · Trợ Lý Tư Vấn Khóa Học</title>
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#ffffff;--surface:#ffffff;--border:#e2e8f0;--text:#0f172a;--muted:#64748b;
  --accent:#3b82f6;--accent2:#2563eb;--green:#10b981;--amber:#f59e0b;--red:#ef4444;--purple:#8b5cf6}
body{font-family:'Roboto',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);
  height:100vh;display:flex;flex-direction:column;overflow:hidden}

/* ── Header ── */
header{padding:14px 24px;background:var(--surface);border-bottom:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;flex-shrink:0;
  box-shadow:0 1px 3px rgba(0,0,0,.04)}
header h1{font-size:1rem;font-weight:700;display:flex;align-items:center;gap:8px;color:var(--text)}
header h1 span{font-size:1.2rem}
.meta{font-size:.75rem;color:var(--muted);display:flex;align-items:center;gap:6px}
.dot{width:6px;height:6px;border-radius:50%;background:var(--green);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}

/* ── Mode toggle ── */
.toggle{display:flex;background:#f8fafc;border:1px solid var(--border);border-radius:10px;padding:3px;gap:2px}
.toggle button{padding:6px 14px;border:none;border-radius:8px;font-size:.78rem;font-weight:600;
  color:var(--muted);background:transparent;cursor:pointer;transition:all .15s}
.toggle button.on{background:var(--accent);color:#fff;box-shadow:0 1px 4px rgba(59,130,246,.3)}

/* ── Chat ── */
.chat{flex:1;overflow-y:auto;padding:24px 24px 12px;display:flex;flex-direction:column;gap:16px}

.msg{max-width:720px;width:100%;margin:0 auto;display:flex;flex-direction:column;gap:6px}
.msg.user{align-self:flex-end}
.msg.bot{align-self:flex-start}

.bubble{padding:12px 16px;border-radius:16px;font-size:.9rem;line-height:1.65;white-space:pre-wrap;word-break:break-word}
.user .bubble{background:var(--accent);color:#fff;border-bottom-right-radius:4px;box-shadow:0 2px 6px rgba(59,130,246,.25)}
.bot .bubble{background:var(--surface);border:1px solid var(--border);border-bottom-left-radius:4px;box-shadow:0 1px 3px rgba(0,0,0,.04)}

/* ── Traces ── */
.trace{margin-top:6px;padding:10px 14px;border-radius:10px;font-size:.84rem;line-height:1.55;border-left:3px solid}
.trace .tag{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;display:block;margin-bottom:4px}
.trace code{font-family:'Roboto Mono','Cascadia Code',monospace;font-size:.82rem;background:rgba(0,0,0,.06);padding:3px 8px;border-radius:6px;display:inline-block}
.trace pre{font-family:'Roboto Mono','Cascadia Code',monospace;font-size:.8rem;background:rgba(0,0,0,.04);padding:8px 10px;border-radius:8px;white-space:pre-wrap;margin-top:4px;max-height:200px;overflow-y:auto}

.thought{background:#f5f3ff;border-color:var(--purple);color:#5b21b6}
.thought .tag{color:var(--purple)}
.action{background:#fffbeb;border-color:var(--amber);color:#92400e}
.action .tag{color:var(--amber)}
.obs{background:#ecfdf5;border-color:var(--green);color:#065f46}
.obs .tag{color:var(--green)}
.final{background:#eef2ff;border-color:var(--accent);color:var(--text)}
.final .tag{color:var(--accent2)}
.guard{background:#fef2f2;border-color:var(--red);color:var(--red)}

/* ── Loading ── */
.typing{display:flex;gap:4px;padding:14px 16px}
.typing span{width:7px;height:7px;background:var(--border);border-radius:50%;animation:bounce .6s infinite alternate}
.typing span:nth-child(2){animation-delay:.15s}
.typing span:nth-child(3){animation-delay:.3s}
@keyframes bounce{to{transform:translateY(-6px);opacity:.3}}

/* ── Input ── */
.input-area{padding:12px 24px 20px;flex-shrink:0;background:var(--surface);border-top:1px solid var(--border)}
.input-row{display:flex;gap:10px;max-width:720px;margin:0 auto}
.input-row input{flex:1;background:#f8fafc;border:1px solid var(--border);padding:12px 16px;
  border-radius:12px;color:var(--text);font-size:.9rem;outline:none;transition:all .15s}
.input-row input:focus{border-color:var(--accent);background:#ffffff;box-shadow:0 0 0 3px rgba(59,130,246,.15)}
.input-row button{background:var(--accent);border:none;color:#fff;font-weight:600;padding:0 20px;
  border-radius:12px;font-size:.88rem;cursor:pointer;transition:all .15s;
  box-shadow:0 2px 6px rgba(59,130,246,.25)}
.input-row button:disabled{opacity:.35;cursor:not-allowed}
.input-row button:hover:not(:disabled){background:var(--accent2)}

/* ── Welcome ── */
.welcome{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;color:var(--muted);text-align:center}
.welcome .icon{font-size:2.5rem;margin-bottom:4px}
.welcome p{font-size:.92rem;max-width:420px;line-height:1.55}
</style>
</head>
<body>

<header>
  <h1><span>🎓</span> Trợ Lý Tư Vấn Khóa Học</h1>
  <div style="display:flex;align-items:center;gap:16px">
    <div class="toggle">
      <button id="bBase" onclick="setMode('baseline')">💬 Chatbot</button>
      <button id="bReact" class="on" onclick="setMode('react')">🧠 ReAct Agent</button>
    </div>
    <div class="meta"><div class="dot"></div>""" + provider_label + """</div>
  </div>
</header>

<div class="chat" id="chat">
  <div class="welcome" id="welcome">
    <div class="icon">🎓</div>
    <p>Xin chào! Tôi là trợ lý tư vấn khóa học.<br>Hỏi tôi bất cứ điều gì về môn học, điều kiện tiên quyết hay lộ trình học tập.</p>
  </div>
</div>

<div class="input-area">
  <div class="input-row">
    <input id="inp" type="text" placeholder="Nhập câu hỏi..." onkeydown="if(event.key==='Enter')send()" autofocus>
    <button id="btn" onclick="send()">Gửi</button>
  </div>
</div>

<script>
let mode='react';

function setMode(m){
  mode=m;
  document.getElementById('bBase').classList.toggle('on',m==='baseline');
  document.getElementById('bReact').classList.toggle('on',m==='react');
}

function ask(q){document.getElementById('inp').value=q;send()}

async function send(){
  const inp=document.getElementById('inp'), btn=document.getElementById('btn'), chat=document.getElementById('chat');
  const q=inp.value.trim(); if(!q)return;

  const w=document.getElementById('welcome'); if(w)w.remove();

  // User bubble
  const u=document.createElement('div');u.className='msg user';
  u.innerHTML='<div class="bubble">'+q.replace(/</g,'&lt;')+'</div>';
  chat.appendChild(u);
  inp.value='';inp.disabled=true;btn.disabled=true;

  // Typing indicator
  const ld=document.createElement('div');ld.className='msg bot';ld.id='typing';
  ld.innerHTML='<div class="bubble"><div class="typing"><span></span><span></span><span></span></div></div>';
  chat.appendChild(ld);
  chat.scrollTop=chat.scrollHeight;

  try{
    const res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:q,mode})});
    const data=await res.json();
    ld.remove();
    const bot=document.createElement('div');bot.className='msg bot';
    bot.innerHTML='<div class="bubble">'+data.html+'</div>';
    chat.appendChild(bot);
  }catch(e){
    ld.remove();
    const bot=document.createElement('div');bot.className='msg bot';
    bot.innerHTML='<div class="bubble" style="color:var(--red)">❌ Lỗi kết nối server.</div>';
    chat.appendChild(bot);
  }
  inp.disabled=false;btn.disabled=false;inp.focus();
  chat.scrollTop=chat.scrollHeight;
}
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *a): pass

    def do_GET(self):
        body = PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_response(404); self.end_headers(); return
        length = int(self.headers.get("Content-Length", 0))
        req = json.loads(self.rfile.read(length).decode("utf-8"))
        query, m = req.get("query", ""), req.get("mode", "react")

        try:
            steps = run_pipeline(query, m)
            html = steps_to_html(steps)
        except Exception as e:
            html = f'<span style="color:var(--red)">❌ {e}</span>'

        body = json.dumps({"html": html}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = 7860
    httpd = HTTPServer(("", port), Handler)
    print(f"\n  🎓 Trợ Lý Tư Vấn Khóa Học — http://localhost:{port}")
    print(f"  🔌 {provider_label}")
    print(f"  Nhấn Ctrl+C để dừng.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  ⏹️  Đã dừng.")
        httpd.server_close()
