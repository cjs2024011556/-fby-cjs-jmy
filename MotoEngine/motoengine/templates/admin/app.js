const state = {
  overview: null,
  sessions: [],
  selectedSessionId: null,
  selectedChatId: null,
  currentChats: [],
};

const $ = (id) => document.getElementById(id);

const refs = {
  refreshAllBtn: $("refreshAllBtn"),
  createSessionBtn: $("createSessionBtn"),
  loadCurrentBtn: $("loadCurrentBtn"),
  deleteSessionBtn: $("deleteSessionBtn"),
  newChatBtn: $("newChatBtn"),
  saveSessionBtn: $("saveSessionBtn"),
  clearSessionBtn: $("clearSessionBtn"),
  saveChatBtn: $("saveChatBtn"),
  deleteChatBtn: $("deleteChatBtn"),
  resetChatBtn: $("resetChatBtn"),
  sessionSearch: $("sessionSearch"),
  sessionList: $("sessionList"),
  chatTable: $("chatTable"),
  currentSessionText: $("currentSessionText"),
  sessionTitlePreview: $("sessionTitlePreview"),
  sessionUpdatedPreview: $("sessionUpdatedPreview"),
  chapterSummary: $("chapterSummary"),
  sessionCount: $("sessionCount"),
  chatCount: $("chatCount"),
  vectorCount: $("vectorCount"),
  manualState: $("manualState"),
  sessionTitleInput: $("sessionTitleInput"),
  sessionIdInput: $("sessionIdInput"),
  chatIdInput: $("chatIdInput"),
  questionInput: $("questionInput"),
  answerInput: $("answerInput"),
  sourceInput: $("sourceInput"),
  chapterInput: $("chapterInput"),
  chapterIdInput: $("chapterIdInput"),
  reasonInput: $("reasonInput"),
  completedInput: $("completedInput"),
};

