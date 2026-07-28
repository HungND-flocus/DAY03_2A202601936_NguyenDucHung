# PHAN CONG CONG VIEC - NHOM 4 NGUOI

Du an: **Tro Ly Tu Van Khoa Hoc Sinh Vien**

Muc tieu: xay dung chatbot/agent co the tu van mon hoc dua tren nganh hoc, so tin chi, mon tien quyet, muc tieu nghe nghiep, lich hoc va nang luc hien tai cua sinh vien.

---

## 1. Nguyen tac lam viec

- Moi ban lam tren **branch rieng**, khong code truc tiep tren `main`.
- Moi branch nen phu trach it file nhat co the de tranh conflict.
- Truoc khi code: `git pull origin main`.
- Sau khi xong: commit, push branch, tao Pull Request, nho it nhat 1 ban review roi moi merge.
- Khong commit `.env`, API key, token, file cache, file tam.

---

## 2. Bang phan cong cho 4 thanh vien

| Thanh vien | Vai tro | File chinh | Nhiem vu |
| :--- | :--- | :--- | :--- |
| TV1 | Product + Data/Test Designer | `config/test_cases.json`, `docs/trace_eval.md` | Dinh nghia bai toan, viet test cases, lap bang Agentic Fit, ghi ket qua test |
| TV2 | Tool Engineer | `src/tools.py` | Viet cac tool tra cuu khoa hoc, check dieu kien tien quyet, tinh workload |
| TV3 | Prompt + Guardrail Engineer | `src/prompts.py` | Viet prompt baseline, ReAct prompt, quy tac an toan, gioi han lap |
| TV4 | Integrator + Git Lead + Demo | `src/app.py`, `README.md` | Noi tools/prompts/tests thanh app chay duoc, xu ly merge, chay demo cuoi |

Neu chua co ten thanh vien, gan tam:

- TV1: Nguyen Van A
- TV2: Nguyen Van B
- TV3: Nguyen Van C
- TV4: Nguyen Van D

---

## 3. Chi tiet cong viec tung thanh vien

### TV1 - Product + Data/Test Designer

Branch: `feature/tv1-test-cases`

Cong viec:

- Xac dinh ro nguoi dung: sinh vien can tu van chon mon hoc.
- Viet 5-7 test cases trong `config/test_cases.json`.
- Test cases can co:
  - Cau hoi don gian: hoi mon hoc phu hop cho nguoi moi bat dau.
  - Cau hoi multi-step: dua GPA, nganh, mon da hoc, yeu cau agent goi tool check dieu kien.
  - Cau hoi lap ke hoach: goi y 3 mon cho hoc ky toi voi gioi han tin chi.
  - Edge case: mon khong ton tai, thieu mon tien quyet, qua tai tin chi.
- Cap nhat `docs/trace_eval.md`:
  - Bang Agentic Fit.
  - So sanh Chatbot Baseline vs ReAct Agent.
  - Dan trace `Thought -> Action -> Observation -> Final Answer`.

Ket qua can ban giao:

- `config/test_cases.json` hop le JSON.
- `docs/trace_eval.md` co bang danh gia va ket qua test.

---

### TV2 - Tool Engineer

Branch: `feature/tv2-course-tools`

Cong viec:

- Sua `src/tools.py` thanh bo tool dung cho tu van khoa hoc.
- Nen co toi thieu 3 tool:
  - `search_courses(keyword: str)`: tim mon hoc theo tu khoa/nganh.
  - `check_prerequisites(course_id: str, completed_courses: str)`: kiem tra mon tien quyet.
  - `estimate_workload(course_ids: str)`: uoc tinh so tin chi va muc do nang.
- Moi tool can co docstring ro:
  - Input la gi.
  - Output la gi.
  - Khi loi thi tra ve chuoi `"LOI: ..."` thay vi lam crash app.
- Dang ky tool vao `AVAILABLE_TOOLS`.

Ket qua can ban giao:

- `src/tools.py` chay duoc doc lap.
- Tool khong crash khi nhap sai mon hoc hoac thieu du lieu.

---

### TV3 - Prompt + Guardrail Engineer

Branch: `feature/tv3-prompts`

Cong viec:

- Sua `src/prompts.py` theo dung chu de tu van khoa hoc.
- `CHATBOT_BASELINE_PROMPT`:
  - Tra loi nhu chatbot tu van thong thuong.
  - Khong duoc gia vo da tra cuu database.
  - Neu thieu thong tin, hoi lai sinh vien.
- `REACT_SYSTEM_PROMPT`:
  - Bat agent dung format:
    - `Thought: ...`
    - `Action: tool_name[tham_so]`
    - `Final Answer: ...`
  - Liet ke dung tool cua TV2.
  - Neu sinh vien thieu thong tin quan trong, hoi lai thay vi doan.
