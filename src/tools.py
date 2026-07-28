"""
Academic backend tools.

Du lieu hoc vu nam trong config/academic_data.json de sau nay them nhieu truong
ma khong phai sua code. Public tools tra ve JSON string de ReAct loop dung duoc;
backend FastAPI co the parse lai JSON thanh dict.
"""

import json
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parents[1] / "config" / "academic_data.json"
PLAN_STORE = {}


def _json(payload):
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _load_data():
    with DATA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _school(school_id="demo_uni"):
    school = _load_data()["schools"].get(school_id)
    if not school:
        raise ValueError(f"LOI: Khong tim thay truong {school_id}.")
    return school


def _split_csv(value):
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip().upper() for item in value if str(item).strip()]
    return [item.strip().upper() for item in str(value).split(",") if item.strip()]


def _terms(start_year=2026, years=4):
    start = int(start_year)
    return [
        {
            "academic_year": f"{year}-{year + 1}",
            "season": season,
            "label": f"{season} {year if season == 'Fall' else year + 1}",
        }
        for year in range(start, start + int(years))
        for season in ("Fall", "Spring")
    ]


def list_schools() -> str:
    """Liet ke cac truong co trong data."""
    data = _load_data()
    return _json({"ok": True, "schools": [{"id": sid, "name": s["name"]} for sid, s in data["schools"].items()]})


def get_academic_schema() -> str:
    """Mo ta schema toi thieu de import data truong moi."""
    return _json({
        "ok": True,
        "schema": {
            "schools": {
                "school_id": {
                    "name": "Ten truong",
                    "credit_limits": {"min_per_term": 6, "default_max_per_term": 12, "hard_max_per_term": 18},
                    "programs": {"program_id": {"name": "Ten CTDT", "advisor_mode": "degree_required", "required_courses": [], "tracks": {}}},
                    "courses": {"COURSE_ID": {"name": "", "credits": 3, "prerequisites": [], "terms": [], "tags": [], "difficulty": 3}},
                    "students": {"STUDENT_ID": {"name": "", "year": 1, "program_id": "", "gpa": 3.0, "completed_courses": [], "failed_courses": [], "interests": [], "career_track": "", "goal": ""}},
                    "advisors": {"ADVISOR_ID": {"name": "", "student_ids": []}},
                }
            }
        },
    })


def get_student_context(student_id: str, school_id: str = "demo_uni") -> str:
    """Lay ho so hoc tap da validate cua sinh vien."""
    try:
        school = _school(school_id)
    except ValueError as exc:
        return _json({"ok": False, "error": str(exc)})

    sid = student_id.strip().upper()
    student = school["students"].get(sid)
    if not student:
        return _json({"ok": False, "error": f"LOI: Khong tim thay sinh vien {sid}."})
    program = school["programs"][student["program_id"]]
    completed = set(student["completed_courses"])
    track = student.get("career_track", "")
    remaining = [cid for cid in _wanted_courses(program, student, school["courses"], track, student.get("interests", [])) if cid not in completed]
    return _json({"ok": True, "school_id": school_id, "student_id": sid, "program": program, "remaining_courses": remaining, **student})


def search_courses(keyword: str, school_id: str = "demo_uni") -> str:
    """Tim mon hoc theo ma, ten, tag nghe nghiep hoac tu khoa."""
    try:
        courses = _school(school_id)["courses"]
    except ValueError as exc:
        return _json({"ok": False, "error": str(exc)})

    query = keyword.strip().lower()
    if not query:
        return _json({"ok": False, "error": "LOI: Can tu khoa de tim mon hoc."})

    results = []
    for course_id, course in courses.items():
        haystack = " ".join([course_id, course["name"], course.get("description", ""), *course.get("tags", [])]).lower()
        if query in haystack:
            results.append({"id": course_id, **course})
    if not results:
        return _json({"ok": False, "error": f"LOI: Khong tim thay mon hoc phu hop voi '{keyword}'."})
    return _json({"ok": True, "courses": results})


