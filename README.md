# AI Academic Advisor

Full-stack MVP cho trợ lý tư vấn lộ trình học tập sinh viên.

Hệ thống phân tích GPA, môn đã hoàn thành, môn cần lưu ý, sở thích cá nhân, định hướng nghề nghiệp, tín chỉ mỗi kỳ và yêu cầu chương trình để soạn lộ trình theo từng năm/học kỳ. Với UIT-CS, planner chạy chế độ tư vấn môn tự chọn/tự học: môn bắt buộc BB được giữ trong catalog nhưng không đưa vào roadmap. LLM chỉ giải thích và tư vấn trên dữ liệu đã validate; planner/rule-based backend quyết định môn học, tiên quyết, tín chỉ và trạng thái phê duyệt.

## Stack

- Frontend: HTML/CSS/JavaScript dashboard tại `web/`
- Backend: FastAPI tại `src/server.py`
- Academic engine: `src/tools.py`
- LLM provider: `src/providers.py` (`mock` mặc định, hoặc OpenAI/Gemini/Anthropic/OpenRouter)
- Data nhiều trường: `config/academic_data.json`
- Database local: SQLite tại `data/academic_advisor.sqlite`, được build từ JSON khi backend khởi động

## Chạy full-stack

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
uvicorn src.server:app --reload --port 8000
```

Mở:

```text
http://127.0.0.1:8000
```

Luồng chính trên giao diện:

1. Chọn trường.
2. Tự nhập tên sinh viên.
3. Chọn chương trình đang học và năm học hiện hành.
4. Nhập GPA, môn đã hoàn thành, môn cần lưu ý hoặc muốn học lại.
5. Chọn mục tiêu, định hướng chuyên ngành, sở thích cá nhân.
6. Bấm **Sinh lộ trình** để hệ thống lập kế hoạch cho các năm/học kỳ tiếp theo.

## Dùng LLM thật

Tạo `.env`:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key
LLM_MODEL=gpt-4o-mini
```

Không có API key thì app tự dùng `MockProvider` để demo offline.

## API chính

- `GET /api/schools`
- `GET /api/db/status`
- `GET /api/schools/{school_id}/students`
- `GET /api/schools/{school_id}/courses`
- `POST /api/roadmap`
- `POST /api/chat`
- `POST /api/plans/{plan_id}/submit`
- `POST /api/plans/{plan_id}/review`

`POST /api/roadmap` nhận được cả sinh viên có sẵn trong database lẫn hồ sơ tự nhập:

```json
{
  "school_id": "uit",
  "student_name": "Nguyen Van A",
  "program_id": "cs",
  "current_year": 2,
  "gpa": 3.1,
  "completed_courses": "IT001, MA003, MA004",
  "failed_courses": "MA006",
  "goal": "balanced",
  "career_track": "AI",
  "interests": "AI, Data Science, research",
  "max_credits_per_term": 18,
  "years": 3
}
```

## Schema data trường học

Hiện đã có data mẫu cho:

- `demo_uni`: trường demo nhỏ
- `uit`: CTĐT ngành Khoa học máy tính, Trường Đại học Công nghệ Thông tin - ĐHQG-HCM, được process từ tài liệu bạn cung cấp. Có 74 môn học CTĐT, nhóm định hướng AI/NLP/Thị giác máy tính/Đa phương tiện/Công nghệ tri thức và 3 sinh viên demo `UIT001`, `UIT002`, `UIT003`. Chương trình `uit/cs` đang đặt `advisor_mode=elective_only`, nên các môn BB trong `mandatory_courses_removed_from_advising` không được xếp vào roadmap.
- Danh mục mô tả môn học toàn trường: đã process 401 môn; 69 môn trùng CTĐT được bổ sung mô tả, 332 môn ngoài CTĐT được thêm vào catalog để agent tìm kiếm/gợi ý theo sở thích. Các môn catalog-only có `credits=0` vì file mô tả không có thông tin tín chỉ.

Thêm trường mới trong `config/academic_data.json` theo cấu trúc:

```json
{
  "schools": {
    "school_id": {
      "name": "Tên trường",
      "credit_limits": {
        "min_per_term": 6,
        "default_max_per_term": 12,
        "hard_max_per_term": 18
      },
      "programs": {
        "program_id": {
          "name": "Tên chương trình",
          "required_courses": ["CS101"],
          "tracks": {
            "AI": ["MATH101", "AI301"]
          }
        }
      },
      "courses": {
        "CS101": {
          "name": "Nhập môn Lập trình",
          "credits": 3,
          "prerequisites": [],
          "terms": ["Fall", "Spring"],
          "tags": ["software", "foundation"],
          "difficulty": 2
        }
      },
      "students": {
        "S001": {
          "name": "Minh Anh",
          "year": 1,
          "program_id": "program_id",
          "gpa": 3.2,
          "completed_courses": [],
          "failed_courses": [],
          "interests": ["AI"],
          "career_track": "AI",
          "goal": "balanced",
          "advisor_id": "ADV01"
        }
      },
      "advisors": {
        "ADV01": {
          "name": "Cố vấn",
          "student_ids": ["S001"]
        }
      }
    }
  }
}
```

## CLI lab vẫn chạy được

```bash
python3 src/app.py
```

## Guardrails

- Không bịa mã môn, tiên quyết, số tín chỉ hoặc điều kiện tốt nghiệp.
- Môn học phải tồn tại trong data trường.
- Với chương trình `elective_only`, planner không xếp môn bắt buộc/BB vào roadmap.
- Planner không xếp môn khi thiếu tiên quyết.
- What-if không ghi đè kế hoạch gốc.
- Kế hoạch đi qua `draft -> pending_approval -> approved/rejected`.

## Có dùng Agent không?

Có.

- CLI `python3 src/app.py` chạy ReAct loop rõ ràng: `Thought -> Action -> Observation -> Final Answer`.
- Web backend dùng cùng tool/planner đã validate và gọi LLM ở `/api/roadmap`, `/api/chat` để phân tích GPA, sở thích, định hướng và giải thích lộ trình.
- LLM không tự quyết định môn học; agent/tool layer mới được quyền đọc database, kiểm tra tiên quyết, tính tín chỉ và sinh roadmap.
