"""
🛠️ TOOL REGISTRY & SCHEMAS — Chủ đề: Trợ Lý Tư Vấn Khóa Học Sinh Viên
Dành cho Role 2: Tool & Spec Engineer

Mốc 3 — Safeguards & Defensive Error Handling:
  - Đảm bảo 100% các hàm tool không bị crash (raise Exception) khi nhận tham số lạ,
    thiếu, rỗng, sai kiểu dữ liệu hoặc bị lỗi cú pháp từ LLM Action string.
  - Tự động làm sạch input (loại bỏ ngoặc vuông [], dấu ngoặc kép '"', khoảng trắng).
  - Trả về chuỗi thông báo lỗi "LỖI: ..." có cấu trúc hướng dẫn LLM khắc phục.

Danh sách 5 Tools:
  1. search_courses          — Tìm khóa học theo từ khóa / ngành học
  2. check_prerequisites     — Kiểm tra điều kiện tiên quyết của môn học
  3. estimate_workload       — Ước tính tổng tín chỉ & mức độ nặng (Guardrail >24 TC)
  4. get_course_detail       — Xem chi tiết một môn học (mô tả, giảng viên, lịch)
  5. check_schedule_conflict — Kiểm tra xung đột lịch học giữa các môn
"""

import re
from typing import Any

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

# Quy định tối đa tín chỉ mỗi học kỳ (Guardrail)
MAX_CREDITS_PER_SEMESTER = 24


# =============================================================================
# 🛡️ HELPER: Bọc lót & làm sạch dữ liệu đầu vào (Defensive Input Cleaner)
# =============================================================================

def _clean_input_string(val: Any) -> str:
    """Loại bỏ ký tự dư thừa như ngoặc vuông, ngoặc đơn, ngoặc kép do LLM sinh ra."""
    if val is None:
        return ""
    s = str(val).strip()
    # Loại bỏ ngoặc bao quanh nếu LLM truyền dạng ['CS101'] hoặc "CS101"
    s = re.sub(r"^[\[\(\'\"]+|[\]\)\'\"]+$", "", s).strip()
    return s


# =============================================================================
# 🔧 TOOL 1: search_courses
# =============================================================================

def search_courses(keyword: str) -> str:
    """
    Tìm kiếm các khóa học phù hợp theo từ khóa hoặc ngành học.

    Args:
        keyword (str): Từ khóa tìm kiếm — có thể là tên môn, mã môn,
                       tên ngành (Ví dụ: 'AI', 'lập trình', 'CNTT', 'CS101')

    Returns:
        str: Danh sách các môn học phù hợp (mã, tên, tín chỉ, độ khó).
             Trả về chuỗi "LỖI: ..." nếu không tìm thấy kết quả hoặc tham số rỗng.
    """
    try:
        kw = _clean_input_string(keyword).lower()

        if not kw:
            return "LỖI: Từ khóa tìm kiếm không được để trống. Hãy truyền từ khóa như 'AI', 'CNTT', 'CS101'."

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
                f"Gợi ý các từ khóa hợp lệ: 'AI', 'CNTT', 'toán', 'lập trình', 'CS101'."
            )

        result_lines = [f"📚 Kết quả tìm kiếm cho '{keyword}' ({len(matched)} môn):"]
        result_lines.extend(matched)
        return "\n".join(result_lines)

    except Exception as e:
        return f"LỖI HỆ THỐNG khi xử lý search_courses('{keyword}'): {str(e)}"


# =============================================================================
# 🔧 TOOL 2: check_prerequisites
# =============================================================================

def check_prerequisites(course_id: str, completed_courses: str = "") -> str:
    """
    Kiểm tra sinh viên có đủ điều kiện tiên quyết để đăng ký môn học không.

    Args:
        course_id (str): Mã môn học cần kiểm tra (Ví dụ: 'CS301', 'MATH201').
        completed_courses (str): Danh sách mã môn đã học, cách nhau bởi dấu phẩy
                                 (Ví dụ: 'CS101,MATH101,CS201'). Mặc định là chuỗi rỗng.

    Returns:
        str: Kết quả kiểm tra — ĐỦ điều kiện hoặc THIẾU môn tiên quyết nào.
             Trả về chuỗi "LỖI: ..." nếu mã môn không hợp lệ.
    """
    try:
        cid = _clean_input_string(course_id).upper()

        if not cid:
            return "LỖI: Mã môn học không được để trống. Hãy truyền mã môn hợp lệ (Ví dụ: 'CS301')."

        if cid not in COURSE_DATABASE:
            valid_codes = ", ".join(sorted(COURSE_DATABASE.keys()))
            return (
                f"LỖI: Mã môn học '{course_id}' không tồn tại trong hệ thống. "
                f"Danh sách mã môn có sẵn: {valid_codes}."
            )

        required = COURSE_DATABASE[cid]["prerequisites"]

        if not required:
            return f"✅ Môn [{cid}] {COURSE_DATABASE[cid]['name']} không yêu cầu môn tiên quyết — Có thể đăng ký ngay!"

        # Chuẩn hóa danh sách môn đã học
        raw_completed = _clean_input_string(completed_courses)
        if not raw_completed:
            done = set()
        else:
            done = {
                _clean_input_string(c).upper()
                for c in raw_completed.split(",")
                if _clean_input_string(c)
            }

        missing = [r for r in required if r not in done]
        course_name = COURSE_DATABASE[cid]["name"]

        if not missing:
            return (
                f"✅ Đủ điều kiện đăng ký [{cid}] {course_name}!\n"
                f"   Môn tiên quyết đã hoàn thành: {', '.join(required)}"
            )
        else:
            missing_detail = [
                f"{m} ({COURSE_DATABASE[m]['name']})" if m in COURSE_DATABASE else m
                for m in missing
            ]
            return (
                f"❌ Chưa đủ điều kiện đăng ký [{cid}] {course_name}.\n"
                f"   Thiếu môn tiên quyết: {', '.join(missing_detail)}\n"
                f"   Gợi ý: Hãy hoàn thành các môn tiên quyết trên trước."
            )

    except Exception as e:
        return f"LỖI HỆ THỐNG khi xử lý check_prerequisites('{course_id}', '{completed_courses}'): {str(e)}"