def check_prerequisites(course_id: str, completed_courses: str, school_id: str = "demo_uni") -> str:
    """Kiem tra sinh vien da du dieu kien tien quyet cho mot mon hoc chua."""
    try:
        courses = _school(school_id)["courses"]
    except ValueError as exc:
        return _json({"ok": False, "error": str(exc)})

    code = course_id.strip().upper()
    course = courses.get(code)
    if not course:
        return _json({"ok": False, "error": f"LOI: Mon {code} khong ton tai trong danh muc hoc vu."})
    completed = set(_split_csv(completed_courses))
    missing = [item for item in course["prerequisites"] if item not in completed]
    return _json({"ok": True, "course_id": code, "course_name": course["name"], "eligible": not missing, "missing_prerequisites": missing})


def estimate_workload(course_ids: str, school_id: str = "demo_uni") -> str:
    """Tinh tong tin chi va muc do nang cua mot danh sach mon."""
    try:
        courses = _school(school_id)["courses"]
    except ValueError as exc:
        return _json({"ok": False, "error": str(exc)})

    codes = _split_csv(course_ids)
    unknown = [code for code in codes if code not in courses]
    if unknown:
        return _json({"ok": False, "error": f"LOI: Mon khong ton tai: {', '.join(unknown)}."})
    total = sum(courses[code]["credits"] for code in codes)
    difficulty = sum(courses[code].get("difficulty", 3) for code in codes)
    level = "nhẹ" if total <= 6 else "vừa" if total <= 9 else "nặng"
    return _json({"ok": True, "course_ids": codes, "total_credits": total, "difficulty_score": difficulty, "workload_level": level, "warning": "Vuot 9 tin chi, nen hoi co van truoc khi dang ky." if total > 9 else ""})


def _profile(student_id, student, gpa="", career_track="", interests=""):
    actual_gpa = float(gpa or student.get("gpa") or 0)
    track = career_track or student.get("career_track", "")
    interest_list = [item.strip() for item in (interests or ",".join(student.get("interests", []))).split(",") if item.strip()]
    risk = "low"
    if actual_gpa < 2.7 or student.get("failed_courses"):
        risk = "medium"
    if actual_gpa < 2.3 or len(student.get("failed_courses", [])) >= 2:
        risk = "high"
    return _json({
        "ok": True,
        "student_id": student_id,
        "name": student["name"],
        "year": student.get("year"),
        "program_id": student.get("program_id"),
        "gpa": actual_gpa,
        "risk_level": risk,
        "career_track": track,
        "interests": interest_list,
        "failed_courses": student.get("failed_courses", []),
        "recommendation_style": "balanced workload" if risk != "low" else "can accelerate selectively",
    })


def analyze_student_profile(student_id: str, gpa: str = "", career_track: str = "", interests: str = "", school_id: str = "demo_uni") -> str:
    """Phan tich GPA, mon no, dinh huong va so thich de tao brief cho LLM."""
    try:
        school = _school(school_id)
    except ValueError as exc:
        return _json({"ok": False, "error": str(exc)})

    sid = student_id.strip().upper()
    student = school["students"].get(sid)
    if not student:
        return _json({"ok": False, "error": f"LOI: Khong tim thay sinh vien {sid}."})
    return _profile(sid, student, gpa, career_track, interests)


def analyze_custom_profile(student_name: str, current_year: str, gpa: str = "3.0", career_track: str = "", interests: str = "", failed_courses: str = "", program_id: str = "cs") -> str:
    """Phan tich ho so sinh vien tu nhap, khong can co san trong database."""
    student = {
        "name": student_name.strip() or "Sinh viên tự nhập",
        "year": int(current_year or 1),
        "program_id": program_id,
        "gpa": float(gpa or 0),
        "failed_courses": _split_csv(failed_courses),
        "interests": [item.strip() for item in interests.split(",") if item.strip()],
        "career_track": career_track,
    }
    return _profile("CUSTOM", student, gpa, career_track, interests)


def _course_priority(course_id, course, student, program, career_track, interests):
    tags = set(tag.lower() for tag in course.get("tags", []))
    wanted = set(item.strip().lower() for item in [career_track, *interests] if item.strip())
    score = 100
    if course_id in student.get("failed_courses", []):
        score -= 60
    if course_id in program.get("required_courses", []):
        score -= 30
    if tags & wanted or course.get("name", "").lower() in wanted:
        score -= 25
    score += len(course.get("prerequisites", [])) * 4
    if float(student.get("gpa", 0)) < 2.7:
        score += course.get("difficulty", 3) * 3
    return score


