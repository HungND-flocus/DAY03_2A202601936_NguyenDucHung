"""
🛠️ TOOL REGISTRY & SCHEMAS — Chủ đề: Trợ Lý Tư Vấn Khóa Học Sinh Viên
Dành cho Role 2: Tool & Spec Engineer

Mốc 2 — Bổ sung Tool Specs, Docstrings chuẩn hóa cho ReAct Agent & khớp với Test Cases (Role 1):
  1. search_courses          — Tìm khóa học theo từ khóa / ngành / định hướng (VD: 'Data Science', 'AI')
  2. check_prerequisites     — Kiểm tra điều kiện tiên quyết của môn học
  3. estimate_workload       — Ước tính tổng tín chỉ & mức độ nặng cho danh sách môn
  4. get_course_detail       — Xem chi tiết một môn học (mô tả, giảng viên, lịch)
  5. check_schedule_conflict — Kiểm tra xung đột lịch học giữa các môn

Quy tắc phanh an toàn (Guardrails / Error Handling):
  - Khi tham số không hợp lệ, môn không tồn tại, hoặc dữ liệu rỗng:
    Trả về string dạng "LỖI: ..." thay vì làm crash app Python (raise Exception).
"""

# =============================================================================
# 📚 DỮ LIỆU MẪU (Mock Data) — Khớp với Test Cases trong config/test_cases.json
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
        "majors": ["CNTT", "KHMT", "AI", "Data Science"],
    },
    "CS201": {
        "name": "Cấu trúc Dữ liệu & Giải thuật",
        "credits": 4,
        "difficulty": "Trung bình",
        "prerequisites": ["CS101"],
        "schedule": "Thứ 3 (9:30 - 11:30)",
        "instructor": "PGS. Trần Thị Bình",
        "description": "Stack, Queue, Tree, Graph và các thuật toán sắp xếp, tìm kiếm.",
        "majors": ["CNTT", "KHMT", "AI", "Data Science"],
    },
    "CS301": {
        "name": "Trí tuệ Nhân tạo Cơ bản",
        "credits": 3,
        "difficulty": "Khó",
        "prerequisites": ["CS201", "MATH201"],
        "schedule": "Thứ 4 (13:30 - 15:30)",
        "instructor": "GS. Lê Quốc Cường",
        "description": "Các thuật toán AI cổ điển, biểu diễn tri thức và tìm kiếm không gian trạng thái.",
        "majors": ["AI", "CNTT"],
    },
    "AI301": {
        "name": "Trí tuệ Nhân tạo Ứng dụng",
        "credits": 3,
        "difficulty": "Khó",
        "prerequisites": ["CS201", "MATH201"],
        "schedule": "Thứ 5 (9:30 - 11:30)",
        "instructor": "GS. Lê Quốc Cường",
        "description": "Môn nâng cao về AI, bao gồm các ứng dụng Học máy và Xử lý ngôn ngữ tự nhiên.",
        "majors": ["AI", "CNTT", "Data Science"],
    },
    "CS302": {
        "name": "Học Máy (Machine Learning)",
        "credits": 4,
        "difficulty": "Khó",
        "prerequisites": ["CS301", "MATH202"],
        "schedule": "Thứ 5 (7:30 - 9:30)",
        "instructor": "TS. Phạm Minh Đức",
        "description": "Supervised, Unsupervised Learning, Neural Networks.",
        "majors": ["AI", "Data Science"],
    },
    "DS201": {
        "name": "Khai phá Dữ liệu & Data Science",
        "credits": 3,
        "difficulty": "Trung bình",
        "prerequisites": ["CS101", "DB201"],
        "schedule": "Thứ 4 (13:30 - 15:30)",
        "instructor": "TS. Nguyễn Thị Thu",
        "description": "Các kỹ thuật Khoa học Dữ liệu, Data Mining, xử lý dữ liệu lớn với Python Pandas, Scikit-Learn.",
        "majors": ["Data Science", "CNTT", "AI"],
    },
    "MATH101": {
        "name": "Giải tích 1",
        "credits": 4,
        "difficulty": "Trung bình",
        "prerequisites": [],
        "schedule": "Thứ 2 (13:30 - 15:30)",
        "instructor": "TS. Hoàng Thị Lan",
        "description": "Giới hạn, đạo hàm, tích phân và ứng dụng.",
        "majors": ["CNTT", "KHMT", "AI", "KT", "Data Science"],
    },
    "MATH201": {
        "name": "Đại số Tuyến tính",
        "credits": 3,
        "difficulty": "Trung bình",
        "prerequisites": ["MATH101"],
        "schedule": "Thứ 6 (9:30 - 11:30)",
        "instructor": "PGS. Vũ Thanh Hà",
        "description": "Ma trận, không gian vector, trị riêng, vector riêng.",
        "majors": ["CNTT", "KHMT", "AI", "Data Science"],
    },
    "MATH202": {
        "name": "Xác suất & Thống kê",
        "credits": 3,
        "difficulty": "Trung bình",
        "prerequisites": ["MATH101"],
        "schedule": "Thứ 3 (13:30 - 15:30)",
        "instructor": "TS. Ngô Thị Mai",
        "description": "Lý thuyết xác suất, phân phối xác suất, kiểm định thống kê.",
        "majors": ["AI", "CNTT", "KT", "Data Science"],
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
        "majors": ["CNTT", "KHMT", "AI", "Data Science"],
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
# 🔧 TOOL 1: search_courses
# =============================================================================

def search_courses(keyword: str) -> str:
    """
    Tra cứu danh sách các khóa học phù hợp theo từ khóa, ngành học hoặc định hướng nghề nghiệp.

    Mục đích cho Agent:
        Dùng tool này để tìm các môn học thuộc một lĩnh vực (VD: 'Data Science', 'AI', 'Lập trình')
        hoặc tìm mã môn chính xác dựa trên tên môn học mà sinh viên nhắc tới.

    Args:
        keyword (str): Từ khóa tìm kiếm — có thể là tên môn, mã môn, ngành học, 
                       hoặc định hướng nghề nghiệp (Ví dụ: 'Data Science', 'AI', 'CNTT', 'CS101', 'Toán').

    Returns:
        str: Chuỗi kết quả liệt kê các môn học khớp với từ khóa (mã môn, tên môn, tín chỉ, độ khó, ngành).
             Nếu không tìm thấy hoặc input rỗng, trả về chuỗi thông báo "LỖI: ...".

    Ví dụ ReAct Call:
        Action: search_courses[Data Science]
        Action: search_courses[CS101]
    """
    if not keyword or not str(keyword).strip():
        return "LỖI: Từ khóa tìm kiếm không được để trống. Hãy cung cấp từ khóa như ngành học (CNTT, AI, Data Science) hoặc tên/mã môn."

    kw = str(keyword).lower().strip()
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
                f"Độ khó: {info['difficulty']}, Ngành: {', '.join(info['majors'])}\n"
                f"    Mô tả: {info['description']}"
            )

    if not matched:
        return (
            f"LỖI: Không tìm thấy môn học nào khớp với từ khóa '{keyword}'. "
            f"Gợi ý: Hãy thử các từ khóa phổ biến như 'CNTT', 'AI', 'Data Science', 'Lập trình', 'Toán', 'CS101'."
        )

    result_lines = [f"📚 Kết quả tìm kiếm khóa học cho từ khóa '{keyword}' ({len(matched)} môn phù hợp):"]
    result_lines.extend(matched)
    return "\n".join(result_lines)