# =============================================================================
# 🔧 TOOL 3: estimate_workload
# =============================================================================

def estimate_workload(course_ids: str) -> str:
    """
    Ước tính tổng số tín chỉ và mức độ nặng khi đăng ký một nhóm môn học.

    Args:
        course_ids (str): Danh sách mã môn muốn đăng ký, cách nhau bởi dấu phẩy
                          (Ví dụ: 'CS101,MATH101,SE201').

    Returns:
        str: Tổng tín chỉ, đánh giá mức độ (Nhẹ / Vừa / Nặng / Quá tải),
             và cảnh báo nếu vượt giới hạn 24 tín chỉ.
    """
    try:
        raw = _clean_input_string(course_ids)

        if not raw:
            return "LỖI: Vui lòng cung cấp ít nhất một mã môn học (Ví dụ: 'CS101,MATH101')."

        ids = [
            _clean_input_string(c).upper()
            for c in raw.split(",")
            if _clean_input_string(c)
        ]

        if not ids:
            return "LỖI: Danh sách môn học không hợp lệ."

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
                valid_courses.append(
                    f"  • [{cid}] {info['name']} — {info['credits']} TC, Độ khó: {info['difficulty']}"
                )
                if info["difficulty"] == "Khó":
                    hard_count += 1

        lines = ["📊 Ước tính khối lượng học tập:"]
        lines.append(f"Các môn đăng ký ({len(valid_courses)} môn):")
        lines.extend(valid_courses)

        if invalid_ids:
            lines.append(f"\n⚠️  Mã môn không tìm thấy: {', '.join(invalid_ids)} (bỏ qua khi tính).")

        lines.append(f"\nTổng tín chỉ: {total_credits} / {MAX_CREDITS_PER_SEMESTER} TC tối đa.")

        # Phanh Guardrail cảnh báo tải học tập
        if total_credits > MAX_CREDITS_PER_SEMESTER:
            level = "🔴 QUÁ TẢI — Vượt giới hạn tín chỉ cho phép cho 1 học kỳ!"
            lines.append(f"Mức độ: {level}")
            lines.append(
                f"🛡️ GUARDRAIL PHANH AN TOÀN: Bắt buộc giảm bớt tối thiểu {total_credits - MAX_CREDITS_PER_SEMESTER} TC để không vượt quy định."
            )
        elif total_credits >= 18 or hard_count >= 2:
            level = "🟠 Nặng — Khối lượng lớn, cần tập trung cao độ."
            lines.append(f"Mức độ: {level}")
        elif total_credits >= 12:
            level = "🟡 Vừa phải — Cân bằng tốt giữa các môn."
            lines.append(f"Mức độ: {level}")
        else:
            level = "🟢 Nhẹ — Khối lượng học tập thoải mái."
            lines.append(f"Mức độ: {level}")

        return "\n".join(lines)

    except Exception as e:
        return f"LỖI HỆ THỐNG khi xử lý estimate_workload('{course_ids}'): {str(e)}"


# =============================================================================
# 🔧 TOOL 4: get_course_detail
# =============================================================================

