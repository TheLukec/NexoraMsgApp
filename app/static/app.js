const loginPanel = document.getElementById("login-panel");
const chatPanel = document.getElementById("chat-panel");
const loginForm = document.getElementById("login-form");
const sendForm = document.getElementById("send-form");
const refreshBtn = document.getElementById("refresh-btn");
const logoutBtn = document.getElementById("logout-btn");
const serverUrlInput = document.getElementById("server_url");
const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const messageInput = document.getElementById("message-input");
const messagesContainer = document.getElementById("messages");
const statusText = document.getElementById("status");
const connectedUser = document.getElementById("connected-user");
const connectedServer = document.getElementById("connected-server");

const SESSION_KEY = "nexora_session";
const state = {
  serverUrl: "",
  token: "",
  username: "",
  pollTimer: null,
};

function setStatus(message) {
  statusText.textContent = message;
}

function normalizeServerUrl(value) {
  let url = value.trim();
  if (!url) {
    return "";
  }
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    url = `http://${url}`;
  }
  return url.replace(/\/+$/, "");
}

function saveSession() {
  localStorage.setItem(
    SESSION_KEY,
    JSON.stringify({
      serverUrl: state.serverUrl,
      token: state.token,
      username: state.username,
    }),
  );
}

function clearSession() {
  localStorage.removeItem(SESSION_KEY);
}

function stopPolling() {
  if (state.pollTimer) {
    clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
}

function startPolling() {
  stopPolling();
  state.pollTimer = setInterval(fetchMessages, 3000);
}

function showLogin() {
  loginPanel.classList.remove("hidden");
  chatPanel.classList.add("hidden");
}

function showChat() {
  loginPanel.classList.add("hidden");
  chatPanel.classList.remove("hidden");
  connectedUser.textContent = state.username;
  connectedServer.textContent = state.serverUrl;
}

function messageToElement(message) {
  const wrapper = document.createElement("div");
  wrapper.className = "message";

  const meta = document.createElement("div");
  meta.className = "message-meta";
  const created = new Date(message.created_at).toLocaleString();
  meta.textContent = `${message.username} | ${created}`;

  const body = document.createElement("div");
  body.textContent = message.content;

  wrapper.appendChild(meta);
  wrapper.appendChild(body);
  return wrapper;
}

function renderMessages(messages) {
  messagesContainer.innerHTML = "";
  messages.forEach((message) => {
    messagesContainer.appendChild(messageToElement(message));
  });
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function fetchMessages() {
  if (!state.serverUrl || !state.token) {
    return;
  }

  try {
    const response = await fetch(`${state.serverUrl}/api/messages?limit=120`, {
      headers: {
        Authorization: `Bearer ${state.token}`,
      },
    });

    if (response.status === 401) {
      setStatus("Session expired. Please login again.");
      logout();
      return;
    }

    if (!response.ok) {
      const body = await response.text();
      setStatus(`Cannot load messages: ${response.status} ${body}`);
      return;
    }

    const messages = await response.json();
    renderMessages(messages);
    setStatus(`Messages updated at ${new Date().toLocaleTimeString()}`);
  } catch (error) {
    setStatus(`Connection error: ${error.message}`);
  }
}

async function login(event) {
  event.preventDefault();

  const serverUrl = normalizeServerUrl(serverUrlInput.value);
  const username = usernameInput.value.trim();
  const password = passwordInput.value;

  if (!serverUrl || !username || !password) {
    setStatus("Please enter server URL, username and password.");
    return;
  }

  setStatus("Signing in...");
  try {
    const response = await fetch(`${serverUrl}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      setStatus(data.detail || "Login failed");
      return;
    }

    const data = await response.json();
    state.serverUrl = serverUrl;
    state.token = data.access_token;
    state.username = data.user.username;

    saveSession();
    showChat();
    setStatus("Login successful");
    await fetchMessages();
    startPolling();
  } catch (error) {
    setStatus(`Login error: ${error.message}`);
  }
}

async function sendMessage(event) {
  event.preventDefault();
  const content = messageInput.value.trim();
  if (!content) {
    return;
  }

  try {
    const response = await fetch(`${state.serverUrl}/api/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${state.token}`,
      },
      body: JSON.stringify({ content }),
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      setStatus(data.detail || "Failed to send message");
      return;
    }

    messageInput.value = "";
    await fetchMessages();
  } catch (error) {
    setStatus(`Send error: ${error.message}`);
  }
}

function logout() {
  stopPolling();
  state.serverUrl = "";
  state.token = "";
  state.username = "";
  clearSession();
  showLogin();
}

function tryRestoreSession() {
  const raw = localStorage.getItem(SESSION_KEY);
  if (!raw) {
    showLogin();
    return;
  }

  try {
    const parsed = JSON.parse(raw);
    if (parsed.serverUrl && parsed.token && parsed.username) {
      state.serverUrl = parsed.serverUrl;
      state.token = parsed.token;
      state.username = parsed.username;
      showChat();
      fetchMessages();
      startPolling();
      setStatus("Session restored");
      return;
    }
  } catch (_) {
    // Ignore invalid local storage value.
  }

  showLogin();
}

loginForm.addEventListener("submit", login);
sendForm.addEventListener("submit", sendMessage);
refreshBtn.addEventListener("click", fetchMessages);
logoutBtn.addEventListener("click", logout);

tryRestoreSession();
