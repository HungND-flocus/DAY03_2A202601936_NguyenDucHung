"""
FastAPI backend cho AI Academic Advisor.

Chay:
    uvicorn src.server:app --reload
"""

import json
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

sys.path.append(str(Path(__file__).resolve().parent))

from db import init_database, status as db_status
from providers import get_llm_provider
from tools import (
    DATA_PATH,
    PLAN_STORE,
    analyze_custom_profile,
    analyze_student_profile,
    generate_custom_yearly_roadmap,
    generate_yearly_roadmap,
    get_academic_schema,
    get_student_context,
    list_schools,
    review_plan,
    search_courses,
    submit_plan,
)


ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"

app = FastAPI(title="AI Academic Advisor", version="0.1.0")
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
init_database()


class RoadmapRequest(BaseModel):
    school_id: str = "demo_uni"
    student_id: str = ""
    student_name: str = ""
    program_id: str = "cs"
    current_year: int = 1
    gpa: float | None = None
    completed_courses: str = ""
    failed_courses: str = ""
    goal: str = "balanced"
    career_track: str = ""
    interests: str = ""
    max_credits_per_term: int = 12
    start_year: int = 2026
    years: int = 4


class ChatRequest(BaseModel):
    school_id: str = "demo_uni"
    student_id: str
    question: str
    plan_id: str | None = None


class SubmitRequest(BaseModel):
    student_id: str


class ReviewRequest(BaseModel):
    advisor_id: str
    decision: str


def _loads(payload):
    return json.loads(payload)


def _academic_data():
    with DATA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _mock_explanation(profile, plan, question=""):
    if not profile.get("ok"):
        return profile.get("error", "Không tìm thấy hồ sơ sinh viên.")
    if plan and not plan.get("ok"):
        return plan.get("error", "Không sinh được lộ trình.")

    risk = profile["risk_level"]
    risk_text = {
        "low": "GPA đang ổn, có thể tăng tốc chọn lọc nếu không vượt tải.",
        "medium": "Có rủi ro trung bình, nên giữ workload cân bằng và ưu tiên môn nền tảng.",
        "high": "Rủi ro cao, cần giảm tải và xử lý môn nợ trước.",
        "custom": "Đây là hồ sơ tự nhập, hệ thống dùng dữ liệu bạn cung cấp để suy luận.",
    }.get(risk, "Hệ thống đã nhận hồ sơ và sẽ ưu tiên các ràng buộc học vụ đã validate.")
    if not plan:
        return f"{risk_text} Mình cần lộ trình hiện tại hoặc thêm mục tiêu để phân tích sâu hơn."

    first_loaded = next((term for term in plan["terms"] if term["courses"]), None)
    next_step = "Chưa có môn phù hợp trong kỳ đầu; nên kiểm tra lịch mở môn."
    if first_loaded:
        names = ", ".join(f"{c['id']} ({c['credits']} tín chỉ)" for c in first_loaded["courses"])
        next_step = f"Kỳ nên bắt đầu với {names} vì các môn này đã qua kiểm tra tiên quyết."
    alerts = " ".join(plan.get("alerts") or ["Không có cảnh báo lớn."])
    return f"{risk_text} {next_step} Cảnh báo: {alerts}"


def _llm_explanation(profile, plan, question):
    provider = get_llm_provider()
    if provider.__class__.__name__ == "MockProvider":
        return _mock_explanation(profile, plan, question)

    prompt = f"""
Bạn là AI Academic Advisor. Hãy phân tích ngắn gọn bằng tiếng Việt, không bịa mã môn.
Câu hỏi: {question}
Profile đã validate:
{json.dumps(profile, ensure_ascii=False, indent=2)}
Plan đã validate:
{json.dumps(plan, ensure_ascii=False, indent=2) if plan else "Chưa có plan"}

Trả lời gồm: nhận xét GPA/rủi ro, môn ưu tiên, cảnh báo, bước tiếp theo.
"""
    response = provider.generate(prompt)
    if response.startswith("["):
        return _mock_explanation(profile, plan, question)
    return response


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/db/status")
def database_status():
    return db_status()


