const state = {
  schoolId: "demo_uni",
  studentId: "",
  students: [],
  programs: [],
  plan: null,
};

const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  return res.json();
}

function setText(id, value) {
  $(id).textContent = value ?? "-";
}

function selectedStudent() {
  return state.students.find((student) => student.id === state.studentId);
}

function selectedProgram() {
  return state.programs.find((program) => program.id === $("programSelect").value);
}

function renderTracks() {
  const program = selectedProgram();
  const tracks = Object.keys(program?.tracks || {});
  $("trackSelect").innerHTML = tracks.length
    ? tracks.map((track) => `<option>${track}</option>`).join("")
    : `<option>General</option>`;
}

function renderStudent() {
  const student = selectedStudent();
  if (!student) {
    $("studentSnapshot").innerHTML = `<span>Nhập hồ sơ thật của sinh viên, hoặc chọn mẫu nhanh để điền tự động.</span>`;
    return;
  }
  $("studentSnapshot").innerHTML = `
    <strong>${student.name}</strong>
    <span>Năm ${student.year} · GPA ${student.gpa}</span>
    <span>Đã học: ${student.completed_courses.join(", ") || "chưa có"}</span>
    <span>Môn lưu ý: ${student.failed_courses.join(", ") || "không"}</span>
  `;
  $("studentNameInput").value = student.name;
  $("programSelect").value = student.program_id;
  renderTracks();
  $("currentYearSelect").value = student.year;
  $("gpaInput").value = student.gpa;
  $("trackSelect").value = student.career_track;
  $("goalSelect").value = student.goal;
  $("interestsInput").value = student.interests.join(", ");
  $("completedInput").value = student.completed_courses.join(", ");
  $("failedInput").value = student.failed_courses.join(", ");
  $("yearsInput").value = Math.max(1, 5 - Number(student.year || 1));
}

function renderPlan(data) {
  const { profile, plan, llm_analysis } = data;
  state.plan = plan.ok ? plan : null;
  setText("riskMetric", profile.risk_level || "-");
  setText("gpaMetric", profile.gpa ?? "-");
  setText("planMetric", plan.plan_id || "-");
  setText("creditMetric", plan.max_credits_per_term || "-");
  setText("planStatus", plan.status || "Không sinh được");
  setText("analysisText", llm_analysis || plan.error || "Không có phân tích.");
  setText("alertCount", `${(plan.alerts || []).length} cảnh báo`);

  if (!plan.ok) {
    $("timeline").innerHTML = `<div class="analysis-panel">${plan.error}</div>`;
    return;
  }

  $("timeline").innerHTML = plan.terms.map((term) => `
    <article class="term-card">
      <div class="term-meta">
        <strong>${term.label}</strong>
        <span>${term.academic_year}</span>
        <span>${term.credits} tín chỉ</span>
      </div>
      <div class="course-list">
        ${term.courses.length ? term.courses.map((course) => `
          <div class="course-item">
            <div class="course-code">${course.id}</div>
            <div class="course-name">
              ${course.name}
              <span>${course.why}</span>
            </div>
            <div class="credit-badge">${course.credits} TC</div>
          </div>
        `).join("") : `<div class="empty-term">Không xếp môn trong kỳ này</div>`}
      </div>
    </article>
  `).join("");
}

function addMessage(role, text) {
  const item = document.createElement("div");
  item.className = `message ${role}`;
  item.textContent = text;
  $("chatLog").appendChild(item);
  $("chatLog").scrollTop = $("chatLog").scrollHeight;
}

async function loadSchools() {
  const data = await api("/api/schools");
  $("schoolSelect").innerHTML = data.schools.map((school) => `<option value="${school.id}">${school.name}</option>`).join("");
  state.schoolId = data.schools.some((school) => school.id === "uit") ? "uit" : data.schools[0]?.id;
  $("schoolSelect").value = state.schoolId;
}

async function loadPrograms() {
  const data = await api(`/api/schools/${state.schoolId}/programs`);
  state.programs = data.programs || [];
  $("programSelect").innerHTML = state.programs.map((program) => `<option value="${program.id}">${program.name}</option>`).join("");
  renderTracks();
}