def get_course_detail(course_id: str) -> str:
    """
    Lấy thông tin chi tiết đầy đủ của một môn học cụ thể.

    Args:
        course_id (str): Mã môn học (Ví dụ: 'CS201', 'MATH101').

    Returns:
        str: Thông tin đầy đủ: tên, mã, tín chỉ, tiên quyết, lịch học, giảng viên, mô tả.
    """
    try:
        cid = _clean_input_string(course_id).upper()

        if not cid:
            return "LỖI: Mã môn học không được để trống. Hãy truyền mã môn như 'CS201'."

        if cid not in COURSE_DATABASE:
            valid_codes = ", ".join(sorted(COURSE_DATABASE.keys()))
            return (
                f"LỖI: Mã môn học '{course_id}' không tồn tại. "
                f"Các mã môn có sẵn: {valid_codes}."
            )

        info = COURSE_DATABASE[cid]
        prereq_str = (
            ", ".join(info["prerequisites"]) if info["prerequisites"] else "Không có"
        )

        return (
            f"📖 Chi tiết môn học:\n"
            f"  Mã môn   : {cid}\n"
            f"  Tên môn  : {info['name']}\n"
            f"  Tín chỉ  : {info['credits']} TC\n"
            f"  Độ khó   : {info['difficulty']}\n"
            f"  Tiên quyết: {prereq_str}\n"
            f"  Lịch học : {info['schedule']}\n"
            f"  Giảng viên: {info['instructor']}\n"
            f"  Ngành    : {', '.join(info['majors'])}\n"
            f"  Mô tả    : {info['description']}"
        )

    except Exception as e:
        return f"LỖI HỆ THỐNG khi xử lý get_course_detail('{course_id}'): {str(e)}"


# =============================================================================
# 🔧 TOOL 5: check_schedule_conflict
# =============================================================================

def check_schedule_conflict(course_ids: str) -> str:
    """
    Kiểm tra xem các môn học đăng ký có bị trùng lịch học với nhau không.

    Args:
        course_ids (str): Danh sách mã môn muốn kiểm tra, cách nhau bởi dấu phẩy
                          (Ví dụ: 'CS101,MATH101,CS201').

    Returns:
        str: Báo cáo xung đột lịch học (nếu có), hoặc xác nhận lịch hợp lệ.
    """
    try:
        raw = _clean_input_string(course_ids)

        if not raw:
            return "LỖI: Vui lòng cung cấp danh sách mã môn học (Ví dụ: 'CS101,MATH101')."

        ids = [
            _clean_input_string(c).upper()
            for c in raw.split(",")
            if _clean_input_string(c)
        ]

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

        lines = ["🗓️  Kiểm tra xung đột lịch học:"]

        conflicts = {slot: cids for slot, cids in schedule_map.items() if len(cids) > 1}

        if invalid_ids:
            lines.append(f"⚠️  Mã môn không tìm thấy: {', '.join(invalid_ids)} (bỏ qua).")

        if not conflicts:
            lines.append("✅ Không có xung đột lịch học — Thời khóa biểu hoàn toàn hợp lệ!")
            for slot, cids in sorted(schedule_map.items()):
                cid = cids[0]
                lines.append(f"   {slot}: [{cid}] {COURSE_DATABASE[cid]['name']}")
        else:
            lines.append("❌ Phát hiện xung đột lịch học:")
            for slot, cids in conflicts.items():
                names = " & ".join(
                    f"[{c}] {COURSE_DATABASE[c]['name']}" for c in cids
                )
                lines.append(f"   ⛔ {slot} → {names} bị TRÙNG lịch!")
            lines.append("💡 Gợi ý: Hãy thay đổi môn học để tránh bị trùng giờ lên lớp.")

        return "\n".join(lines)

    except Exception as e:
        return f"LỖI HỆ THỐNG khi xử lý check_schedule_conflict('{course_ids}'): {str(e)}"

# =============================================================================
# 🔧 TOOL 6: evaluate_gpa
# =============================================================================
def evaluate_gpa(gpa_str: str) -> str:
    """
    Xếp loại học lực dựa trên điểm GPA hệ 4.0.
    """
    try:
        gpa = float(_clean_input_string(gpa_str))
        if gpa < 0 or gpa > 4.0:
            return "LỖI: GPA phải nằm trong khoảng từ 0.0 đến 4.0."
        
        if gpa >= 3.6:
            rank = "Xuất sắc"
        elif gpa >= 3.2:
            rank = "Giỏi"
        elif gpa >= 2.5:
            rank = "Khá"
        elif gpa >= 2.0:
            rank = "Trung bình"
        else:
            rank = "Yếu/Kém"
            
        return f"✅ Với GPA {gpa}/4.0, quy chế xếp loại học lực là: {rank}"
    except ValueError:
        return f"LỖI: '{gpa_str}' không phải là một số hợp lệ. Hãy truyền vào số (ví dụ: '3.65')."
    except Exception as e:
        return f"LỖI HỆ THỐNG khi xử lý evaluate_gpa('{gpa_str}'): {str(e)}"


# =============================================================================
# 📋 ĐĂNG KÝ TOOL — Agent sẽ tra bảng này để gọi tool
# =============================================================================

AVAILABLE_TOOLS = {
    "search_courses": search_courses,
    "check_prerequisites": check_prerequisites,
    "estimate_workload": estimate_workload,
    "get_course_detail": get_course_detail,
    "check_schedule_conflict": check_schedule_conflict,
    "evaluate_gpa": evaluate_gpa,
}