function shortTime(value) {
  if (!value) return "-";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? value : d.toLocaleString();
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

async function apiJson(path, options = {}) {
  const response = await api(path, options);
  if (response.status === 204) return null;
  return response.json();
}

function renderEmpty(target, text) {
  target.innerHTML = `<div class="empty">${text}</div>`;
}

function resetChatForm() {
  refs.chatIdInput.value = "";
  refs.questionInput.value = "";
  refs.answerInput.value = "";
  refs.sourceInput.value = "";
  refs.chapterInput.value = "";
  refs.chapterIdInput.value = "";
  refs.reasonInput.value = "";
  refs.completedInput.checked = false;
  state.selectedChatId = null;
}

function fillChatForm(chat) {
  refs.chatIdInput.value = chat.chat_id || "";
  refs.questionInput.value = chat.question || "";
  refs.answerInput.value = chat.answer || "";
  refs.sourceInput.value = chat.metadata?.source || "";
  refs.chapterInput.value = chat.metadata?.chapter_name || chat.metadata?.chapter_id || "";
  refs.chapterIdInput.value = chat.metadata?.chapter_id || "";
  refs.reasonInput.value = chat.metadata?.reasoning || "";
  refs.completedInput.checked = Boolean(chat.completed);
  state.selectedChatId = chat.chat_id || null;
}

function renderSessions() {
  const filter = (refs.sessionSearch.value || "").trim().toLowerCase();
  const sessions = state.sessions.filter((item) => {
    const text = `${item.title || ""} ${item.session_id || ""}`.toLowerCase();
    return text.includes(filter);
  });

  refs.sessionList.innerHTML = "";
  if (!sessions.length) {
    renderEmpty(refs.sessionList, "暂无会话");
    return;
  }

  sessions.forEach((session) => {
    const item = document.createElement("div");
    item.className = `session-item ${session.session_id === state.selectedSessionId ? "active" : ""}`;
    item.innerHTML = `
      <strong>${session.title || "新会话"}</strong>
      <small>${session.session_id}</small>
      <small>${session.chat_count || 0} 条消息 · ${shortTime(session.updated_at)}</small>
    `;
    item.onclick = () => selectSession(session.session_id);
    refs.sessionList.appendChild(item);
  });
}

function renderChatTable() {
  refs.chatTable.innerHTML = "";
  if (!state.currentChats.length) {
    const row = document.createElement("tr");
    row.innerHTML = `<td colspan="6"><div class="empty">这个会话暂时没有聊天记录</div></td>`;
    refs.chatTable.appendChild(row);
    return;
  }

  state.currentChats.forEach((chat) => {
    const row = document.createElement("tr");
    row.style.background =
      chat.chat_id === state.selectedChatId ? "rgba(56, 189, 248, 0.08)" : "transparent";
    row.innerHTML = `
      <td>${chat.question || ""}</td>
      <td>${(chat.answer || "").slice(0, 120) || "（空）"}</td>
      <td>${chat.metadata?.source || "-"}</td>
      <td>${chat.completed ? '<span class="chip">已完成</span>' : '<span class="chip">进行中</span>'}</td>
      <td>${shortTime(chat.updated_at)}</td>
      <td>
        <div class="cell-actions">
          <button class="ghost-btn small" data-action="edit">编辑</button>
          <button class="danger-btn small" data-action="delete">删除</button>
        </div>
      </td>
    `;
    row.querySelector('[data-action="edit"]').onclick = () => fillChatForm(chat);
    row.querySelector('[data-action="delete"]').onclick = async () => {
      if (!confirm("确定删除这条聊天记录吗？")) return;
      await apiJson(`/api/v2/admin/sessions/${state.selectedSessionId}/chats/${chat.chat_id}`, {
        method: "DELETE",
      });
      await loadSessionDetail(state.selectedSessionId);
      await loadSessions();
    };
    row.onclick = (event) => {
      if (event.target.closest("button")) return;
      fillChatForm(chat);
    };
    refs.chatTable.appendChild(row);
  });
}

function updateOverviewUI() {
  const overview = state.overview || {};
  refs.sessionCount.textContent = String(overview.session_count || 0);
  refs.chatCount.textContent = String(overview.chat_count || 0);
  refs.vectorCount.textContent = String(overview.vector_chunks || 0);
  refs.manualState.textContent = overview.manual_loaded ? "已加载" : "未加载";
  refs.chapterSummary.textContent =
    overview.vector_chapters && Object.keys(overview.vector_chapters).length
      ? Object.entries(overview.vector_chapters)
          .map(([chapter, count]) => `第${chapter}章 ${count}`)
          .join(" · ")
      : "-";
}

async function loadOverview() {
  state.overview = await apiJson("/api/v2/admin/overview");
  updateOverviewUI();
}

async function loadSessions() {
  const data = await apiJson("/api/v2/admin/sessions");
  state.sessions = data.sessions || [];
  renderSessions();
}

async function loadSessionDetail(sessionId) {
  if (!sessionId) return;
  const detail = await apiJson(`/api/v2/admin/sessions/${sessionId}`);
  state.selectedSessionId = detail.session_id;
  state.currentChats = detail.chats || [];

  refs.currentSessionText.textContent = `${detail.session_id}`;
  refs.sessionTitlePreview.textContent = detail.title || "新会话";
  refs.sessionUpdatedPreview.textContent = shortTime(detail.updated_at);
  refs.sessionTitleInput.value = detail.title || "";
  refs.sessionIdInput.value = detail.session_id || "";
  renderSessions();
  renderChatTable();
}

async function selectSession(sessionId) {
  await loadSessionDetail(sessionId);
  resetChatForm();
}

async function createSession() {
  const title = prompt("请输入会话标题", "新会话") || "新会话";
  const detail = await apiJson("/api/v2/admin/sessions", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
  await refreshAll();
  await selectSession(detail.session_id);
}

async function saveSession() {
  const sessionId = refs.sessionIdInput.value.trim();
  const title = refs.sessionTitleInput.value.trim();
  if (!sessionId) {
    const created = await apiJson("/api/v2/admin/sessions", {
      method: "POST",
      body: JSON.stringify({ title: title || "新会话" }),
    });
    await refreshAll();
    await selectSession(created.session_id);
    return;
  }
  await apiJson(`/api/v2/admin/sessions/${sessionId}`, {
    method: "PUT",
    body: JSON.stringify({ title: title || "新会话" }),
  });
  await refreshAll();
  await selectSession(sessionId);
}

async function deleteSession() {
  if (!state.selectedSessionId) return;
  if (!confirm("确定删除当前会话吗？")) return;
  await apiJson(`/api/v2/admin/sessions/${state.selectedSessionId}`, { method: "DELETE" });
  state.selectedSessionId = null;
  state.currentChats = [];
  refs.currentSessionText.textContent = "尚未选择会话";
  refs.sessionTitlePreview.textContent = "-";
  refs.sessionUpdatedPreview.textContent = "-";
  refs.sessionIdInput.value = "";
  refs.sessionTitleInput.value = "";
  resetChatForm();
  await refreshAll();
}

async function saveChat() {
  if (!state.selectedSessionId) {
    alert("请先选择一个会话");
    return;
  }
  const payload = {
    question: refs.questionInput.value.trim(),
    answer: refs.answerInput.value.trim(),
    metadata: {
      source: refs.sourceInput.value.trim() || "rag",
      reasoning: refs.reasonInput.value.trim(),
      chapter_name: refs.chapterInput.value.trim() || null,
      chapter_id: refs.chapterIdInput.value.trim() || null,
    },
    completed: refs.completedInput.checked,
  };
  if (!payload.question) {
    alert("问题不能为空");
    return;
  }

  if (state.selectedChatId) {
    await apiJson(`/api/v2/admin/sessions/${state.selectedSessionId}/chats/${state.selectedChatId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  } else {
    await apiJson(`/api/v2/admin/sessions/${state.selectedSessionId}/chats`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  await loadSessionDetail(state.selectedSessionId);
  await loadSessions();
}

async function deleteChat() {
  if (!state.selectedSessionId || !state.selectedChatId) {
    alert("请先选择一条聊天记录");
    return;
  }
  if (!confirm("确定删除这条聊天记录吗？")) return;
  await apiJson(`/api/v2/admin/sessions/${state.selectedSessionId}/chats/${state.selectedChatId}`, {
    method: "DELETE",
  });
  await loadSessionDetail(state.selectedSessionId);
  await loadSessions();
  resetChatForm();
}

async function refreshAll() {
  await Promise.all([loadOverview(), loadSessions()]);
  if (state.selectedSessionId) {
    try {
      await loadSessionDetail(state.selectedSessionId);
    } catch {
      state.selectedSessionId = null;
    }
  }
}

function bindEvents() {
  refs.refreshAllBtn.onclick = refreshAll;
  refs.createSessionBtn.onclick = createSession;
  refs.loadCurrentBtn.onclick = async () => {
    if (state.selectedSessionId) await loadSessionDetail(state.selectedSessionId);
  };
  refs.deleteSessionBtn.onclick = deleteSession;
  refs.newChatBtn.onclick = resetChatForm;
  refs.saveSessionBtn.onclick = saveSession;
  refs.clearSessionBtn.onclick = () => {
    refs.sessionIdInput.value = "";
    refs.sessionTitleInput.value = "";
  };
  refs.saveChatBtn.onclick = saveChat;
  refs.deleteChatBtn.onclick = deleteChat;
  refs.resetChatBtn.onclick = resetChatForm;
  refs.sessionSearch.addEventListener("input", renderSessions);
}

async function bootstrap() {
  bindEvents();
  await refreshAll();
  if (state.sessions.length && !state.selectedSessionId) {
    await selectSession(state.sessions[0].session_id);
  }
}

bootstrap().catch((error) => {
  console.error(error);
  alert(`管理台加载失败：${error.message}`);
});