def _pick_until(pool, min_credits, courses, student, program, track, interests, excluded, available=None, skip_unreachable=False):
    picked = []
    credits = 0
    reachable = set(available or []) | set(student.get("completed_courses", [])) | set(pool)
    for course_id in sorted(dict.fromkeys(pool), key=lambda cid: _course_priority(cid, courses.get(cid, {}), student, program, track, interests)):
        course = courses.get(course_id)
        if course_id in excluded or not course or course.get("credits", 0) <= 0:
            continue
        if skip_unreachable and any(pre not in reachable for pre in course.get("prerequisites", [])):
            continue
        picked.append(course_id)
        credits += course.get("credits", 0)
        if credits >= min_credits:
            break
    return picked


def _wanted_courses(program, student, courses, track, interests):
    if program.get("advisor_mode") != "elective_only":
        return list(dict.fromkeys([*student.get("failed_courses", []), *program.get("required_courses", []), *program.get("tracks", {}).get(track, [])]))

    excluded = set(program.get("mandatory_courses_removed_from_advising", program.get("required_courses", [])))
    requirements = program.get("graduation_requirements", {})
    pools = program.get("elective_pools", {})
    choice_pool = []
    for pool_name, course_ids in pools.items():
        if pool_name not in {"free_electives", "graduation_topics"}:
            choice_pool.extend(course_ids)

    interest_list = interests if isinstance(interests, list) else [item.strip() for item in str(interests).split(",") if item.strip()]
    major_pool = [*student.get("failed_courses", []), *program.get("tracks", {}).get(track, []), *choice_pool]
    major = _pick_until(major_pool, requirements.get("major_elective_min_credits", 16), courses, student, program, track, interest_list, excluded)
    free = _pick_until(pools.get("free_electives", []), requirements.get("free_elective_min_credits", 10), courses, student, program, track, interest_list, excluded, major, True)
    graduation = _pick_until(pools.get("graduation_topics", []), requirements.get("graduation_min_credits", 10), courses, student, program, track, interest_list, excluded, [*major, *free], True)
    return list(dict.fromkeys([*major, *free, *graduation]))


