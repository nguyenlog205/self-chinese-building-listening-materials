const contentSelect = document.getElementById("content-select");
const emptyState = document.getElementById("empty-state");
const practice = document.getElementById("practice");
const progressLabel = document.getElementById("progress-label");
const playBtn = document.getElementById("play-btn");
const replayBtn = document.getElementById("replay-btn");
const audioPlayer = document.getElementById("audio-player");
const answerInput = document.getElementById("answer-input");
const answerFeedback = document.getElementById("answer-feedback");
const pinyinToggle = document.getElementById("pinyin-toggle");
const textToggle = document.getElementById("text-toggle");
const pinyinLine = document.getElementById("pinyin-line");
const textLine = document.getElementById("text-line");
const checkBtn = document.getElementById("check-btn");
const prevBtn = document.getElementById("prev-btn");
const nextBtn = document.getElementById("next-btn");

let sentences = [];
let currentIndex = 0;

async function loadContents() {
  const res = await fetch("/api/contents");
  const contents = await res.json();

  contentSelect.innerHTML =
    '<option value="">— Chọn bài —</option>' +
    contents
      .map(
        (c) =>
          `<option value="${c.content_id}">${c.content_id} (${c.sentence_count} câu)</option>`
      )
      .join("");
}

async function loadContent(contentId) {
  const res = await fetch(`/api/contents/${encodeURIComponent(contentId)}/sentences`);
  sentences = await res.json();
  currentIndex = 0;
  emptyState.classList.add("hidden");
  practice.classList.remove("hidden");
  renderCurrent();
}

function renderCurrent() {
  const sentence = sentences[currentIndex];
  progressLabel.textContent = `${currentIndex + 1} / ${sentences.length}`;
  audioPlayer.src = `/${sentence.audio_path}`;

  answerInput.value = "";
  answerFeedback.innerHTML = "";
  pinyinToggle.checked = false;
  textToggle.checked = false;
  pinyinLine.classList.add("hidden");
  textLine.classList.add("hidden");
  pinyinLine.textContent = sentence.pinyin;
  textLine.textContent = sentence.text_zh;

  prevBtn.disabled = currentIndex === 0;
  nextBtn.disabled = currentIndex === sentences.length - 1;
}

function playAudio() {
  audioPlayer.currentTime = 0;
  audioPlayer.play();
}

function checkAnswer() {
  const target = sentences[currentIndex].text_zh;
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

contentSelect.addEventListener("change", () => {
  if (contentSelect.value) {
    loadContent(contentSelect.value);
  } else {
    practice.classList.add("hidden");
    emptyState.classList.remove("hidden");
  }
});

playBtn.addEventListener("click", playAudio);
replayBtn.addEventListener("click", playAudio);

checkBtn.addEventListener("click", checkAnswer);
answerInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") checkAnswer();
});

pinyinToggle.addEventListener("change", () => {
  pinyinLine.classList.toggle("hidden", !pinyinToggle.checked);
});
textToggle.addEventListener("change", () => {
  textLine.classList.toggle("hidden", !textToggle.checked);
});

prevBtn.addEventListener("click", () => {
  if (currentIndex > 0) {
    currentIndex--;
    renderCurrent();
  }
});
nextBtn.addEventListener("click", () => {
  if (currentIndex < sentences.length - 1) {
    currentIndex++;
    renderCurrent();
  }
});

loadContents();
