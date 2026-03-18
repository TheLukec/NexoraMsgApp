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
const usersListContainer = document.getElementById("users-list");
const statusText = document.getElementById("status");
const connectedUser = document.getElementById("connected-user");
const connectedServer = document.getElementById("connected-server");

const changePasswordForm = document.getElementById("change-password-form");
const currentPasswordInput = document.getElementById("current-password");
const newPasswordInput = document.getElementById("new-password");
const confirmPasswordInput = document.getElementById("confirm-password");
const passwordFeedback = document.getElementById("password-feedback");

const SESSION_KEY = "nexora_session";
const state = {
  serverUrl: "",
  token: "",
  username: "",
  messagePollTimer: null,
  usersPollTimer: null,
};

function setStatus(message) {
  statusText.textContent = message;
}

function setPasswordFeedback(message, isError = false) {
  if (!passwordFeedback) {
    return;
  }

  passwordFeedback.textContent = message;
  passwordFeedback.classList.remove("password-feedback-success", "password-feedback-error", "muted");
  passwordFeedback.classList.add(isError ? "password-feedback-error" : "password-feedback-success");
}

function clearPasswordFeedback() {
  if (!passwordFeedback) {
    return;
  }

  passwordFeedback.textContent = "";
  passwordFeedback.classList.remove("password-feedback-success", "password-feedback-error");
  passwordFeedback.classList.add("muted");
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
  if (state.messagePollTimer) {
    clearInterval(state.messagePollTimer);
    state.messagePollTimer = null;
  }
  if (state.usersPollTimer) {
    clearInterval(state.usersPollTimer);
    state.usersPollTimer = null;
  }
}

function startPolling() {
  stopPolling();
  state.messagePollTimer = setInterval(fetchMessages, 3000);
  state.usersPollTimer = setInterval(fetchUsersPresence, 8000);
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

  const header = document.createElement("div");
  header.className = "message-header";

  const meta = document.createElement("div");
  meta.className = "message-meta";
  const created = new Date(message.created_at).toLocaleString();
  meta.textContent = `${message.username} | ${created}`;

  header.appendChild(meta);

  // Delete is shown only for messages created by the currently logged-in user.
  if (message.username === state.username) {
    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "message-delete";
    deleteButton.textContent = "Delete";
    deleteButton.addEventListener("click", () => {
      void deleteMessage(message.id);
    });
    header.appendChild(deleteButton);
  }

  const body = document.createElement("div");
  body.textContent = message.content;

  wrapper.appendChild(header);
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

function userToElement(user) {
  const row = document.createElement("div");
  row.className = "user-row";

  const indicator = document.createElement("span");
  indicator.className = user.online ? "user-indicator online" : "user-indicator";

  const name = document.createElement("span");
  name.className = "user-name";
  name.textContent = user.username;

  const status = document.createElement("span");
  status.className = "user-status";
  status.textContent = user.online ? "online" : "offline";

  row.appendChild(indicator);
  row.appendChild(name);
  row.appendChild(status);

  return row;
}

function renderUsers(users) {
  usersListContainer.innerHTML = "";

  users.forEach((user) => {
    usersListContainer.appendChild(userToElement(user));
  });

  if (users.length === 0) {
    const empty = document.createElement("div");
    empty.className = "muted";
    empty.textContent = "No users found.";
    usersListContainer.appendChild(empty);
  }
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
      await logout(false);
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

async function fetchUsersPresence() {
  if (!state.serverUrl || !state.token) {
    return;
  }

  try {
    const response = await fetch(`${state.serverUrl}/api/users/presence`, {
      headers: {
        Authorization: `Bearer ${state.token}`,
      },
    });

    if (response.status === 401) {
      setStatus("Session expired. Please login again.");
      await logout(false);
      return;
    }

    if (!response.ok) {
      const body = await response.text();
      setStatus(`Cannot load users: ${response.status} ${body}`);
      return;
    }

    const users = await response.json();
    renderUsers(users);
  } catch (error) {
    setStatus(`Users list error: ${error.message}`);
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
    clearPasswordFeedback();
    setStatus("Login successful");

    await fetchMessages();
    await fetchUsersPresence();
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

    if (response.status === 401) {
      setStatus("Session expired. Please login again.");
      await logout(false);
      return;
    }

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      setStatus(data.detail || "Failed to send message");
      return;
    }

    messageInput.value = "";
    await fetchMessages();
    await fetchUsersPresence();
  } catch (error) {
    setStatus(`Send error: ${error.message}`);
  }
}
async function deleteMessage(messageId) {
  try {
    const response = await fetch(`${state.serverUrl}/api/messages/${messageId}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${state.token}`,
      },
    });

    if (response.status === 401) {
      setStatus("Session expired. Please login again.");
      await logout(false);
      return;
    }

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      setStatus(data.detail || "Failed to delete message");
      return;
    }

    setStatus(data.detail || "Message deleted");
    await fetchMessages();
    await fetchUsersPresence();
  } catch (error) {
    setStatus(`Delete error: ${error.message}`);
  }
}

async function changePassword(event) {
  event.preventDefault();

  if (!state.serverUrl || !state.token) {
    setPasswordFeedback("You must be logged in.", true);
    return;
  }

  const currentPassword = currentPasswordInput.value;
  const newPassword = newPasswordInput.value;
  const confirmPassword = confirmPasswordInput.value;

  if (newPassword.length < 6) {
    setPasswordFeedback("New password must be at least 6 characters.", true);
    return;
  }

  if (newPassword !== confirmPassword) {
    setPasswordFeedback("New password and confirm password do not match.", true);
    return;
  }

  try {
    const response = await fetch(`${state.serverUrl}/api/user/change-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${state.token}`,
      },
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });

    if (response.status === 401) {
      setStatus("Session expired. Please login again.");
      await logout(false);
      return;
    }

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      setPasswordFeedback(data.detail || "Password change failed.", true);
      return;
    }

    changePasswordForm.reset();
    setPasswordFeedback(data.detail || "Password changed successfully", false);
  } catch (error) {
    setPasswordFeedback(`Password change error: ${error.message}`, true);
  }
}

async function notifyServerLogout() {
  if (!state.serverUrl || !state.token) {
    return;
  }

  try {
    await fetch(`${state.serverUrl}/api/auth/logout`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${state.token}`,
      },
    });
  } catch (_) {
    // Ignore network errors during logout cleanup.
  }
}

async function logout(notifyServer = true) {
  if (notifyServer) {
    await notifyServerLogout();
  }

  stopPolling();
  state.serverUrl = "";
  state.token = "";
  state.username = "";
  clearSession();
  messagesContainer.innerHTML = "";
  usersListContainer.innerHTML = "";
  if (changePasswordForm) {
    changePasswordForm.reset();
  }
  clearPasswordFeedback();
  showLogin();
}

async function tryRestoreSession() {
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
      clearPasswordFeedback();
      await fetchMessages();
      await fetchUsersPresence();
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
if (changePasswordForm) {
  changePasswordForm.addEventListener("submit", changePassword);
}
refreshBtn.addEventListener("click", async () => {
  await fetchMessages();
  await fetchUsersPresence();
});
logoutBtn.addEventListener("click", () => {
  void logout(true);
});

void tryRestoreSession();

