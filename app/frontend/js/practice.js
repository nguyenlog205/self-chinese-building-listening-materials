const params = new URLSearchParams(window.location.search);
const lessonId = params.get("id");

const lessonTitleEl = document.getElementById("lesson-title");
const subtitleToggle = document.getElementById("subtitle-toggle");
const pinyinToggle = document.getElementById("pinyin-toggle");
const dictationToggle = document.getElementById("dictation-toggle");
const volumeSlider = document.getElementById("volume-slider");
const speedSelect = document.getElementById("speed-select");
const pinyinLine = document.getElementById("pinyin-line");
const textLine = document.getElementById("text-line");
const dictationPanel = document.getElementById("dictation-panel");
const answerInput = document.getElementById("answer-input");
const answerFeedback = document.getElementById("answer-feedback");
const checkBtn = document.getElementById("check-btn");
const prevBtn = document.getElementById("prev-btn");
const nextBtn = document.getElementById("next-btn");
const replayBtn = document.getElementById("replay-btn");
const progressLabel = document.getElementById("progress-label");

let segments = [];
let currentIndex = 0;
let player = null;
let playerReady = false;
let boundaryTimer = null;

function renderCurrent() {
  const segment = segments[currentIndex];
  if (!segment) return;

  progressLabel.textContent = `${currentIndex + 1} / ${segments.length}`;
  pinyinLine.textContent = segment.pinyin;
  textLine.textContent = segment.text_zh;
  pinyinLine.classList.toggle("hidden", !pinyinToggle.checked);
  textLine.classList.toggle("hidden", !subtitleToggle.checked);

  answerInput.value = "";
  answerFeedback.innerHTML = "";

  prevBtn.disabled = currentIndex === 0;
  nextBtn.disabled = currentIndex === segments.length - 1;

  playSegment();
}

function playSegment() {
  if (!playerReady) return;
  const segment = segments[currentIndex];
  clearInterval(boundaryTimer);
  player.seekTo(segment.start_sec, true);
  player.playVideo();
  boundaryTimer = setInterval(() => {
    if (player.getCurrentTime() >= segment.end_sec) {
      player.pauseVideo();
      clearInterval(boundaryTimer);
    }
  }, 200);
}

function checkAnswer() {
  const target = segments[currentIndex].text_zh;
  const guess = answerInput.value.trim();
  const len = Math.max(target.length, guess.length);

  let html = "";
  for (let i = 0; i < len; i++) {
    const expected = target[i] ?? "";
    const actual = guess[i] ?? "";
    const shown = expected || actual;
    const cls = expected && expected === actual ? "ok" : "err";
    html += `<span class="${cls}">${shown}</span>`;
  }
  answerFeedback.innerHTML = html;
}

function goTo(index) {
  if (index < 0 || index >= segments.length) return;
  currentIndex = index;
  renderCurrent();
  if (currentIndex === segments.length - 1) {
    Api.markPracticed(lessonId).catch(() => {});
  }
}

subtitleToggle.addEventListener("change", () => {
  textLine.classList.toggle("hidden", !subtitleToggle.checked);
});
pinyinToggle.addEventListener("change", () => {
  pinyinLine.classList.toggle("hidden", !pinyinToggle.checked);
});
dictationToggle.addEventListener("change", () => {
  dictationPanel.classList.toggle("hidden", !dictationToggle.checked);
});
volumeSlider.addEventListener("input", () => {
  if (playerReady) player.setVolume(Number(volumeSlider.value));
});
speedSelect.addEventListener("change", () => {
  if (playerReady) player.setPlaybackRate(Number(speedSelect.value));
});

checkBtn.addEventListener("click", checkAnswer);
answerInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") checkAnswer();
});
prevBtn.addEventListener("click", () => goTo(currentIndex - 1));
nextBtn.addEventListener("click", () => goTo(currentIndex + 1));
replayBtn.addEventListener("click", playSegment);

document.addEventListener("keydown", (e) => {
  if (e.target === answerInput) return;
  if (e.code === "Space") {
    e.preventDefault();
    if (!playerReady) return;
    const state = player.getPlayerState();
    if (state === YT.PlayerState.PLAYING) player.pauseVideo();
    else player.playVideo();
  } else if (e.key === "ArrowRight") {
    goTo(currentIndex + 1);
  } else if (e.key === "ArrowLeft") {
    goTo(currentIndex - 1);
  }
});

function onYouTubeIframeAPIReady() {
  player = new YT.Player("yt-player", {
    videoId: lessonId,
    playerVars: { controls: 1, rel: 0 },
    events: {
      onReady: () => {
        playerReady = true;
        player.setVolume(Number(volumeSlider.value));
        playSegment();
      },
    },
  });
}
window.onYouTubeIframeAPIReady = onYouTubeIframeAPIReady;

async function init() {
  if (!lessonId) {
    window.location.href = "index.html";
    return;
  }
  const [lesson, segs] = await Promise.all([
    Api.getLesson(lessonId),
    Api.getSegments(lessonId),
  ]);
  lessonTitleEl.innerHTML = `${lesson.title} <span class="subtitle">Luyện tập</span>`;
  segments = segs;
  dictationPanel.classList.toggle("hidden", !dictationToggle.checked);
  renderCurrent();
}

init();