# =============================================================================
# 🔧 TOOL 2: check_prerequisites
# =============================================================================

def check_prerequisites(course_id: str, completed_courses: str = "") -> str:
    """
    Kiểm tra điều kiện tiên quyết xem sinh viên đã đủ điều kiện đăng ký học phần hay chưa.

    Mục đích cho Agent:
        Dùng tool này trước khi gợi ý đăng ký một môn học để đảm bảo sinh viên không bị thiếu môn tiên quyết.

    Args:
        course_id (str): Mã môn học sinh viên muốn đăng ký (Ví dụ: 'CS201', 'CS301', 'DS201').
        completed_courses (str): Danh sách mã các môn sinh viên đã học xong, phân cách bởi dấu phẩy
                                 (Ví dụ: 'CS101,MATH101' hoặc '' nếu chưa học môn nào).

    Returns:
        str: Kết quả xác nhận ĐỦ điều kiện đăng ký hoặc liệt kê cụ thể các môn tiên quyết còn THIẾU.
             Trả về chuỗi "LỖI: ..." nếu mã môn không tồn tại trong hệ thống.

    Ví dụ ReAct Call:
        Action: check_prerequisites[CS201, CS101]
        Action: check_prerequisites[CS301, CS101,MATH101]
    """
    if not course_id or not str(course_id).strip():
        return "LỖI: Tham số course_id không được để trống. Hãy truyền mã môn học cần kiểm tra."

    course_id = str(course_id).strip().upper()

    if course_id not in COURSE_DATABASE:
        return (
            f"LỖI: Mã môn học '{course_id}' không tồn tại trong hệ thống. "
            f"Vui lòng sử dụng tool search_courses để tra cứu mã môn chính xác."
        )

    required = COURSE_DATABASE[course_id]["prerequisites"]

    if not required:
        return f"✅ Môn [{course_id}] {COURSE_DATABASE[course_id]['name']} KHÔNG có môn tiên quyết — Sinh viên có thể đăng ký ngay!"

    # Chuẩn hóa danh sách môn đã hoàn thành
    if not completed_courses or not str(completed_courses).strip():
        done = set()
    else:
        done = {c.strip().upper() for c in str(completed_courses).split(",") if c.strip()}

    missing = [r for r in required if r not in done]
    course_name = COURSE_DATABASE[course_id]["name"]

    if not missing:
        return (
            f"✅ ĐỦ ĐIỀU KIỆN! Sinh viên có thể đăng ký môn [{course_id}] {course_name}.\n"
            f"   Môn tiên quyết đã hoàn thành: {', '.join(required)}"
        )
    else:
        missing_detail = []
        for m in missing:
            if m in COURSE_DATABASE:
                missing_detail.append(f"{m} ({COURSE_DATABASE[m]['name']})")
            else:
                missing_detail.append(m)
        return (
            f"❌ CHƯA ĐỦ ĐIỀU KIỆN đăng ký môn [{course_id}] {course_name}.\n"
            f"   Các môn tiên quyết còn THIẾU: {', '.join(missing_detail)}\n"
            f"   Gợi ý: Sinh viên cần đăng ký và hoàn thành các môn thiếu trên trước."
        )


