"""
🛠️ TOOL REGISTRY & SCHEMAS — Chủ đề: Trợ Lý Tư Vấn Khóa Học Sinh Viên
Dành cho Role 2: Tool & Spec Engineer (Mốc 2: Chuẩn hóa Tool Specs & Docstrings)

Mốc 2 — Danh sách tool & Tool Specs đã chuẩn hóa:
  1. search_courses          — Tìm khóa học theo từ khóa / ngành học
  2. check_prerequisites     — Kiểm tra điều kiện tiên quyết của môn học
  3. estimate_workload       — Ước tính tổng tín chỉ & mức độ nặng
  4. get_course_detail       — Xem chi tiết một môn học (mô tả, giảng viên, lịch)
  5. check_schedule_conflict — Kiểm tra xung đột lịch học giữa các môn

Bổ sung Mốc 2:
  - Helper chuẩn hóa mã môn: `_normalize_course_id("cs 301") -> "CS301"`
  - Helper tự động tạo Tool Specs cho ReAct System Prompt: `get_tools_spec_prompt()`
"""

# =============================================================================
# 📚 DỮ LIỆU MẪU (Mock Data) — Dùng thay thế database thực tế
# =============================================================================

COURSE_DATABASE = {
    "CS101": {
        "name": "Nhập môn Lập trình",
        "credits": 3,
        "difficulty": "Dễ",
        "prerequisites": [],
        "schedule": "Thứ 2 (7:30 - 9:30)",
        "instructor": "TS. Nguyễn Văn An",
        "description": "Giới thiệu tư duy lập trình và ngôn ngữ Python cơ bản.",
        "majors": ["CNTT", "KHMT", "AI"],
    },
    "CS201": {
        "name": "Cấu trúc Dữ liệu & Giải thuật",
        "credits": 4,
        "difficulty": "Trung bình",
        "prerequisites": ["CS101"],
        "schedule": "Thứ 3 (9:30 - 11:30)",
        "instructor": "PGS. Trần Thị Bình",
        "description": "Stack, Queue, Tree, Graph và các thuật toán sắp xếp, tìm kiếm.",
        "majors": ["CNTT", "KHMT", "AI"],
    },
    "CS301": {
        "name": "Trí tuệ Nhân tạo",
        "credits": 3,
        "difficulty": "Khó",
        "prerequisites": ["CS201", "MATH201"],
        "schedule": "Thứ 4 (13:30 - 15:30)",
        "instructor": "GS. Lê Quốc Cường",
        "description": "Các thuật toán AI cổ điển, học máy cơ bản và ứng dụng thực tế.",
        "majors": ["AI", "CNTT"],
    },
    "CS302": {
        "name": "Học Máy (Machine Learning)",
        "credits": 4,
        "difficulty": "Khó",
        "prerequisites": ["CS301", "MATH202"],
        "schedule": "Thứ 5 (7:30 - 9:30)",
        "instructor": "TS. Phạm Minh Đức",
        "description": "Supervised, Unsupervised Learning, Neural Networks.",
        "majors": ["AI"],
    },
    "MATH101": {
        "name": "Giải tích 1",
        "credits": 4,
        "difficulty": "Trung bình",
        "prerequisites": [],
        "schedule": "Thứ 2 (13:30 - 15:30)",
        "instructor": "TS. Hoàng Thị Lan",
        "description": "Giới hạn, đạo hàm, tích phân và ứng dụng.",
        "majors": ["CNTT", "KHMT", "AI", "KT"],
    },
    "MATH201": {
        "name": "Đại số Tuyến tính",
        "credits": 3,
        "difficulty": "Trung bình",
        "prerequisites": ["MATH101"],
        "schedule": "Thứ 6 (9:30 - 11:30)",
        "instructor": "PGS. Vũ Thanh Hà",
        "description": "Ma trận, không gian vector, trị riêng, vector riêng.",
        "majors": ["CNTT", "KHMT", "AI"],
    },
    "MATH202": {
        "name": "Xác suất & Thống kê",
        "credits": 3,
        "difficulty": "Trung bình",
        "prerequisites": ["MATH101"],
        "schedule": "Thứ 3 (13:30 - 15:30)",
        "instructor": "TS. Ngô Thị Mai",
        "description": "Lý thuyết xác suất, phân phối xác suất, kiểm định thống kê.",
        "majors": ["AI", "CNTT", "KT"],
    },
    "SE201": {
        "name": "Kỹ nghệ Phần mềm",
        "credits": 3,
        "difficulty": "Trung bình",
        "prerequisites": ["CS101"],
        "schedule": "Thứ 4 (9:30 - 11:30)",
        "instructor": "TS. Đinh Văn Khoa",
        "description": "Quy trình phát triển phần mềm, UML, Agile, kiểm thử.",
        "majors": ["CNTT", "KHMT"],
    },
    "DB201": {
        "name": "Cơ sở Dữ liệu",
        "credits": 3,
        "difficulty": "Trung bình",
        "prerequisites": ["CS101"],
        "schedule": "Thứ 5 (13:30 - 15:30)",
        "instructor": "TS. Chu Thị Hương",
        "description": "Mô hình quan hệ, SQL, thiết kế và tối ưu cơ sở dữ liệu.",
        "majors": ["CNTT", "KHMT", "AI"],
    },
    "NET201": {
        "name": "Mạng Máy tính",
        "credits": 3,
        "difficulty": "Trung bình",
        "prerequisites": ["CS101"],
        "schedule": "Thứ 6 (13:30 - 15:30)",
        "instructor": "PGS. Bùi Văn Dũng",
        "description": "Mô hình OSI, TCP/IP, các giao thức mạng phổ biến.",
        "majors": ["CNTT", "KHMT"],
    },
}