async function loadStudents() {
  const data = await api(`/api/schools/${state.schoolId}/students`);
  state.students = data.students || [];
  $("studentSelect").innerHTML = `<option value="">Tự nhập hồ sơ</option>` + state.students.map((student) => `<option value="${student.id}">${student.id} · ${student.name}</option>`).join("");
  state.studentId = "";
  renderStudent();
}

async function generateRoadmap() {
  const studentName = $("studentNameInput").value.trim();
  const payload = {
    school_id: state.schoolId,
    student_id: state.studentId,
    student_name: studentName,
    program_id: $("programSelect").value,
    current_year: Number($("currentYearSelect").value),
    gpa: Number($("gpaInput").value),
    completed_courses: $("completedInput").value,
    failed_courses: $("failedInput").value,
    goal: $("goalSelect").value,
    career_track: $("trackSelect").value,
    interests: $("interestsInput").value,
    max_credits_per_term: Number($("creditsInput").value),
    start_year: 2026,
    years: Number($("yearsInput").value),
  };
  $("generateBtn").disabled = true;
  setText("analysisText", "Đang sinh lộ trình...");
  try {
    renderPlan(await api("/api/roadmap", { method: "POST", body: JSON.stringify(payload) }));
  } finally {
    $("generateBtn").disabled = false;
  }
}

async function submitPlan() {
  if (!state.plan) return;
  const data = await api(`/api/plans/${state.plan.plan_id}/submit`, {
    method: "POST",
    body: JSON.stringify({ student_id: state.plan.student_id }),
  });
  setText("planStatus", data.status || data.error);
  addMessage("ai", data.message || data.error || "Đã cập nhật trạng thái.");
}

async function approvePlan() {
  if (!state.plan) return;
  const student = selectedStudent();
  const data = await api(`/api/plans/${state.plan.plan_id}/review`, {
    method: "POST",
    body: JSON.stringify({ advisor_id: state.plan.advisor_id || student?.advisor_id || "CUSTOM_ADV", decision: "approve" }),
  });
  setText("planStatus", data.status || data.error);
  addMessage("ai", data.error || `Cố vấn đã cập nhật: ${data.status}`);
}

async function sendChat(event) {
  event.preventDefault();
  const question = $("chatInput").value.trim();
  if (!question) return;
  $("chatInput").value = "";
  addMessage("user", question);
  const data = await api("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      school_id: state.schoolId,
      student_id: state.plan?.student_id || state.studentId || "CUSTOM",
      question,
      plan_id: state.plan?.plan_id,
    }),
  });
  addMessage("ai", data.answer || "Chưa có câu trả lời.");
}

async function searchCatalog(event) {
  event.preventDefault();
  const q = $("catalogInput").value.trim();
  if (!q) return;
  const data = await api(`/api/catalog/search?school_id=${encodeURIComponent(state.schoolId)}&q=${encodeURIComponent(q)}&limit=8`);
  if (!data.ok) {
    $("catalogResults").innerHTML = `<div class="catalog-item"><p>${data.error}</p></div>`;
    return;
  }
  $("catalogResults").innerHTML = data.courses.map((course) => `
    <div class="catalog-item">
      <strong>${course.id} · ${course.name}</strong>
      <p>${(course.description || "Chưa có mô tả.").slice(0, 220)}</p>
    </div>
  `).join("");
}

async function init() {
  await loadSchools();
  await loadPrograms();
  await loadStudents();
  addMessage("ai", "Mình sẽ phân tích GPA, định hướng, sở thích và dữ liệu học vụ đã validate để giải thích lộ trình môn tự chọn.");
}

$("schoolSelect").addEventListener("change", async (event) => {
  state.schoolId = event.target.value;
  await loadPrograms();
  await loadStudents();
});

$("studentSelect").addEventListener("change", (event) => {
  state.studentId = event.target.value;
  renderStudent();
});

$("programSelect").addEventListener("change", renderTracks);
$("currentYearSelect").addEventListener("change", () => {
  $("yearsInput").value = Math.max(1, 5 - Number($("currentYearSelect").value));
});

$("generateBtn").addEventListener("click", generateRoadmap);
$("submitBtn").addEventListener("click", submitPlan);
$("approveBtn").addEventListener("click", approvePlan);
$("chatForm").addEventListener("submit", sendChat);
$("catalogForm").addEventListener("submit", searchCatalog);

init();