# =============================================================================
# 🔧 TOOL 3: estimate_workload
# =============================================================================

def estimate_workload(course_ids: str) -> str:
    """
    Ước tính tổng số tín chỉ, kiểm tra giới hạn tín chỉ và phân tích mức độ học tập cho danh sách môn dự định đăng ký.

    Mục đích cho Agent:
        Dùng tool này để đảm bảo kế hoạch học tập không bị quá tải hoặc vượt số tín chỉ tối đa sinh viên yêu cầu.

    Args:
        course_ids (str): Danh sách mã các môn học định đăng ký, phân cách bằng dấu phẩy
                          (Ví dụ: 'CS101,MATH101,SE201' hoặc 'CS201,DS201,AI301').

    Returns:
        str: Bảng phân tích khối lượng: Tổng tín chỉ, danh sách môn, độ khó, mức độ tải 
             (🟢 Nhẹ / 🟡 Vừa / 🟠 Nặng / 🔴 Quá tải) và cảnh báo vượt giới hạn.
             Trả về "LỖI: ..." nếu tham số rỗng hoặc không có môn hợp lệ.

    Ví dụ ReAct Call:
        Action: estimate_workload[CS201,DS201,AI301]
    """
    if not course_ids or not str(course_ids).strip():
        return "LỖI: Tham số course_ids không được để trống. Hãy cung cấp ít nhất một mã môn học."

    ids = [c.strip().upper() for c in str(course_ids).split(",") if c.strip()]

    if not ids:
        return "LỖI: Danh sách mã môn học không hợp lệ."

    total_credits = 0
    hard_count = 0
    valid_courses = []
    invalid_ids = []

    for cid in ids:
        if cid not in COURSE_DATABASE:
            invalid_ids.append(cid)
        else:
            info = COURSE_DATABASE[cid]
            total_credits += info["credits"]
            valid_courses.append(f"  • [{cid}] {info['name']} — {info['credits']} tín chỉ (Độ khó: {info['difficulty']})")
            if info["difficulty"] == "Khó":
                hard_count += 1

    lines = ["📊 ĐÁNH GIÁ KHỐI LƯỢNG HỌC TẬP (WORKLOAD ESTIMATION):"]
    lines.append(f"Các môn lựa chọn ({len(valid_courses)} môn):")
    lines.extend(valid_courses)

    if invalid_ids:
        lines.append(f"\n⚠️  Cảnh báo: Mã môn không tồn tại trong hệ thống: {', '.join(invalid_ids)} (bỏ qua khi tính tín chỉ).")

    lines.append(f"\nTổng số tín chỉ: {total_credits} TC (Tối đa quy định: {MAX_CREDITS_PER_SEMESTER} TC).")

    # Đánh giá phân mức
    if total_credits > MAX_CREDITS_PER_SEMESTER:
        level = "🔴 QUÁ TẢI — Vượt quá giới hạn tín chỉ cho phép của học kỳ!"
        lines.append(f"Mức độ: {level}")
        lines.append(f"💡 Đề xuất: Cần loại bỏ ít nhất {total_credits - MAX_CREDITS_PER_SEMESTER} tín chỉ để tuân thủ quy chế.")
    elif total_credits >= 18 or hard_count >= 2:
        level = "🟠 NẶNG — Khối lượng học tập cao (nhiều môn khó/nhiều tín chỉ)."
        lines.append(f"Mức độ: {level}")
        lines.append("💡 Đề xuất: Sinh viên cần phân bổ thời gian học hợp lý.")
    elif total_credits >= 12:
        level = "🟡 VỪA PHẢI — Cân bằng tốt giữa việc học và các hoạt động khác."
        lines.append(f"Mức độ: {level}")
    else:
        level = "🟢 NHẸ — Khối lượng vừa sức, dễ đạt kết quả cao."
        lines.append(f"Mức độ: {level}")

    return "\n".join(lines)


