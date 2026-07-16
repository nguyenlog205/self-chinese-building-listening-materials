let basePromise = null;

async function apiBase() {
  if (!basePromise) {
    basePromise = window.listeningApp
      .getBackendPort()
      .then((port) => `http://127.0.0.1:${port}`);
  }
  return basePromise;
}

async function apiFetch(path, options) {
  const base = await apiBase();
  const res = await fetch(`${base}${path}`, options);
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

async function wsBase() {
  const base = await apiBase();
  return base.replace("http://", "ws://");
}

const Api = {
  listLessons: () => apiFetch("/api/lessons"),
  addLesson: (url) =>
    apiFetch("/api/lessons", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    }),
  getLesson: (id) => apiFetch(`/api/lessons/${encodeURIComponent(id)}`),
  getSegments: (id) => apiFetch(`/api/lessons/${encodeURIComponent(id)}/segments`),
  markPracticed: (id) =>
    apiFetch(`/api/lessons/${encodeURIComponent(id)}/practiced`, { method: "POST" }),
  deleteLesson: (id) =>
    apiFetch(`/api/lessons/${encodeURIComponent(id)}`, { method: "DELETE" }),
  jobSocket: async (id, onEvent) => {
    const base = await wsBase();
    const ws = new WebSocket(`${base}/ws/jobs/${encodeURIComponent(id)}`);
    ws.onmessage = (msg) => onEvent(JSON.parse(msg.data));
    return ws;
  },
};
