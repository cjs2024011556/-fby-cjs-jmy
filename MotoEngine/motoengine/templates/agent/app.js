const state = {
  sessionId: null,
  sessions: [],
  chapters: {},
  currentStreamingId: null,
  metadata: null,
};

const $ = (id) => document.getElementById(id);

const refs = {
  apiStatus: $("apiStatus"),
  backendState: $("backendState"),
  currentSession: $("currentSession"),
  sessionMeta: $("sessionMeta"),
  routeSource: $("routeSource"),
  routeReason: $("routeReason"),
  debugSource: $("debugSource"),
  debugChapter: $("debugChapter"),
  debugReason: $("debugReason"),
  sessionCount: $("sessionCount"),
  chapterCount: $("chapterCount"),
  sessionList: $("sessionList"),
  chapterList: $("chapterList"),
  quickList: $("quickList"),
  messages: $("messages"),
  composer: $("composer"),
  questionInput: $("questionInput"),
  composerHint: $("composerHint"),
  newSessionBtn: $("newSessionBtn"),
  reloadHistoryBtn: $("reloadHistoryBtn"),
};

function setStatus(text, kind = "ok") {
  refs.apiStatus.textContent = text;
  refs.apiStatus.style.background =
    kind === "error" ? "rgba(251, 113, 133, 0.12)" : "rgba(52, 211, 153, 0.12)";
  refs.apiStatus.style.borderColor =
    kind === "error" ? "rgba(251, 113, 133, 0.3)" : "rgba(52, 211, 153, 0.3)";
}

function shortTime(value) {
  if (!value) return "-";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? value : d.toLocaleString();
}

function scrollToBottom() {
  refs.messages.scrollTop = refs.messages.scrollHeight;
}

function clearMessages() {
  refs.messages.innerHTML = "";
}