def _build_roadmap(school_id, student_id, goal, career_track, interests, max_credits_per_term, start_year, years, store, student_override=None):
    school = _school(school_id)
    sid = student_id.strip().upper() or "CUSTOM"
    student = student_override or school["students"].get(sid)
    if not student:
        return {"ok": False, "error": f"LOI: Khong tim thay sinh vien {sid}."}

    limits = school["credit_limits"]
    max_credits = int(max_credits_per_term or limits["default_max_per_term"])
    if max_credits < limits["min_per_term"] or max_credits > limits["hard_max_per_term"]:
        return {"ok": False, "error": f"LOI: Tin chi moi ky phai trong khoang {limits['min_per_term']}-{limits['hard_max_per_term']}."}

    courses = school["courses"]
    program = school["programs"].get(student["program_id"])
    if not program:
        return {"ok": False, "error": f"LOI: Khong tim thay chuong trinh {student['program_id']}."}
    completed = set(student["completed_courses"])
    interest_list = [item.strip() for item in (interests or ",".join(student.get("interests", []))).split(",") if item.strip()]
    track = career_track or student.get("career_track", "")
    wanted = _wanted_courses(program, student, courses, track, interest_list)
    remaining = [course_id for course_id in wanted if course_id not in completed]
    alerts = []
    if program.get("advisor_mode") == "elective_only":
        ignored = sorted(set(student.get("failed_courses", [])) & set(program.get("mandatory_courses_removed_from_advising", [])))
        if ignored:
            alerts.append("Đã bỏ qua môn bắt buộc/BB trong roadmap tự chọn: " + ", ".join(ignored) + ".")
    terms = []
    blocked = {}

    # ponytail: greedy planner; swap for OR-Tools CP-SAT when real catalog scale needs optimization.
    for term in _terms(start_year, years):
        selected = []
        credits = 0
        candidates = sorted(
            list(remaining),
            key=lambda cid: _course_priority(cid, courses.get(cid, {}), student, program, track, interest_list),
        )
        for course_id in candidates:
            course = courses.get(course_id)
            if not course:
                alerts.append(f"{course_id}: mon khong ton tai.")
                remaining.remove(course_id)
                continue
            if term["season"] not in course["terms"]:
                continue
            missing = [pre for pre in course["prerequisites"] if pre not in completed]
            if missing:
                blocked[course_id] = missing
                continue
            if credits + course["credits"] > max_credits:
                continue
            if float(student.get("gpa", 0)) < 2.7 and course.get("difficulty", 3) >= 5 and selected:
                continue
            scope = "tư vấn môn tự chọn/tự học" if program.get("advisor_mode") == "elective_only" else goal
            selected.append({"id": course_id, **course, "why": f"Phù hợp {scope}, track {track}, sở thích {', '.join(interest_list) or 'chưa có'}."})
            credits += course["credits"]
            remaining.remove(course_id)
        completed.update(item["id"] for item in selected)
        terms.append({**term, "credits": credits, "courses": selected})

    if remaining:
        detail = "; ".join(f"{cid} thiếu {', '.join(blocked[cid])}" for cid in remaining if cid in blocked)
        suffix = f" ({detail})" if detail else ""
        alerts.append("Chưa xếp được: " + ", ".join(remaining) + suffix + ". Cần thêm học kỳ, mở môn đúng kỳ, hoặc nhập đủ môn tiên quyết đã hoàn thành.")

    plan_id = f"PLAN-{sid}-{len(PLAN_STORE) + 1:03d}"
    plan = {
        "ok": True,
        "school_id": school_id,
        "plan_id": plan_id,
        "student_id": sid,
        "student_name": student["name"],
        "student_year": student.get("year"),
        "program_id": student.get("program_id"),
        "program_name": program["name"],
        "advisor_mode": program.get("advisor_mode", "degree_required"),
        "advising_scope": program.get("advising_scope", "Tư vấn theo yêu cầu chương trình."),
        "advisor_id": student.get("advisor_id", "CUSTOM_ADV"),
        "status": "draft",
        "goal": goal,
        "career_track": track,
        "interests": interest_list,
        "gpa": student.get("gpa"),
        "max_credits_per_term": max_credits,
        "terms": terms,
        "alerts": alerts,
    }
    if store:
        PLAN_STORE[plan_id] = plan
    return plan


def generate_yearly_roadmap(student_id: str, goal: str = "balanced", career_track: str = "", interests: str = "", max_credits_per_term: str = "12", school_id: str = "demo_uni", start_year: str = "2026", years: str = "4") -> str:
    """Sinh lo trinh qua tung nam/hoc ky dua tren GPA, so thich, dinh huong va rang buoc hoc vu."""
    try:
        return _json(_build_roadmap(school_id, student_id, goal, career_track, interests, max_credits_per_term, start_year, years, True))
    except ValueError as exc:
        return _json({"ok": False, "error": str(exc)})


def generate_custom_yearly_roadmap(student_name: str, program_id: str = "cs", current_year: str = "1", gpa: str = "3.0", completed_courses: str = "", failed_courses: str = "", goal: str = "balanced", career_track: str = "", interests: str = "", max_credits_per_term: str = "12", school_id: str = "uit", start_year: str = "2026", years: str = "4") -> str:
    """Sinh lo trinh cho ho so sinh vien tu nhap."""
    student = {
        "name": student_name.strip() or "Sinh viên tự nhập",
        "year": int(current_year or 1),
        "program_id": program_id,
        "gpa": float(gpa or 0),
        "completed_courses": _split_csv(completed_courses),
        "failed_courses": _split_csv(failed_courses),
        "interests": [item.strip() for item in interests.split(",") if item.strip()],
        "career_track": career_track,
        "goal": goal,
        "advisor_id": "CUSTOM_ADV",
    }
    try:
        return _json(_build_roadmap(school_id, "CUSTOM", goal, career_track, interests, max_credits_per_term, start_year, years, True, student))
    except ValueError as exc:
        return _json({"ok": False, "error": str(exc)})