# =============================================================================
# 🔧 TOOL 4: get_course_detail
# =============================================================================

def get_course_detail(course_id: str) -> str:
    """
    Truy xuất toàn bộ thông tin chi tiết của một mã môn học cụ thể.

    Mục đích cho Agent:
        Dùng tool này khi sinh viên hỏi sâu về một môn học cụ thể (mô tả môn, giảng viên dạy, lịch học, độ khó).

    Args:
        course_id (str): Mã môn học cần xem thông tin (Ví dụ: 'CS201', 'MATH101', 'DS201').

    Returns:
        str: Thông tin đầy đủ gồm Tên, Mã, Tín chỉ, Độ khó, Tiên quyết, Lịch học, Giảng viên, Ngành học & Mô tả.
             Trả về "LỖI: ..." nếu mã môn không tồn tại.

    Ví dụ ReAct Call:
        Action: get_course_detail[CS201]
    """
    if not course_id or not str(course_id).strip():
        return "LỖI: Tham số course_id không được để trống. Hãy truyền mã môn học cần xem chi tiết."

    course_id = str(course_id).strip().upper()

    if course_id not in COURSE_DATABASE:
        return (
            f"LỖI: Mã môn học '{course_id}' không tồn tại. "
            f"Vui lòng dùng tool search_courses để tra cứu mã môn chính xác."
        )

    info = COURSE_DATABASE[course_id]
    prereq_str = (
        ", ".join(info["prerequisites"]) if info["prerequisites"] else "Không có"
    )

    return (
        f"📖 THÔNG TIN CHI TIẾT MÔN HỌC:\n"
        f"  • Mã môn học : {course_id}\n"
        f"  • Tên môn học: {info['name']}\n"
        f"  • Số tín chỉ : {info['credits']} TC\n"
        f"  • Mức độ khó : {info['difficulty']}\n"
        f"  • Tiên quyết : {prereq_str}\n"
        f"  • Lịch học   : {info['schedule']}\n"
        f"  • Giảng viên : {info['instructor']}\n"
        f"  • Dành cho   : {', '.join(info['majors'])}\n"
        f"  • Mô tả môn  : {info['description']}"
    )


