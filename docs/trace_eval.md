# Báo Cáo Trace & Agentic Fit

Dự án: **AI Academic Advisor - Trợ lý tư vấn khóa học sinh viên**

## 1. Mô Tả Bài Toán

Đầu mỗi học kỳ, sinh viên phải chọn môn từ danh sách lớn và chịu nhiều ràng buộc: môn tiên quyết, tín chỉ tối đa/tối thiểu, mục tiêu tốt nghiệp, môn còn nợ và định hướng nghề nghiệp. Nếu chọn sai, sinh viên có thể trễ tiến độ hoặc lập kế hoạch không khả thi.

Giải pháp trong lab: ReAct Agent đóng vai trò lớp hội thoại, nhưng mọi quyết định học vụ đều đi qua tool/backend giả lập. Agent chỉ giải thích, hỏi lại, cảnh báo và gọi tool; không tự bịa mã môn hay điều kiện tốt nghiệp.

## 2. Scoring Matrix - Agentic Fit

| Tiêu chí | Điểm | Lý do |
| :--- | :---: | :--- |
| Multi-step Reasoning | `5/5` | Cần kết hợp hồ sơ sinh viên, môn đã học, môn còn thiếu, tiên quyết, tín chỉ và mục tiêu. |
| Tool Interaction | `5/5` | Phải gọi tool để tra cứu môn, kiểm tra tiên quyết, tính workload, sinh kế hoạch và duyệt kế hoạch. |
| Dynamic Decision | `5/5` | Kết quả tool quyết định bước tiếp theo: xếp môn, cảnh báo, hỏi lại, gửi duyệt hoặc từ chối. |
| Long Horizon | `4/5` | Có kế hoạch nhiều học kỳ, nhưng bản lab chỉ mô phỏng vài học kỳ mẫu. |
| Tổng | **19/20** | **Rất phù hợp dùng ReAct Agent có guardrails.** |

## 3. Bộ Test Cases

| ID | Nhóm case | Tool kỳ vọng |
| :---: | :--- | :--- |
| 1 | Hỏi kiến thức nền tảng AI | Không cần tool |
| 2 | Sinh kế hoạch cho S001 theo Data Science, tối đa 9 tín chỉ | `generate_study_plan` |
| 3 | Sinh viên S002 nợ môn, cần bắt kịp tiến độ | `generate_study_plan` |
| 4 | Sinh viên S003 năm cuối, muốn tốt nghiệp đúng hạn | `generate_study_plan` |
| 5 | What-if tăng giới hạn lên 12 tín chỉ/kỳ | `simulate_what_if` |
| 6 | Tính workload danh sách môn | `estimate_workload` |
| 7 | Câu hỏi thiếu thông tin | Không cần tool, phải hỏi lại |
| 8 | Môn không tồn tại `MAGIC999` | `search_courses` |
| 9 | Sinh viên gửi kế hoạch cho cố vấn | `submit_plan` |
| 10 | Cố vấn duyệt kế hoạch | `review_plan` |

## 4. Trace Mẫu

### Case #2 - Sinh Kế Hoạch

User: Sinh viên S001 muốn kế hoạch Data Science cân bằng, tối đa 9 tín chỉ.

```text
Thought: Cần sinh kế hoạch bằng planner đã kiểm tra tiên quyết và giới hạn tín chỉ.
Action: generate_study_plan["S001", "balanced", "Data Science", "9"]
Observation: plan_id=PLAN-S001-001, status=draft, terms=[...], alerts=[...]
Thought: Planner đã trả về kế hoạch đã kiểm tra tiên quyết và tín chỉ.
Final Answer: Kế hoạch đề xuất đang ở trạng thái draft. Sinh viên cần gửi kế hoạch cho cố vấn trước khi áp dụng.
```

### Case #8 - Guardrail Môn Không Tồn Tại

```text
Thought: Cần kiểm tra môn MAGIC999 có trong danh mục học vụ không.
Action: search_courses["MAGIC999"]
Observation: LOI: Khong tim thay mon hoc phu hop voi 'MAGIC999'.
Thought: Tool trả về lỗi nên không được bịa kết quả.
Final Answer: Không thể thêm MAGIC999 vì môn này không tồn tại trong danh mục học vụ.
```

### Case #9-10 - Human Approval

```text
Thought: Cần chuyển kế hoạch nháp sang trạng thái chờ cố vấn duyệt.
Action: submit_plan["PLAN-S001-001", "S001"]
Observation: status=pending_approval

Thought: Cần kiểm tra quyền cố vấn và duyệt kế hoạch đang chờ.
Action: review_plan["PLAN-S001-001", "ADV01", "approve"]
Observation: status=approved
Final Answer: Kế hoạch đã được cố vấn duyệt.
```

## 5. Baseline Vs ReAct Agent

| Tiêu chí | Baseline Chatbot | ReAct Agent |
| :--- | :--- | :--- |
| Kiến thức chung | Trả lời được | Trả lời được |
| Kiểm tra tiên quyết | Không có dữ liệu thật | Gọi `check_prerequisites` hoặc planner |
| Sinh kế hoạch nhiều học kỳ | Dễ bịa | Gọi `generate_study_plan` |
| What-if | Có thể nói chung chung | Gọi `simulate_what_if`, không ghi đè plan gốc |
| Gửi/duyệt kế hoạch | Không có trạng thái | Gọi `submit_plan`, `review_plan` |
| Guardrail | Phụ thuộc prompt | Tool trả lỗi, agent không bịa |

## 6. Kết Luận

Academic Advisor nên dùng mô hình hybrid: planner/rule-based quyết định kế hoạch, ReAct Agent giải thích và điều phối tool, cố vấn con người phê duyệt cuối cùng.