@app.get("/api/catalog/search")
def catalog_search(q: str, school_id: str = "uit", limit: int = 20):
    results = _loads(search_courses(q, school_id))
    if results.get("courses"):
        results["courses"] = results["courses"][:limit]
    return results


@app.get("/api/schema")
def schema():
    return _loads(get_academic_schema())


@app.get("/api/schools")
def schools():
    return _loads(list_schools())


@app.get("/api/schools/{school_id}/students")
def students(school_id: str):
    school = _academic_data()["schools"].get(school_id)
    if not school:
        return {"ok": False, "error": f"Không tìm thấy trường {school_id}."}
    return {"ok": True, "students": [{"id": sid, **student} for sid, student in school["students"].items()]}


@app.get("/api/schools/{school_id}/programs")
def programs(school_id: str):
    school = _academic_data()["schools"].get(school_id)
    if not school:
        return {"ok": False, "error": f"Không tìm thấy trường {school_id}."}
    return {
        "ok": True,
        "programs": [
            {"id": pid, **program}
            for pid, program in school["programs"].items()
        ],
    }


@app.get("/api/schools/{school_id}/courses")
def courses(school_id: str, q: str = ""):
    if q:
        return _loads(search_courses(q, school_id))
    school = _academic_data()["schools"].get(school_id)
    if not school:
        return {"ok": False, "error": f"Không tìm thấy trường {school_id}."}
    return {"ok": True, "courses": [{"id": cid, **course} for cid, course in school["courses"].items()]}


@app.get("/api/students/{student_id}")
def student_context(student_id: str, school_id: str = "demo_uni"):
    return _loads(get_student_context(student_id, school_id))


@app.post("/api/roadmap")
def roadmap(req: RoadmapRequest):
    custom_profile = bool(req.student_name.strip() or not req.student_id.strip())
    if custom_profile:
        plan = _loads(generate_custom_yearly_roadmap(
            req.student_name,
            req.program_id,
            str(req.current_year),
            "" if req.gpa is None else str(req.gpa),
            req.completed_courses,
            req.failed_courses,
            req.goal,
            req.career_track,
            req.interests,
            str(req.max_credits_per_term),
            req.school_id,
            str(req.start_year),
            str(req.years),
        ))
        profile = _loads(analyze_custom_profile(
            req.student_name,
            str(req.current_year),
            "" if req.gpa is None else str(req.gpa),
            req.career_track,
            req.interests,
            req.failed_courses,
            req.program_id,
        ))
    else:
        plan = _loads(generate_yearly_roadmap(
            req.student_id,
            req.goal,
            req.career_track,
            req.interests,
            str(req.max_credits_per_term),
            req.school_id,
            str(req.start_year),
            str(req.years),
        ))
        profile = _loads(analyze_student_profile(
            req.student_id,
            "" if req.gpa is None else str(req.gpa),
            req.career_track,
            req.interests,
            req.school_id,
        ))
    return {"ok": plan.get("ok", False), "profile": profile, "plan": plan, "llm_analysis": _llm_explanation(profile, plan, "Sinh lộ trình học tập")}


@app.post("/api/chat")
def chat(req: ChatRequest):
    plan = PLAN_STORE.get(req.plan_id.upper()) if req.plan_id else None
    profile = _loads(analyze_student_profile(req.student_id, "", "", "", req.school_id))
    if not profile.get("ok") and plan:
        profile = {
            "ok": True,
            "student_id": plan["student_id"],
            "name": plan["student_name"],
            "year": plan.get("student_year"),
            "program_id": plan.get("program_id"),
            "gpa": plan.get("gpa") or 0,
            "risk_level": "custom",
            "career_track": plan.get("career_track", ""),
            "interests": plan.get("interests", []),
            "failed_courses": [],
            "recommendation_style": "custom roadmap",
        }
    return {"ok": True, "answer": _llm_explanation(profile, plan, req.question), "profile": profile, "plan": plan}


@app.post("/api/plans/{plan_id}/submit")
def submit(plan_id: str, req: SubmitRequest):
    return _loads(submit_plan(plan_id, req.student_id))


@app.post("/api/plans/{plan_id}/review")
def review(plan_id: str, req: ReviewRequest):
    return _loads(review_plan(plan_id, req.advisor_id, req.decision))