# =============================================================================
# 🔧 TOOL 5: check_schedule_conflict
# =============================================================================

def check_schedule_conflict(course_ids: str) -> str:
    """
    Kiểm tra xem các môn học sinh viên có ý định chọn có bị xung đột (trùng) lịch học với nhau hay không.

    Mục đích cho Agent:
        Dùng tool này để đảm bảo các môn trong kế hoạch đăng ký học tập không bị trùng giờ học.

    Args:
        course_ids (str): Danh sách mã các môn học phân cách bằng dấu phẩy
                          (Ví dụ: 'CS101,MATH101,CS201').

    Returns:
        str: Báo cáo kiểm tra lịch học — Xác nhận hợp lệ hoặc chỉ rõ ca học bị trùng kèm mã các môn trùng.
             Trả về "LỖI: ..." nếu tham số rỗng hoặc không hợp lệ.

    Ví dụ ReAct Call:
        Action: check_schedule_conflict[CS101, MATH101]
    """
    if not course_ids or not str(course_ids).strip():
        return "LỖI: Tham số course_ids không được để trống. Hãy truyền danh sách mã môn học."

    ids = [c.strip().upper() for c in str(course_ids).split(",") if c.strip()]

    if not ids:
        return "LỖI: Danh sách môn học trống hoặc không hợp lệ."

    schedule_map: dict[str, list[str]] = {}
    invalid_ids = []

    for cid in ids:
        if cid not in COURSE_DATABASE:
            invalid_ids.append(cid)
            continue
        slot = COURSE_DATABASE[cid]["schedule"]
        if slot not in schedule_map:
            schedule_map[slot] = []
        schedule_map[slot].append(cid)

    lines = ["🗓️  BÁO CÁO KIỂM TRA XUNG ĐỘT LỊCH HỌC:"]

    conflicts = {slot: cids for slot, cids in schedule_map.items() if len(cids) > 1}

    if invalid_ids:
        lines.append(f"⚠️  Mã môn không tồn tại trong hệ thống: {', '.join(invalid_ids)} (bỏ qua kiểm tra).")

    if not conflicts:
        lines.append("✅ HỢP LỆ! Không có bất kỳ xung đột lịch học nào giữa các môn đã chọn.")
        lines.append("Chi tiết thời khóa biểu:")
        for slot, cids in sorted(schedule_map.items()):
            cid = cids[0]
            lines.append(f"   • {slot}: [{cid}] {COURSE_DATABASE[cid]['name']}")
    else:
        lines.append("❌ PHÁT HIỆN XUNG ĐỘT LỊCH HỌC!")
        for slot, cids in conflicts.items():
            names = " & ".join(
                f"[{c}] {COURSE_DATABASE[c]['name']}" for c in cids
            )
            lines.append(f"   ⛔ Khung giờ {slot} → Môn {names} bị TRÙNG LỊCH!")
        lines.append("💡 Đề xuất: Sinh viên cần chọn lớp/môn khác để tránh trùng lịch học.")

    return "\n".join(lines)


# =============================================================================
# 📋 ĐĂNG KÝ TOOL REGISTRY — ReAct Agent sẽ tra bảng này để gọi hàm
# =============================================================================

AVAILABLE_TOOLS = {
    "search_courses": search_courses,
    "check_prerequisites": check_prerequisites,
    "estimate_workload": estimate_workload,
    "get_course_detail": get_course_detail,
    "check_schedule_conflict": check_schedule_conflict,
}