# Quy định tối đa tín chỉ mỗi học kỳ
MAX_CREDITS_PER_SEMESTER = 24


# =============================================================================
# 🛠️ HELPER FUNCTIONS (Chuẩn hóa dữ liệu đầu vào)
# =============================================================================

def _normalize_course_id(raw_id: str) -> str:
    """
    Chuẩn hóa mã môn học nhập vào (ví dụ: 'cs 101' -> 'CS101', 'math-201' -> 'MATH201').
    """
    if not raw_id:
        return ""
    cleaned = raw_id.upper().strip().replace(" ", "").replace("-", "")
    return cleaned


# =============================================================================
# 🔧 TOOL 1: search_courses
# =============================================================================

def search_courses(keyword: str) -> str:
    """
    Mô tả: Tìm kiếm các khóa học trong hệ thống theo từ khóa, tên môn, mã môn hoặc ngành học.

    Args:
        keyword (str): Từ khóa cần tra cứu (Ví dụ: 'AI', 'CNTT', 'lập trình', 'CS101', 'toán').

    Returns:
        str: Danh sách khóa học tìm thấy kèm thông tin cơ bản (mã, tên, tín chỉ, độ khó).
             Nếu lỗi/rỗng/không tìm thấy, trả về chuỗi thông báo "LỖI: ...".
    """
    if not keyword or not keyword.strip():
        return "LỖI: Từ khóa tìm kiếm không được để trống."

    kw = keyword.lower().strip()
    matched = []

    for course_id, info in COURSE_DATABASE.items():
        # Tìm theo mã môn, tên môn, ngành, hoặc mô tả
        if (
            kw in course_id.lower()
            or kw in info["name"].lower()
            or kw in info["description"].lower()
            or any(kw in major.lower() for major in info["majors"])
        ):
            matched.append(
                f"  • [{course_id}] {info['name']} — {info['credits']} tín chỉ, "
                f"Độ khó: {info['difficulty']}, Ngành: {', '.join(info['majors'])}"
            )

    if not matched:
        return (
            f"LỖI: Không tìm thấy môn học nào khớp với từ khóa '{keyword}'. "
            f"Gợi ý từ khóa hợp lệ: 'AI', 'CNTT', 'KHMT', 'lập trình', 'toán', 'CS101'."
        )

    result_lines = [f"📚 Kết quả tìm kiếm cho '{keyword}' ({len(matched)} môn):"]
    result_lines.extend(matched)
    return "\n".join(result_lines)