def generate_study_plan(student_id: str, goal: str = "balanced", career_track: str = "AI", max_credits_per_term: str = "9") -> str:
    """Alias cu cho lab ReAct."""
    return generate_yearly_roadmap(student_id, goal, career_track, "", max_credits_per_term, "demo_uni", "2026", "2")


def simulate_what_if(student_id: str, max_credits_per_term: str, career_track: str = "AI") -> str:
    """Thu kich ban what-if ma khong ghi de ke hoach goc."""
    try:
        plan = _build_roadmap("demo_uni", student_id, "what_if", career_track, "", max_credits_per_term, "2026", "2", False)
    except ValueError as exc:
        return _json({"ok": False, "error": str(exc)})
    if plan.get("ok"):
        plan["status"] = "simulation_only"
    return _json(plan)


def submit_plan(plan_id: str, student_id: str) -> str:
    """Chuyen ke hoach tu draft sang pending_approval de co van duyet."""
    plan = PLAN_STORE.get(plan_id.strip().upper())
    if not plan:
        return _json({"ok": False, "error": f"LOI: Khong tim thay ke hoach {plan_id}. Hay sinh ke hoach truoc."})
    if plan["student_id"] != student_id.strip().upper():
        return _json({"ok": False, "error": "LOI: Sinh vien khong so huu ke hoach nay."})
    plan["status"] = "pending_approval"
    return _json({"ok": True, "plan_id": plan["plan_id"], "status": plan["status"], "message": "Da gui ke hoach cho co van."})


def review_plan(plan_id: str, advisor_id: str, decision: str) -> str:
    """Co van duyet hoac tu choi ke hoach dang cho duyet."""
    plan = PLAN_STORE.get(plan_id.strip().upper())
    if not plan:
        return _json({"ok": False, "error": f"LOI: Khong tim thay ke hoach {plan_id}."})

    school = _school(plan.get("school_id", "demo_uni"))
    student = school["students"].get(plan["student_id"], {"advisor_id": plan.get("advisor_id", "CUSTOM_ADV")})
    if advisor_id.strip().upper() != student.get("advisor_id"):
        return _json({"ok": False, "error": "LOI: Co van khong phu trach sinh vien nay."})
    if plan["status"] != "pending_approval":
        return _json({"ok": False, "error": "LOI: Chi duyet duoc ke hoach o trang thai pending_approval."})

    normalized = decision.strip().lower()
    if normalized not in {"approve", "reject"}:
        return _json({"ok": False, "error": "LOI: decision phai la approve hoac reject."})
    plan["status"] = "approved" if normalized == "approve" else "rejected"
    return _json({"ok": True, "plan_id": plan["plan_id"], "status": plan["status"]})


AVAILABLE_TOOLS = {
    "list_schools": list_schools,
    "get_academic_schema": get_academic_schema,
    "get_student_context": get_student_context,
    "search_courses": search_courses,
    "check_prerequisites": check_prerequisites,
    "estimate_workload": estimate_workload,
    "analyze_student_profile": analyze_student_profile,
    "analyze_custom_profile": analyze_custom_profile,
    "generate_yearly_roadmap": generate_yearly_roadmap,
    "generate_custom_yearly_roadmap": generate_custom_yearly_roadmap,
    "generate_study_plan": generate_study_plan,
    "simulate_what_if": simulate_what_if,
    "submit_plan": submit_plan,
    "review_plan": review_plan,
}


if __name__ == "__main__":
    assert json.loads(check_prerequisites("CS201", "CS101"))["eligible"] is True
    assert json.loads(estimate_workload("CS201,DS201,AI301"))["total_credits"] == 9
    assert json.loads(generate_yearly_roadmap("S001", "balanced", "Data Science", "AI,research", "12"))["ok"] is True
    uit_plan = json.loads(generate_custom_yearly_roadmap("Test", "cs", "3", "3.2", "IT003,MA004,MA005,CS106,CS114", "MA006", "balanced", "AI", "AI,research", "18", "uit", "2026", "2"))
    scheduled = {course["id"] for term in uit_plan["terms"] for course in term["courses"]}
    forbidden = set(_school("uit")["programs"]["cs"].get("mandatory_courses_removed_from_advising", []))
    assert not scheduled & forbidden
    print("tools self-check OK")
