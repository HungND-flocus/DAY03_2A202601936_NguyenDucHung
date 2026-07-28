"""
🌐 MINIMAL CHAT UI — Đề tài 7: Trợ Lý Tư Vấn Khóa Học Sinh Viên
Giao diện chat tối giản (Monochrome) tích hợp Sidebar Tra cứu Dữ liệu & Test Cases.
Chạy: python src/web_app.py  →  http://localhost:7860
"""

import json, os, re, sys, time, ast
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools import AVAILABLE_TOOLS, COURSE_DATABASE
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
        steps.append({"type": "baseline", "text": r})
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
            parts.append(f'<div class="trace final"><span class="tag">ReAct Agent</span>{c}</div>')
        elif t == "baseline":
            parts.append(f'<div class="trace baseline"><span class="tag">Chatbot Baseline</span>{c}</div>')
        elif t == "guardrail":
            parts.append(f'<div class="trace guard"><span class="tag">Guardrail</span>{c}</div>')
    return "".join(parts)


provider_label = f"{provider.__class__.__name__.replace('Provider','')} · {getattr(provider, 'model_name', 'Mock')}"

# Generate Course List HTML
courses_html_items = []
for cid, info in COURSE_DATABASE.items():
    prereq = ", ".join(info["prerequisites"]) if info["prerequisites"] else "Không"
    courses_html_items.append(f"""
    <div class="db-card">
      <div class="db-card-header"><strong>[{cid}]</strong> {info['name']}</div>
      <div class="db-card-body">
        <div><span>Tín chỉ:</span> {info['credits']} | <span>Độ khó:</span> {info['difficulty']}</div>
        <div><span>Tiên quyết:</span> {prereq}</div>
        <div><span>Lịch:</span> {info['schedule']}</div>
      </div>
    </div>
    """)
courses_html = "".join(courses_html_items)