# =============================================================================
# 🔧 TOOL 2: check_prerequisites
# =============================================================================

def check_prerequisites(course_id: str, completed_courses: str = "") -> str:
    """
    Mô tả: Kiểm tra sinh viên đã đạt đủ điều kiện môn tiên quyết để đăng ký môn học hay chưa.

    Args:
        course_id (str): Mã môn học cần kiểm tra đăng ký (Ví dụ: 'CS301', 'CS201').
        completed_courses (str): Danh sách mã môn đã hoàn thành, phân cách bởi dấu phẩy
                                 (Ví dụ: 'CS101, MATH101, MATH201'). Mặc định rỗng.

    Returns:
        str: Báo cáo kết quả ✅ ĐỦ ĐIỀU KIỆN hoặc ❌ THIẾU MÔN TIÊN QUYẾT.
             Nếu mã môn không tồn tại, trả về chuỗi "LỖI: ...".
    """
    if not course_id or not course_id.strip():
        return "LỖI: Mã môn học không được để trống."

    cid_norm = _normalize_course_id(course_id)

    if cid_norm not in COURSE_DATABASE:
        return (
            f"LỖI: Mã môn học '{course_id}' không tồn tại trong hệ thống. "
            f"Hãy dùng tool search_courses để tra cứu mã môn chính xác."
        )

    required = COURSE_DATABASE[cid_norm]["prerequisites"]

    if not required:
        return f"✅ Môn [{cid_norm}] {COURSE_DATABASE[cid_norm]['name']} không yêu cầu môn tiên quyết. Sinh viên có thể đăng ký ngay!"

    # Chuẩn hóa danh sách môn đã học
    if not completed_courses or not completed_courses.strip():
        done = set()
    else:
        done = {_normalize_course_id(c) for c in completed_courses.split(",") if c.strip()}

    missing = [r for r in required if r not in done]
    course_name = COURSE_DATABASE[cid_norm]["name"]

    if not missing:
        return (
            f"✅ ĐỦ ĐIỀU KIỆN đăng ký [{cid_norm}] {course_name}!\n"
            f"   Các môn tiên quyết đã học: {', '.join(required)}"
        )
    else:
        missing_detail = []
        for m in missing:
            if m in COURSE_DATABASE:
                missing_detail.append(f"{m} ({COURSE_DATABASE[m]['name']})")
            else:
                missing_detail.append(m)
        return (
            f"❌ CHƯA ĐỦ ĐIỀU KIỆN đăng ký [{cid_norm}] {course_name}.\n"
            f"   Môn tiên quyết còn thiếu: {', '.join(missing_detail)}\n"
            f"   Gợi ý: Sinh viên cần học và vượt qua các môn trên trước khi đăng ký môn này."
        )


# =============================================================================
# 🔧 TOOL 3: estimate_workload
# =============================================================================