- Guardrail:
  - Giu `MAX_ITERATIONS = 3` hoac `4`.
  - Chan tu van qua so tin chi hop ly.
  - Neu chua dat dieu kien tien quyet thi khong goi y dang ky mon do.

Ket qua can ban giao:

- `src/prompts.py` ro format, ro tool, ro cach fallback.

---

### TV4 - Integrator + Git Lead + Demo

Branch: `feature/tv4-integrate-app`

Cong viec:

- Sua `src/app.py` de chay test cases cua TV1.
- Ket noi:
  - `config/test_cases.json`
  - `src/tools.py`
  - `src/prompts.py`
  - `providers.py`
- Chay duoc 2 che do:
  - Baseline chatbot.
  - ReAct agent co tool.
- Ghi log de TV1 dua vao `docs/trace_eval.md`.
- Lam Git lead:
  - Kiem tra PR cua cac ban.
  - Merge theo thu tu it conflict.
  - Chay test sau moi lan merge.
- Cap nhat `README.md` cach cai dat va chay demo neu can.

Ket qua can ban giao:

- `python src/app.py` chay duoc tu dau den cuoi.
- Demo duoc 1 cau don gian, 1 cau multi-step, 1 edge case.

---

## 4. Quy trinh Git cho ca nhom

### Lan dau clone project

