const addForm = document.getElementById("add-form");
const urlInput = document.getElementById("url-input");
const addBtn = document.getElementById("add-btn");
const lessonList = document.getElementById("lesson-list");
const emptyState = document.getElementById("empty-state");
const errorBanner = document.getElementById("error-banner");

const STAGE_LABELS = {
  queued: "Đang xếp hàng...",
  metadata: "Đang lấy thông tin video...",
  audio: "Đang tải audio...",
  transcribing: "Đang nhận diện giọng nói...",
  segmenting: "Đang tách câu...",
  done: "Sẵn sàng",
  error: "Lỗi",
};

const openSockets = new Map();

function showError(message) {
  errorBanner.textContent = message;
  errorBanner.classList.add("visible");
  setTimeout(() => errorBanner.classList.remove("visible"), 6000);
}

function statusBadgeClass(status) {
  if (status === "ready") return "status-badge ready";
  if (status === "error") return "status-badge error";
  return "status-badge";
}

function renderLessons(lessons) {
  lessonList.innerHTML = "";
  emptyState.classList.toggle("hidden", lessons.length > 0);

  for (const lesson of lessons) {
    const card = document.createElement("div");
    card.className = "lesson-card";

    const inProgress = !["ready", "error"].includes(lesson.status);
    const stageLabel = STAGE_LABELS[lesson.stage] || lesson.stage;

    card.innerHTML = `
      <div class="lesson-info">
        <div class="lesson-title">${escapeHtml(lesson.title || lesson.id)}</div>
        <div class="lesson-meta">
          ${lesson.segment_count} câu${lesson.duration_sec ? " · " + formatDuration(lesson.duration_sec) : ""}
        </div>
        ${
          inProgress
            ? `<div class="progress-bar-track"><div class="progress-bar-fill" style="width:${lesson.progress_pct}%"></div></div>`
            : ""
        }
        ${lesson.status === "error" ? `<div class="lesson-meta">${escapeHtml(lesson.error_message || "")}</div>` : ""}
      </div>
      <span class="${statusBadgeClass(lesson.status)}">
        ${lesson.status === "ready" ? "Sẵn sàng ▶" : lesson.status === "error" ? "Lỗi" : stageLabel}
      </span>
    `;

    if (lesson.status === "ready") {
      card.style.cursor = "pointer";
      card.addEventListener("click", () => {
        window.location.href = `practice.html?id=${encodeURIComponent(lesson.id)}`;
      });
    }

    lessonList.appendChild(card);

    if (inProgress && !openSockets.has(lesson.id)) {
      trackProgress(lesson.id);
    }
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function formatDuration(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60)
    .toString()
    .padStart(2, "0");
  return `${m}:${s}`;
}

async function refreshLessons() {
  try {
    const lessons = await Api.listLessons();
    renderLessons(lessons);
  } catch (err) {
    showError(err.message);
  }
}

async function trackProgress(lessonId) {
  const ws = await Api.jobSocket(lessonId, (event) => {
    if (event.status === "ready" || event.status === "error") {
      openSockets.delete(lessonId);
      refreshLessons();
    } else {
      refreshLessons();
    }
  });
  openSockets.set(lessonId, ws);
}

addForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const url = urlInput.value.trim();
  if (!url) return;

  addBtn.disabled = true;
  try {
    const lesson = await Api.addLesson(url);
    urlInput.value = "";
    await refreshLessons();
    if (!["ready", "error"].includes(lesson.status)) {
      trackProgress(lesson.id);
    }
  } catch (err) {
    showError(err.message);
  } finally {
    addBtn.disabled = false;
  }
});

refreshLessons();