def estimate_workload(course_ids: str) -> str:
    """
    Mô tả: Ước tính tổng số tín chỉ và đánh giá mức độ nặng/nhẹ của danh sách môn học dự định đăng ký.

    Args:
        course_ids (str): Danh sách mã các môn dự định đăng ký, phân cách bởi dấu phẩy
                          (Ví dụ: 'CS101, MATH101, SE201').

    Returns:
        str: Tổng số tín chỉ, mức độ học tập (🟢 Nhẹ / 🟡 Vừa / 🟠 Nặng / 🔴 Quá tải),
             và lời khuyên điều chỉnh. Trả về "LỖI: ..." nếu dữ liệu rỗng.
    """
    if not course_ids or not course_ids.strip():
        return "LỖI: Vui lòng cung cấp danh sách ít nhất một mã môn học."

    raw_list = [c.strip() for c in course_ids.split(",") if c.strip()]
    if not raw_list:
        return "LỖI: Danh sách môn học không hợp lệ."

    total_credits = 0
    hard_count = 0
    valid_courses = []
    invalid_ids = []

    for raw in raw_list:
        cid = _normalize_course_id(raw)
        if cid not in COURSE_DATABASE:
            invalid_ids.append(raw)
        else:
            info = COURSE_DATABASE[cid]
            total_credits += info["credits"]
            valid_courses.append(f"  • [{cid}] {info['name']} — {info['credits']} TC (Độ khó: {info['difficulty']})")
            if info["difficulty"] == "Khó":
                hard_count += 1

    lines = ["📊 Ước tính khối lượng học tập:"]
    lines.append(f"Danh sách môn hợp lệ ({len(valid_courses)} môn):")
    lines.extend(valid_courses)

    if invalid_ids:
        lines.append(f"\n⚠️ Mã môn không hợp lệ/không thấy: {', '.join(invalid_ids)} (bỏ qua khi tính).")

    lines.append(f"\nTổng số tín chỉ: {total_credits} TC / {MAX_CREDITS_PER_SEMESTER} TC tối đa một học kỳ.")

    # Đánh giá mức độ tải
    if total_credits > MAX_CREDITS_PER_SEMESTER:
        level = "🔴 QUÁ TẢI — Vượt quá giới hạn tín chỉ cho phép!"
        lines.append(f"Mức độ: {level}")
        lines.append(f"💡 Lời khuyên: Sinh viên cần rút bớt ít nhất {total_credits - MAX_CREDITS_PER_SEMESTER} tín chỉ để đúng quy chế.")
    elif total_credits >= 18 or hard_count >= 2:
        level = "🟠 Nặng — Áp lực học tập cao, cần quản lý thời gian tốt."
        lines.append(f"Mức độ: {level}")
    elif total_credits >= 12:
        level = "🟡 Vừa phải — Khối lượng cân bằng, phù hợp số đông sinh viên."
        lines.append(f"Mức độ: {level}")
    else:
        level = "🟢 Nhẹ — Phù hợp học kỳ cải thiện hoặc tập trung môn khó."
        lines.append(f"Mức độ: {level}")

    return "\n".join(lines)


# =============================================================================
# 🔧 TOOL 4: get_course_detail
# =============================================================================

def get_course_detail(course_id: str) -> str:
    """
    Mô tả: Trích xuất thông tin chi tiết đầy đủ của một môn học (tín chỉ, giảng viên, lịch học, mô tả,...).

    Args:
        course_id (str): Mã môn học cần xem chi tiết (Ví dụ: 'CS301', 'MATH101').

    Returns:
        str: Toàn bộ hồ sơ chi tiết môn học. Trả về "LỖI: ..." nếu không tìm thấy môn.
    """
    if not course_id or not course_id.strip():
        return "LỖI: Mã môn học không được để trống."

    cid_norm = _normalize_course_id(course_id)

    if cid_norm not in COURSE_DATABASE:
        return (
            f"LỖI: Không tìm thấy mã môn '{course_id}'. "
            f"Vui lòng kiểm tra lại hoặc dùng search_courses để tìm mã đúng."
        )

    info = COURSE_DATABASE[cid_norm]
    prereq_str = ", ".join(info["prerequisites"]) if info["prerequisites"] else "Không có"

    return (
        f"📖 Chi tiết môn học [{cid_norm}]:\n"
        f"  • Tên môn    : {info['name']}\n"
        f"  • Số tín chỉ : {info['credits']} TC\n"
        f"  • Độ khó     : {info['difficulty']}\n"
        f"  • Tiên quyết : {prereq_str}\n"
        f"  • Lịch học   : {info['schedule']}\n"
        f"  • Giảng viên : {info['instructor']}\n"
        f"  • Dành cho   : Ngành {', '.join(info['majors'])}\n"
        f"  • Mô tả môn  : {info['description']}"
    )