function createMessageNode(role, content, meta = {}) {
  const wrap = document.createElement("article");
  wrap.className = `message ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = content || "";

  const metaBar = document.createElement("div");
  metaBar.className = "message-meta";
  metaBar.innerHTML = `
    <span>${role === "user" ? "用户" : "智能体"}</span>
    <span>${meta.created_at ? shortTime(meta.created_at) : ""}</span>
    ${meta.source ? `<span class="chip">${meta.source}</span>` : ""}
  `;

  wrap.appendChild(bubble);
  wrap.appendChild(metaBar);
  refs.messages.appendChild(wrap);
  scrollToBottom();
  return { wrap, bubble, metaBar };
}

function renderEmpty(target, text) {
  target.innerHTML = `<div class="empty-state">${text}</div>`;
}

function renderSessions() {
  refs.sessionList.innerHTML = "";
  if (!state.sessions.length) {
    renderEmpty(refs.sessionList, "还没有会话，先创建一个。");
    return;
  }

  state.sessions.forEach((session) => {
    const item = document.createElement("div");
    item.className = `list-item ${session.session_id === state.sessionId ? "active" : ""}`;
    item.innerHTML = `
      <span>${session.session_id.slice(0, 8)}</span>
      <span class="sub">${session.chat_count} 条消息 · ${shortTime(session.updated_at)}</span>
    `;
    const deleteBtn = document.createElement("button");
    deleteBtn.type = "button";
    deleteBtn.className = "chip";
    deleteBtn.textContent = "删除";
    deleteBtn.style.marginTop = "10px";
    deleteBtn.onclick = (event) => {
      event.stopPropagation();
      deleteSession(session.session_id);
    };

    item.style.cursor = "pointer";
    item.onclick = () => switchSession(session.session_id);
    item.appendChild(deleteBtn);
    refs.sessionList.appendChild(item);
  });
}

function renderChapters() {
  refs.chapterList.innerHTML = "";
  const chapters = Object.entries(state.chapters);
  if (!chapters.length) {
    renderEmpty(refs.chapterList, "章节信息暂时不可用。");
    return;
  }

  chapters.forEach(([chapterId, info]) => {
    const item = document.createElement("button");
    item.className = "list-item";
    item.innerHTML = `
      第${chapterId}章 · ${info.name}
      <span class="sub">${info.sections?.length || 0} 个子章节</span>
    `;
    item.onclick = () => {
      const prompt = `请详细讲解第${chapterId}章 ${info.name} 的维修要点。`;
      refs.questionInput.value = prompt;
      refs.questionInput.focus();
    };
    refs.chapterList.appendChild(item);
  });
}

function renderQuickPrompts() {
  const prompts = [
    ["摩托车发动机保养需要注意什么？", "通用知识"],
    ["如何拆卸火花塞？", "Workflow"],
    ["火花塞的间隙标准值是多少？", "参数查询"],
    ["起动电机如何维修？", "复杂部件"],
  ];

  refs.quickList.innerHTML = "";
  prompts.forEach(([question, label]) => {
    const btn = document.createElement("button");
    btn.className = "quick-btn";
    btn.innerHTML = `<span>${question}</span><small>${label}</small>`;
    btn.onclick = () => {
      refs.questionInput.value = question;
      refs.questionInput.focus();
    };
    refs.quickList.appendChild(btn);
  });
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response;
}

async function loadBackendState() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    setStatus(`后端在线 · ${data.framework}`, "ok");
    refs.backendState.textContent = data.status;
  } catch (error) {
    setStatus("后端不可用", "error");
    refs.backendState.textContent = "离线";
  }
}

async function loadSessions() {
  try {
    const response = await api("/api/v2/chat/sessions", { headers: {} });
    const data = await response.json();
    state.sessions = data.sessions || [];
    refs.sessionCount.textContent = String(state.sessions.length);
    renderSessions();
  } catch (error) {
    refs.sessionCount.textContent = "0";
    renderEmpty(refs.sessionList, "会话列表加载失败。");
  }
}

async function loadChapters() {
  try {
    const response = await api("/api/v2/chat/chapters", { headers: {} });
    const data = await response.json();
    state.chapters = data.chapters || {};
    refs.chapterCount.textContent = String(Object.keys(state.chapters).length);
    renderChapters();
  } catch (error) {
    refs.chapterCount.textContent = "0";
    renderEmpty(refs.chapterList, "章节列表加载失败。");
  }
}

async function createSession() {
  const response = await api("/api/v2/chat/session", { method: "GET", headers: {} });
  const data = await response.json();
  state.sessionId = data.session_id;
  localStorage.setItem("motoengine-session-id", state.sessionId);
  refs.currentSession.textContent = state.sessionId;
  refs.sessionMeta.textContent = `创建于 ${shortTime(data.created_at)}`;
  refs.composerHint.textContent = "可以开始提问了。";
  await Promise.all([loadSessions(), loadHistory(state.sessionId)]);
  renderSessions();
}

async function switchSession(sessionId) {
  state.sessionId = sessionId;
  localStorage.setItem("motoengine-session-id", sessionId);
  refs.currentSession.textContent = sessionId;
  refs.sessionMeta.textContent = "已切换到历史会话";
  renderSessions();
  await loadHistory(sessionId);
}

async function deleteSession(sessionId) {
  if (!confirm("确定删除这个会话吗？")) return;
  await api(`/api/v2/chat/session/${sessionId}`, { method: "DELETE", headers: {} });
  if (state.sessionId === sessionId) {
    state.sessionId = null;
    localStorage.removeItem("motoengine-session-id");
    clearMessages();
    refs.currentSession.textContent = "-";
    refs.sessionMeta.textContent = "等待创建或选择会话";
  }
  await loadSessions();
}

async function loadHistory(sessionId) {
  if (!sessionId) return;
  const response = await api(`/api/v2/chat/${sessionId}/messages`, { headers: {} });
  const data = await response.json();
  clearMessages();

  const chats = data.chats || [];
  if (!chats.length) {
    renderEmpty(refs.messages, "这个会话还没有消息，先发一条吧。");
    return;
  }

  refs.messages.innerHTML = "";
  chats.forEach((chat) => {
    createMessageNode("user", chat.question, { created_at: chat.created_at });
    createMessageNode("assistant", chat.answer || "（当前未生成回答，请重试）", {
      created_at: chat.updated_at,
      source: chat.metadata?.source || "-",
    });
  });
}

function parseSseBlock(block) {
  const event = { name: "message", data: null };
  const lines = block.split(/\r?\n/).filter(Boolean);
  for (const line of lines) {
    if (line.startsWith("event:")) {
      event.name = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      const raw = line.slice(5).trim();
      event.data = raw ? JSON.parse(raw) : null;
    }
  }
  return event.data ? event : null;
}

async function streamMessage(sessionId, question) {
  const response = await fetch(`/api/v2/chat/${sessionId}/messages`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok || !response.body) {
    throw new Error(await response.text());
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let assistantNode = createMessageNode("assistant", "正在分析维修手册...");

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split(/\n\n/);
    buffer = parts.pop() || "";

    for (const part of parts) {
      const payload = parseSseBlock(part);
      if (!payload) continue;

      if (payload.name === "metadata") {
        state.metadata = payload.data.metadata;
        refs.routeSource.textContent = state.metadata?.source || "-";
        refs.routeReason.textContent = state.metadata?.reasoning || "-";
        refs.debugSource.textContent = state.metadata?.source || "-";
        refs.debugChapter.textContent =
          state.metadata?.chapter_name
            ? `第${state.metadata.chapter_id}章 · ${state.metadata.chapter_name}`
            : "-";
        refs.debugReason.textContent = state.metadata?.reasoning || "-";
        assistantNode.bubble.textContent = "";
      } else if (payload.name === "message") {
        const chunk = payload.data.chunk || "";
        assistantNode.bubble.textContent += chunk;
        scrollToBottom();
      } else if (payload.name === "done") {
        assistantNode.metaBar.innerHTML = `
          <span>智能体</span>
          <span>${new Date().toLocaleString()}</span>
          ${state.metadata?.source ? `<span class="chip">${state.metadata.source}</span>` : ""}
        `;
      } else if (payload.name === "error") {
        assistantNode.bubble.textContent = `发生错误：${payload.data.error}`;
        assistantNode.metaBar.innerHTML = `<span>错误</span><span>${new Date().toLocaleString()}</span>`;
      }
    }
  }

  await Promise.all([loadSessions(), loadHistory(sessionId)]);
}

async function handleSubmit(event) {
  event.preventDefault();
  const question = refs.questionInput.value.trim();
  if (!question || !state.sessionId) {
    return;
  }

  createMessageNode("user", question, { created_at: new Date().toISOString() });
  refs.questionInput.value = "";
  refs.composerHint.textContent = "正在流式输出...";

  try {
    await streamMessage(state.sessionId, question);
    refs.composerHint.textContent = "回答完成。";
  } catch (error) {
    createMessageNode("assistant", `请求失败：${error.message}`);
    refs.composerHint.textContent = "请求失败，请稍后重试。";
    setStatus("请求失败", "error");
  }
}

async function bootstrap() {
  renderQuickPrompts();
  setStatus("正在连接后端...", "ok");
  await Promise.all([loadBackendState(), loadChapters(), loadSessions()]);

  const savedSessionId = localStorage.getItem("motoengine-session-id");
  if (savedSessionId) {
    try {
      await switchSession(savedSessionId);
      return;
    } catch {
      localStorage.removeItem("motoengine-session-id");
    }
  }

  await createSession();
}

refs.composer.addEventListener("submit", handleSubmit);
refs.newSessionBtn.addEventListener("click", createSession);
refs.reloadHistoryBtn.addEventListener("click", () => {
  if (state.sessionId) loadHistory(state.sessionId);
});

bootstrap();