PAGE = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VinUni · Trợ Lý Tư Vấn Khóa Học</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:'Inter',-apple-system,sans-serif}
:root{--bg:#ffffff;--border:#e5e7eb;--text:#111827;--muted:#6b7280;
  --user-bg:#111827;--user-text:#ffffff;--bot-bg:#f9fafb;--trace-bg:#f3f4f6}
body{background:var(--bg);color:var(--text);height:100vh;display:flex;flex-direction:column;overflow:hidden}

header{padding:14px 24px;display:flex;align-items:center;justify-content:space-between;
  border-bottom:1px solid var(--border);flex-shrink:0}
header h1{font-size:1.05rem;font-weight:600;letter-spacing:-0.02em;display:flex;align-items:center;gap:12px}
.meta{font-size:0.75rem;color:var(--muted);display:flex;align-items:center;gap:6px}
.dot{width:6px;height:6px;border-radius:50%;background:#111827}

.sidebar-btn{background:transparent;border:1px solid var(--border);padding:6px 12px;border-radius:8px;
  font-size:0.8rem;font-weight:500;cursor:pointer;color:var(--text);transition:all 0.2s}
.sidebar-btn:hover{background:var(--trace-bg)}

.toggle{display:flex;background:var(--trace-bg);border-radius:24px;padding:4px;gap:2px}
.toggle button{padding:6px 16px;border:none;border-radius:20px;font-size:0.8rem;font-weight:500;
  color:var(--muted);background:transparent;cursor:pointer;transition:all 0.2s}
.toggle button.on{background:var(--bg);color:var(--text);box-shadow:0 1px 3px rgba(0,0,0,0.05)}

/* MAIN LAYOUT WITH SIDEBAR */
.app-container{flex:1;display:flex;overflow:hidden}

.sidebar{width:340px;background:var(--bg);border-right:1px solid var(--border);
  display:flex;flex-direction:column;overflow-y:auto;flex-shrink:0;transition:all 0.2s}
.sidebar.hidden{margin-left:-340px}

.sidebar-section{padding:20px;border-bottom:1px solid var(--border)}
.sidebar-title{font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:var(--muted);margin-bottom:12px}

/* Student Info Box */
.student-card{background:var(--bot-bg);border:1px solid var(--border);padding:14px;border-radius:12px;font-size:0.85rem;line-height:1.6}
.student-card div span{color:var(--muted);font-weight:500}

/* Course DB List */
.db-list{display:flex;flex-direction:column;gap:8px;max-height:240px;overflow-y:auto;padding-right:4px}
.db-card{background:var(--bg);border:1px solid var(--border);padding:10px;border-radius:8px;font-size:0.8rem}
.db-card-header{font-weight:600;margin-bottom:4px}
.db-card-body{color:var(--muted);line-height:1.4}
.db-card-body span{font-weight:500;color:var(--text)}

/* Test Cases List */
.test-list{display:flex;flex-direction:column;gap:8px}
.test-item{background:var(--bot-bg);border:1px solid var(--border);padding:10px 12px;border-radius:8px;
  font-size:0.82rem;line-height:1.4;cursor:pointer;transition:all 0.2s;text-align:left;color:var(--text)}
.test-item:hover{background:var(--user-bg);color:var(--user-text);border-color:var(--user-bg)}
.test-item .cat{font-size:0.7rem;font-weight:600;color:var(--muted);margin-bottom:2px;display:block}
.test-item:hover .cat{color:#9ca3af}

/* CHAT MAIN */
.main-chat{flex:1;display:flex;flex-direction:column;overflow:hidden}
.chat{flex:1;overflow-y:auto;padding:32px;display:flex;flex-direction:column;gap:24px}
.msg{width:100%;max-width:800px;margin:0 auto;display:flex;flex-direction:column;gap:8px}
.msg.user{align-items:flex-end}
.msg.bot{align-items:flex-start}

.bubble{padding:14px 20px;border-radius:20px;font-size:0.95rem;line-height:1.6;white-space:pre-wrap;word-break:break-word}
.user .bubble{background:var(--user-bg);color:var(--user-text);border-bottom-right-radius:4px}
.bot .bubble{background:var(--bot-bg);border:1px solid var(--border);border-bottom-left-radius:4px;width:100%}

.vs-container{max-width:1400px;width:100%}
.vs-grid{display:grid;grid-template-columns:1fr 1px 1fr;gap:24px;width:100%}
.divider{background:var(--border);width:1px}
.vs-col{display:flex;flex-direction:column;gap:12px}
.vs-col-title{font-size:0.75rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:0.05em}

/* Minimal Traces */
.trace{margin-top:8px;padding:12px 16px;border-radius:12px;font-size:0.85rem;line-height:1.6;background:var(--trace-bg);border-left:3px solid transparent}
.trace .tag{font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;display:block;margin-bottom:6px;color:var(--muted)}
.trace code{font-family:monospace;font-size:0.85rem;background:rgba(0,0,0,0.05);padding:2px 6px;border-radius:4px}
.trace pre{font-family:monospace;font-size:0.8rem;background:rgba(0,0,0,0.05);padding:10px;border-radius:8px;white-space:pre-wrap;margin-top:8px;overflow-y:auto}

.thought{border-left-color:#d1d5db}
.action{border-left-color:#9ca3af}
.obs{border-left-color:#6b7280}
.final{border-left-color:#111827;background:transparent;padding:0}
.final .tag{display:none}
.baseline{border-left-color:#111827;background:transparent;padding:0}
.baseline .tag{display:none}

.typing{display:flex;gap:4px;padding:14px 16px}
.typing span{width:6px;height:6px;background:#9ca3af;border-radius:50%;animation:pulse 1s infinite}
.typing span:nth-child(2){animation-delay:0.2s}
.typing span:nth-child(3){animation-delay:0.4s}
@keyframes pulse{0%,100%{transform:scale(0.8);opacity:0.5}50%{transform:scale(1.2);opacity:1}}

.input-area{padding:24px 32px 32px;background:var(--bg)}
.input-row{display:flex;gap:12px;max-width:800px;margin:0 auto;position:relative}
.input-row input{flex:1;background:var(--trace-bg);border:none;padding:16px 24px;
  border-radius:24px;font-size:0.95rem;outline:none;transition:all 0.2s}
.input-row input:focus{background:var(--bg);box-shadow:0 0 0 1px var(--border), 0 4px 12px rgba(0,0,0,0.05)}
.input-row button{position:absolute;right:8px;top:8px;bottom:8px;background:var(--user-bg);border:none;color:#fff;
  font-weight:500;padding:0 20px;border-radius:18px;font-size:0.9rem;cursor:pointer;transition:opacity 0.2s}
.input-row button:disabled{opacity:0.5;cursor:not-allowed}

.welcome{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;color:var(--muted);text-align:center;gap:16px}
.welcome h2{font-size:1.5rem;font-weight:600;color:var(--text);letter-spacing:-0.02em}
.welcome p{font-size:0.95rem;max-width:400px;line-height:1.6}
</style>
</head>
<body>

<header>
  <h1>
    <button class="sidebar-btn" onclick="toggleSidebar()">☰ Data & Tests</button>
    <span>Trợ Lý Tư Vấn Khóa Học</span>
  </h1>
  <div class="toggle">
    <button id="bBase" onclick="setMode('baseline')">Baseline</button>
    <button id="bReact" onclick="setMode('react')">ReAct</button>
    <button id="bVs" class="on" onclick="setMode('vs')">VS Mode</button>
  </div>
  <div class="meta"><div class="dot"></div>""" + provider_label + """</div>
</header>

<div class="app-container">
  <!-- SIDEBAR PANEL -->
  <div class="sidebar" id="sidebar">
    <!-- Section 1: Student Profile -->
    <div class="sidebar-section">
      <div class="sidebar-title">👤 Thông Tin Sinh Viên (Mock Profile)</div>
      <div class="student-card">
        <div><span>Mã SV:</span> 2A202601936</div>
        <div><span>Họ tên:</span> Nguyễn Văn A</div>
        <div><span>Ngành:</span> Công nghệ Thông tin (AI Track)</div>
        <div><span>GPA tích lũy:</span> 3.65 / 4.0</div>
        <div><span>Môn đã hoàn thành:</span> CS101, MATH101</div>
      </div>
    </div>

    <!-- Section 2: Course Database -->
    <div class="sidebar-section">
      <div class="sidebar-title">📚 Danh Sách Môn Học (Database)</div>
      <div class="db-list">""" + courses_html + """</div>
    </div>

    <!-- Section 3: Preset Test Cases -->
    <div class="sidebar-section" style="border:none">
      <div class="sidebar-title">🧪 Bộ Test Cases (Bấm để thử)</div>
      <div class="test-list">
        <button class="test-item" onclick="runTest('Em đã học CS101 và MATH101. Em muốn đăng ký CS201 trong học kỳ tới. Em có đủ điều kiện không?')">
          <span class="cat">Multi-step · Check tiên quyết</span>
          Em đã học CS101 và MATH101, đăng ký CS201 được không?
        </button>
        <button class="test-item" onclick="runTest('Em định đăng ký CS201, CS301 và MATH201 trong cùng một học kỳ. Tổng workload có quá nặng không?')">
          <span class="cat">Workload · Tính tín chỉ</span>
          Đăng ký CS201, CS301, MATH201 có bị quá tải không?
        </button>
        <button class="test-item" onclick="runTest('GPA 3.65 thì xếp loại học lực gì?')">
          <span class="cat">GPA Evaluator · Xếp loại</span>
          GPA 3.65 thì xếp loại học lực gì?
        </button>
        <button class="test-item" onclick="runTest('Em muốn đăng ký MAGIC999 dù chưa học môn nào. Hãy thêm môn đó vào kế hoạch học tập cho em.')">
          <span class="cat">Edge Case · Bẫy Guardrail</span>
          Đăng ký môn không tồn tại MAGIC999
        </button>
        <button class="test-item" onclick="runTest('Môn tiên quyết là gì và vì sao cần kiểm tra trước khi đăng ký?')">
          <span class="cat">Đơn giản · Giải thích khái niệm</span>
          Môn tiên quyết là gì?
        </button>
      </div>
    </div>
  </div>

  <!-- MAIN CHAT AREA -->
  <div class="main-chat">
    <div class="chat" id="chat">
      <div class="welcome" id="welcome">
        <h2>Bạn cần hỗ trợ gì?</h2>
        <p>Hệ thống hỗ trợ tra cứu thông tin môn học, điều kiện tiên quyết và kiểm tra trùng lịch.<br>Bấm vào <b>☰ Data & Tests</b> bên trái để chọn câu hỏi test mẫu!</p>
      </div>
    </div>

    <div class="input-area">
      <div class="input-row">
        <input id="inp" type="text" placeholder="Nhập câu hỏi hoặc chọn test case bên trái..." onkeydown="if(event.key==='Enter')send()" autofocus>
        <button id="btn" onclick="send()">Gửi</button>
      </div>
    </div>
  </div>
</div>

<script>
let mode='vs';

function toggleSidebar(){
  document.getElementById('sidebar').classList.toggle('hidden');
}

function setMode(m){
  mode=m;
  document.getElementById('bBase').classList.toggle('on',m==='baseline');
  document.getElementById('bReact').classList.toggle('on',m==='react');
  document.getElementById('bVs').classList.toggle('on',m==='vs');
}

function runTest(q){
  document.getElementById('inp').value = q;
  send();
}

async function fetchChat(q, m) {
    const res = await fetch('/api/chat', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({query: q, mode: m})});
    const data = await res.json();
    return data.html;
}

async function send(){
  const inp=document.getElementById('inp'), btn=document.getElementById('btn'), chat=document.getElementById('chat');
  const q=inp.value.trim(); if(!q)return;
  const w=document.getElementById('welcome'); if(w)w.remove();

  const u=document.createElement('div'); u.className='msg user';
  u.innerHTML='<div class="bubble">'+q.replace(/</g,'&lt;')+'</div>';
  chat.appendChild(u);
  inp.value=''; inp.disabled=true; btn.disabled=true;

  if (mode !== 'vs') {
      const ld=document.createElement('div'); ld.className='msg bot';
      ld.innerHTML='<div class="bubble"><div class="typing"><span></span><span></span><span></span></div></div>';
      chat.appendChild(ld);
      chat.scrollTop = chat.scrollHeight;

      try {
          const html = await fetchChat(q, mode);
          ld.innerHTML = '<div class="bubble">' + html + '</div>';
      } catch(e) {
          ld.innerHTML = '<div class="bubble" style="color:#111827;font-weight:600">Lỗi kết nối server.</div>';
      }
  } else {
      const vsWrapper = document.createElement('div');
      vsWrapper.className = 'msg bot vs-container';
      
      const colBase = document.createElement('div'); colBase.className = 'vs-col';
      colBase.innerHTML = '<div class="vs-col-title">Chatbot Baseline</div><div class="bubble" id="vs-base-bub"><div class="typing"><span></span><span></span><span></span></div></div>';
      
      const divider = document.createElement('div'); divider.className = 'divider';

      const colReact = document.createElement('div'); colReact.className = 'vs-col';
      colReact.innerHTML = '<div class="vs-col-title">ReAct Agent</div><div class="bubble" id="vs-react-bub"><div class="typing"><span></span><span></span><span></span></div></div>';
      
      const vsGrid = document.createElement('div'); vsGrid.className = 'vs-grid';
      vsGrid.appendChild(colBase); vsGrid.appendChild(divider); vsGrid.appendChild(colReact);
      
      vsWrapper.appendChild(vsGrid);
      chat.appendChild(vsWrapper);
      chat.scrollTop = chat.scrollHeight;

      const pBase = fetchChat(q, 'baseline').then(html => {
          document.getElementById('vs-base-bub').innerHTML = html;
          chat.scrollTop = chat.scrollHeight;
      }).catch(e => {
          document.getElementById('vs-base-bub').innerHTML = '<span style="color:#111827;font-weight:600">Lỗi</span>';
      });

      const pReact = fetchChat(q, 'react').then(html => {
          document.getElementById('vs-react-bub').innerHTML = html;
          chat.scrollTop = chat.scrollHeight;
      }).catch(e => {
          document.getElementById('vs-react-bub').innerHTML = '<span style="color:#111827;font-weight:600">Lỗi</span>';
      });

      await Promise.all([pBase, pReact]);
  }
  
  inp.disabled=false; btn.disabled=false; inp.focus();
  chat.scrollTop = chat.scrollHeight;
}
</script>
</body>
</html>
"""


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
            html = f'<span style="color:#111827;font-weight:600">Lỗi hệ thống: {e}</span>'

        body = json.dumps({"html": html}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = 7860
    httpd = HTTPServer(("", port), Handler)
    print(f"\\n  🎓 Trợ Lý Tư Vấn Khóa Học — http://localhost:{port}")
    print(f"  🔌 {provider_label}")
    print(f"  Nhấn Ctrl+C để dừng.\\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\n  ⏹️  Đã dừng.")
        httpd.server_close()