# =============================================================================
# 🔧 TOOL 5: check_schedule_conflict
# =============================================================================

def check_schedule_conflict(course_ids: str) -> str:
    """
    Mô tả: Kiểm tra xem danh sách môn học dự định đăng ký có bị xung đột (trùng) lịch học hay không.

    Args:
        course_ids (str): Danh sách mã môn cần kiểm tra, phân cách bởi dấu phẩy
                          (Ví dụ: 'CS101, MATH101, CS201').

    Returns:
        str: Báo cáo trùng lịch chi tiết hoặc xác nhận không có trùng lịch. Trả về "LỖI: ..." nếu dữ liệu rỗng.
    """
    if not course_ids or not course_ids.strip():
        return "LỖI: Vui lòng cung cấp danh sách ít nhất một mã môn học."

    raw_list = [c.strip() for c in course_ids.split(",") if c.strip()]
    if not raw_list:
        return "LỖI: Danh sách môn học không hợp lệ."

    schedule_map: dict[str, list[str]] = {}
    invalid_ids = []

    for raw in raw_list:
        cid = _normalize_course_id(raw)
        if cid not in COURSE_DATABASE:
            invalid_ids.append(raw)
            continue
        slot = COURSE_DATABASE[cid]["schedule"]
        if slot not in schedule_map:
            schedule_map[slot] = []
        schedule_map[slot].append(cid)

    lines = ["🗓️  Kiểm tra xung đột lịch học:"]

    conflicts = {slot: cids for slot, cids in schedule_map.items() if len(cids) > 1}

    if invalid_ids:
        lines.append(f"⚠️ Mã môn không tìm thấy: {', '.join(invalid_ids)} (bỏ qua).")

    if not conflicts:
        lines.append("✅ Không có xung đột lịch học — Sinh viên có thể đăng ký tất cả các môn trên!")
        for slot, cids in sorted(schedule_map.items()):
            cid = cids[0]
            lines.append(f"   • {slot}: [{cid}] {COURSE_DATABASE[cid]['name']}")
    else:
        lines.append("❌ BÁO ĐỘNG: Phát hiện xung đột lịch học giữa các môn:")
        for slot, cids in conflicts.items():
            names = " & ".join(f"[{c}] {COURSE_DATABASE[c]['name']}" for c in cids)
            lines.append(f"   ⛔ Ka học {slot} -> {names} bị TRÙNG LỊCH!")
        lines.append("💡 Lời khuyên: Sinh viên chọn thay thế 1 trong các môn bị trùng ca trên.")

    return "\n".join(lines)


# =============================================================================
# 📋 REGISTER & TOOL SPECS PROMPT HELPER (Phục vụ Role 3 & Role 4)
# =============================================================================

AVAILABLE_TOOLS = {
    "search_courses": search_courses,
    "check_prerequisites": check_prerequisites,
    "estimate_workload": estimate_workload,
    "get_course_detail": get_course_detail,
    "check_schedule_conflict": check_schedule_conflict,
}


def get_tools_spec_prompt() -> str:
    """
    Tự động sinh chuỗi định nghĩa Tool Specs để Role 3 (Prompt Engineer) dán vào 
    REACT_SYSTEM_PROMPT trong file src/prompts.py.
    """
    specs = ["DANH SÁCH CÁC CÔNG CỤ (TOOLS) KHẢ DỤNG:"]
    for name, func in AVAILABLE_TOOLS.items():
        doc = func.__doc__.strip() if func.__doc__ else "Không có mô tả"
        specs.append(f"\n--- Tool: {name} ---\n{doc}")
    return "\n".join(specs)