```bash
git clone <link-repo>
cd DAY03_2A202601936_NguyenDucHung
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Tao branch rieng

TV1:

```bash
git switch main
git pull origin main
git switch -c feature/tv1-test-cases
```

TV2:

```bash
git switch main
git pull origin main
git switch -c feature/tv2-course-tools
```

TV3:

```bash
git switch main
git pull origin main
git switch -c feature/tv3-prompts
```

TV4:

```bash
git switch main
git pull origin main
git switch -c feature/tv4-integrate-app
```

### Commit va push

```bash
git status
git add <file-da-sua>
git commit -m "feat: mo ta ngan gon viec da lam"
git push -u origin <ten-branch>
```

Vi du:

```bash
git add config/test_cases.json docs/trace_eval.md
git commit -m "feat: add course advisor test cases"
git push -u origin feature/tv1-test-cases
```

### Tao Pull Request

Moi ban tao PR tu branch cua minh vao `main`.

Tieu de PR nen theo mau:

```text
[TV1] Add course advisor test cases
[TV2] Add course advisor tools
[TV3] Add ReAct prompts and guardrails
[TV4] Integrate course advisor app
```

Checklist PR:

- Code/file dung phan cong.
- Khong sua file cua ban khac neu khong can.
- `python src/app.py` khong loi, neu branch da co du file de chay.
- Khong co API key/token.

### Thu tu merge de it conflict

Nen merge theo thu tu:

1. TV1: `config/test_cases.json`, `docs/trace_eval.md`
2. TV2: `src/tools.py`
3. TV3: `src/prompts.py`
4. TV4: `src/app.py`, `README.md`

Sau moi PR duoc merge, ca nhom cap nhat lai may:

```bash
git switch main
git pull origin main
```

Neu branch cua ban bi cu so voi `main`:

```bash
git switch <ten-branch>
git pull origin main
git push
```

---

## 5. Cach xu ly conflict don gian

Khi `git pull` bao conflict:

```bash
git status
```

Mo file bi conflict, tim cac dau:

```text
<<<<<<< HEAD
noi dung cua minh
=======
noi dung tu main
>>>>>>> main
```

Giu lai phan dung, xoa 3 dong ky hieu conflict, sau do:

```bash
git add <file-bi-conflict>
git commit -m "fix: resolve merge conflict"
git push
```

Neu khong chac nen giu phan nao, hoi TV4 truoc khi commit.

---

## 6. Ke hoach theo 4 moc va output tung thanh vien

### Moc 1 - Dinh hinh & Danh gia Agentic Fit (20 phut)

Muc tieu: chot bai toan **Tro Ly Tu Van Khoa Hoc Sinh Vien** va chung minh bai toan can Agent.

| Thanh vien | Can lam | Output can co |
| :--- | :--- | :--- |
| TV1 | Mo ta user, nhu cau, ranh gioi bai toan; lap Scoring Matrix Agentic Fit | `docs/trace_eval.md` co bang Agentic Fit va ket luan co nen dung Agent |
| TV2 | De xuat cac tool can co de tra cuu khoa hoc | Danh sach tool du kien: `search_courses`, `check_prerequisites`, `estimate_workload` |
| TV3 | Liet ke failure modes va guardrails can co | Ghi nhanh quy tac: thieu thong tin thi hoi lai, khong du dieu kien thi khong goi y dang ky |
| TV4 | Kiem tra moi truong va app hien tai co chay duoc khong | Terminal chay duoc `python3 src/app.py` hoac ghi ro loi moi truong |

Output chung cua Moc 1:

- Bai toan da chot: tu van khoa hoc sinh vien.
- Co bang Agentic Fit trong `docs/trace_eval.md`.
- Co danh sach tool can lam.
- Co branch rieng cho moi thanh vien.

Commit goi y:

```bash
git commit -m "docs: define course advisor scope"
```

### Moc 2 - Baseline Chatbot & Khai bao Tool (30 phut)

Muc tieu: co chatbot baseline, tool specs va it nhat 5 test cases.

| Thanh vien | Can lam | Output can co |
| :--- | :--- | :--- |
| TV1 | Viet 5-7 test cases gom don gian, multi-step, thieu thong tin, edge case | `config/test_cases.json` hop le JSON, dung chu de tu van khoa hoc |
| TV2 | Viet tool specs va code tool ban dau trong `src/tools.py` | Tool co docstring, input/output ro, loi tra ve chuoi `LOI: ...` |
| TV3 | Viet `CHATBOT_BASELINE_PROMPT` va khung `REACT_SYSTEM_PROMPT` | `src/prompts.py` co prompt baseline, danh sach tool va format tra loi |
| TV4 | Noi baseline chatbot voi test cases va chay thu | `src/app.py` doc duoc `config/test_cases.json`, chay baseline tren it nhat 1 case |

Output chung cua Moc 2:

- `config/test_cases.json` co it nhat 5 test cases.
- `src/tools.py` co tool specs.
- `src/prompts.py` co baseline prompt.
- Baseline chatbot chay duoc de so sanh.

Commit goi y:

```bash
git commit -m "feat: add chatbot baseline and tool specs"
```

### Moc 3 - ReAct Loop & Safeguards (60 phut)

Muc tieu: lap Agent co vong lap `Thought -> Action -> Observation`, co guardrail va chay test.

| Thanh vien | Can lam | Output can co |
| :--- | :--- | :--- |
| TV1 | Chay/doi chieu test cases, ghi ket qua pass/fail va trace mau | `docs/trace_eval.md` co trace cua it nhat 1 case multi-step va 1 edge case |
| TV2 | Hoan thien tool implementation va dang ky vao `AVAILABLE_TOOLS` | `src/tools.py` co it nhat 3 tool chay duoc, khong crash khi input sai |
| TV3 | Hoan thien ReAct prompt va guardrails | `src/prompts.py` co `REACT_SYSTEM_PROMPT`, `MAX_ITERATIONS`, quy tac fallback |
| TV4 | Lap ReAct loop, parse Action, goi tool, chen Observation, in Final Answer | `src/app.py` chay duoc baseline va ReAct agent tren test cases |

Output chung cua Moc 3:

- `python3 src/app.py` chay duoc.
- Agent goi dung tool theo cau hoi.
- Co phanh `MAX_ITERATIONS`.
- Co log trace trong `docs/trace_eval.md`.

Commit goi y:

```bash
git commit -m "feat: add react agent loop and safeguards"
```

### Moc 4 - Tuong tac lien nhom & Hybrid Pattern (40 phut)

Muc tieu: test cheo, sua loi cuoi va ve flowchart chatbot/agent.

| Thanh vien | Can lam | Output can co |
| :--- | :--- | :--- |
| TV1 | Dung test case cua nhom minh de tan cong nhom khac; ghi nhan ket qua | `docs/trace_eval.md` co muc Cross-Audit va nhan xet pass/fail |
| TV2 | Sua tool neu bi hoi cau bay lam loi | `src/tools.py` xu ly duoc mon khong ton tai, thieu tien quyet, qua tai tin chi |
| TV3 | Sua prompt/guardrail neu agent doan bua hoac lap vo han | `src/prompts.py` co fallback lich su va quy tac khong tu van sai dieu kien |
| TV4 | Ve flowchart va chay demo ban cuoi | `docs/hybrid_flowchart.mermaid`, app demo duoc 3 case chinh |

Output chung cua Moc 4:

- Co bien ban cross-audit trong `docs/trace_eval.md`.
- Co `docs/hybrid_flowchart.mermaid`.
- Demo duoc 1 case don gian, 1 case multi-step, 1 edge case.
- Tat ca branch da merge vao `main`.

Commit goi y:

```bash
git commit -m "docs: add cross audit and hybrid flowchart"
```

---

## 7. Tieu chi hoan thanh

Project duoc xem la hoan chinh khi:

- `python src/app.py` chay duoc.
- Co it nhat 5 test cases dung chu de tu van khoa hoc.
- Co it nhat 3 tool trong `src/tools.py`.
- Prompt bat dung format ReAct.
- Co guardrail chong vong lap vo han.
- Co bao cao trace trong `docs/trace_eval.md`.
- Tat ca code da merge vao `main`.
- Repo khong chua secret/API key.
