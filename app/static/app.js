const loginPanel = document.getElementById("login-panel");
const chatPanel = document.getElementById("chat-panel");
const loginForm = document.getElementById("login-form");
const sendForm = document.getElementById("send-form");
const refreshBtn = document.getElementById("refresh-btn");
const logoutBtn = document.getElementById("logout-btn");
const sendBtn = document.getElementById("send-btn");

const serverUrlInput = document.getElementById("server_url");
const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const messageInput = document.getElementById("message-input");

const fileInput = document.getElementById("file-input");
const filePickerBtn = document.getElementById("file-picker-btn");
const selectedFileLabel = document.getElementById("selected-file");
const uploadProgress = document.getElementById("upload-progress");
const uploadProgressBar = document.getElementById("upload-progress-bar");
const uploadProgressText = document.getElementById("upload-progress-text");

const messagesContainer = document.getElementById("messages");
const usersListContainer = document.getElementById("users-list");
const statusText = document.getElementById("status");
const connectedUser = document.getElementById("connected-user");
const connectedServer = document.getElementById("connected-server");
const sidebarUsersSection = document.getElementById("sidebar-users-section");
const sidebarChangePasswordSection = document.getElementById("sidebar-change-password-section");

const changePasswordForm = document.getElementById("change-password-form");
const currentPasswordInput = document.getElementById("current-password");
const newPasswordInput = document.getElementById("new-password");
const confirmPasswordInput = document.getElementById("confirm-password");
const passwordFeedback = document.getElementById("password-feedback");

const replyPreview = document.getElementById("reply-preview");
const replyPreviewAuthor = document.getElementById("reply-preview-author");
const replyPreviewText = document.getElementById("reply-preview-text");
const cancelReplyBtn = document.getElementById("cancel-reply-btn");

const SESSION_KEY = "nexora_session";
const state = {
  serverUrl: "",
  token: "",
  username: "",
  messagePollTimer: null,
  usersPollTimer: null,
  currentReply: null,
  isUploading: false,
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

function summarizeReplyText(content, maxLength = 120) {
  const compact = String(content ?? "").replace(/\s+/g, " ").trim();
  if (compact.length <= maxLength) {
    return compact;
  }
  return `${compact.slice(0, maxLength - 3).trimEnd()}...`;
}

function formatFileSize(sizeBytes) {
  if (!Number.isFinite(sizeBytes) || sizeBytes < 0) {
    return "Unknown size";
  }
  if (sizeBytes < 1024) {
    return `${sizeBytes} B`;
  }
  if (sizeBytes < 1024 * 1024) {
    return `${(sizeBytes / 1024).toFixed(1)} KB`;
  }
  return `${(sizeBytes / (1024 * 1024)).toFixed(2)} MB`;
}

function parseErrorDetail(raw, fallback) {
  if (!raw) {
    return fallback;
  }
  if (typeof raw === "string") {
    return raw;
  }
  if (typeof raw.detail === "string") {
    return raw.detail;
  }
  return fallback;
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

function updateSidebarAuthSections(isLoggedIn) {
  if (sidebarUsersSection) {
    sidebarUsersSection.classList.toggle("hidden", !isLoggedIn);
  }
  if (sidebarChangePasswordSection) {
    sidebarChangePasswordSection.classList.toggle("hidden", !isLoggedIn);
  }
}

function setUploadingState(isUploading) {
  state.isUploading = isUploading;

  if (sendBtn) {
    sendBtn.disabled = isUploading;
  }
  if (filePickerBtn) {
    filePickerBtn.disabled = isUploading;
  }
}

function updateSelectedFileLabel() {
  if (!selectedFileLabel) {
    return;
  }

  const selectedFile = fileInput?.files?.[0] ?? null;
  if (!selectedFile) {
    selectedFileLabel.textContent = "No file selected";
    return;
  }

  selectedFileLabel.textContent = `Attached: ${selectedFile.name} (${formatFileSize(selectedFile.size)})`;
}

function clearSelectedFile() {
  if (fileInput) {
    fileInput.value = "";
  }
  updateSelectedFileLabel();
}

function showUploadProgress() {
  if (uploadProgress) {
    uploadProgress.classList.remove("hidden");
  }
  if (uploadProgressText) {
    uploadProgressText.classList.remove("hidden");
  }
}

function hideUploadProgress() {
  if (uploadProgress) {
    uploadProgress.classList.add("hidden");
  }
  if (uploadProgressText) {
    uploadProgressText.classList.add("hidden");
  }
}

function setUploadProgress(percent, hasRealPercent) {
  showUploadProgress();

  if (uploadProgressBar) {
    uploadProgressBar.classList.toggle("indeterminate", !hasRealPercent);
    uploadProgressBar.style.width = hasRealPercent ? `${percent}%` : "35%";
  }

  if (uploadProgressText) {
    uploadProgressText.textContent = hasRealPercent
      ? `Uploading... ${percent}%`
      : "Uploading...";
  }
}

function resetUploadProgress() {
  if (uploadProgressBar) {
    uploadProgressBar.classList.remove("indeterminate");
    uploadProgressBar.style.width = "0%";
  }
  if (uploadProgressText) {
    uploadProgressText.textContent = "";
  }
  hideUploadProgress();
}

function setReplyTarget(message) {
  if (!message || !Number.isInteger(message.id)) {
    return;
  }

  const previewText = (message.content || "").trim() || (message.file_name ? `[Attachment] ${message.file_name}` : "");

  state.currentReply = {
    id: message.id,
    username: message.username,
    content: previewText,
  };

  if (replyPreview && replyPreviewAuthor && replyPreviewText) {
    replyPreviewAuthor.textContent = message.username;
    replyPreviewText.textContent = `"${summarizeReplyText(previewText || "(empty message)", 160)}"`;
    replyPreview.classList.remove("hidden");
  }

  messageInput.focus();
}

function clearReplyTarget() {
  state.currentReply = null;

  if (replyPreview) {
    replyPreview.classList.add("hidden");
  }
  if (replyPreviewAuthor) {
    replyPreviewAuthor.textContent = "-";
  }
  if (replyPreviewText) {
    replyPreviewText.textContent = "-";
  }
}

function showLogin() {
  updateSidebarAuthSections(false);
  clearReplyTarget();
  clearSelectedFile();
  resetUploadProgress();
  setUploadingState(false);
  loginPanel.classList.remove("hidden");
  chatPanel.classList.add("hidden");
}

function showChat() {
  updateSidebarAuthSections(true);
  loginPanel.classList.add("hidden");
  chatPanel.classList.remove("hidden");
  connectedUser.textContent = state.username;
  connectedServer.textContent = state.serverUrl;
}

function uploadMessageWithProgress(formData) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${state.serverUrl}/api/messages`);
    xhr.setRequestHeader("Authorization", `Bearer ${state.token}`);
    xhr.timeout = 45000;

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && event.total > 0) {
        const percent = Math.min(100, Math.round((event.loaded / event.total) * 100));
        setUploadProgress(percent, true);
      } else {
        setUploadProgress(0, false);
      }
    };

    xhr.onload = () => {
      let data = {};
      if (xhr.responseText) {
        try {
          data = JSON.parse(xhr.responseText);
        } catch (_) {
          data = { detail: xhr.responseText };
        }
      }

      resolve({
        status: xhr.status,
        ok: xhr.status >= 200 && xhr.status < 300,
        data,
      });
    };

    xhr.onerror = () => {
      reject(new Error("Network error during upload"));
    };

    xhr.ontimeout = () => {
      reject(new Error("Upload timed out"));
    };

    xhr.onabort = () => {
      reject(new Error("Upload was cancelled"));
    };

    xhr.send(formData);
  });
}

async function sendMessageWithoutFile(formData) {
  const response = await fetch(`${state.serverUrl}/api/messages`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${state.token}`,
    },
    body: formData,
  });

  const data = await response.json().catch(() => ({}));
  return {
    status: response.status,
    ok: response.ok,
    data,
  };
}

async function downloadMessageFile(message) {
  try {
    const response = await fetch(`${state.serverUrl}/api/uploads/${message.id}`, {
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
      const data = await response.json().catch(() => ({}));
      setStatus(parseErrorDetail(data, "Cannot download file"));
      return;
    }

    const blob = await response.blob();
    const blobUrl = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = blobUrl;
    anchor.download = message.file_name || "download";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(blobUrl);

    setStatus(`Downloaded ${message.file_name || "file"}`);
  } catch (error) {
    setStatus(`Download error: ${error.message}`);
  }
}

function createAttachmentElement(message) {
  if (!message.file_name) {
    return null;
  }

  const attachment = document.createElement("div");
  attachment.className = "message-attachment";

  const meta = document.createElement("div");
  meta.className = "message-attachment-meta";
  meta.textContent = `${message.file_name} (${formatFileSize(message.file_size)})`;

  const downloadBtn = document.createElement("button");
  downloadBtn.type = "button";
  downloadBtn.className = "message-download";
  downloadBtn.textContent = "Download";
  downloadBtn.addEventListener("click", () => {
    void downloadMessageFile(message);
  });

  attachment.appendChild(meta);
  attachment.appendChild(downloadBtn);
  return attachment;
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

  const actions = document.createElement("div");
  actions.className = "message-actions";

  const replyButton = document.createElement("button");
  replyButton.type = "button";
  replyButton.className = "message-reply";
  replyButton.textContent = "Reply";
  replyButton.addEventListener("click", () => {
    setReplyTarget(message);
  });
  actions.appendChild(replyButton);

  // Delete is shown only for messages created by the currently logged-in user.
  if (message.username === state.username) {
    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "message-delete";
    deleteButton.textContent = "Delete";
    deleteButton.addEventListener("click", () => {
      void deleteMessage(message.id);
    });
    actions.appendChild(deleteButton);
  }

  header.appendChild(actions);
  wrapper.appendChild(header);

  if (message.reply_to) {
    const replyContext = document.createElement("div");
    replyContext.className = message.reply_to.deleted
      ? "message-reply-context deleted"
      : "message-reply-context";

    replyContext.textContent = message.reply_to.deleted
      ? `-> Reply to deleted message (${message.reply_to.author})`
      : `-> Reply to ${message.reply_to.author}: "${summarizeReplyText(message.reply_to.content, 90)}"`;

    wrapper.appendChild(replyContext);
  }

  const text = (message.content || "").trim();
  if (text) {
    const body = document.createElement("div");
    body.textContent = text;
    wrapper.appendChild(body);
  }

  const attachment = createAttachmentElement(message);
  if (attachment) {
    wrapper.appendChild(attachment);
  }

  if (!text && !attachment) {
    const empty = document.createElement("div");
    empty.className = "muted";
    empty.textContent = "(empty message)";
    wrapper.appendChild(empty);
  }

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
      setStatus(parseErrorDetail(data, "Login failed"));
      return;
    }

    const data = await response.json();
    state.serverUrl = serverUrl;
    state.token = data.access_token;
    state.username = data.user.username;

    saveSession();
    showChat();
    clearPasswordFeedback();
    clearReplyTarget();
    clearSelectedFile();
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

  if (state.isUploading) {
    return;
  }

  const content = messageInput.value.trim();
  const selectedFile = fileInput?.files?.[0] ?? null;

  if (!content && !selectedFile) {
    setStatus("Write a message or attach a file.");
    return;
  }

  const buildFormData = () => {
    const payload = new FormData();
    payload.append("content", content);

    if (state.currentReply && Number.isInteger(state.currentReply.id)) {
      payload.append("parent_message_id", String(state.currentReply.id));
    }

    if (selectedFile) {
      payload.append("file", selectedFile);
    }

    return payload;
  };

  const hasFileUpload = Boolean(selectedFile);

  setUploadingState(true);
  if (hasFileUpload) {
    setUploadProgress(0, true);
  } else {
    resetUploadProgress();
  }

  try {
    let result;
    if (hasFileUpload) {
      try {
        result = await uploadMessageWithProgress(buildFormData());
      } catch (_) {
        // Fallback for environments where XHR upload may fail (status 0 / CORS / proxy),
        // while regular fetch still works.
        setUploadProgress(0, false);
        if (uploadProgressText) {
          uploadProgressText.textContent = "Retrying upload...";
        }
        result = await sendMessageWithoutFile(buildFormData());
      }
    } else {
      result = await sendMessageWithoutFile(buildFormData());
    }

    if (result.status === 401) {
      setStatus("Session expired. Please login again.");
      await logout(false);
      return;
    }

    if (!result.ok) {
      setStatus(parseErrorDetail(result.data, "Failed to send message"));
      return;
    }

    if (hasFileUpload) {
      setUploadProgress(100, true);
    }

    messageInput.value = "";
    clearSelectedFile();
    clearReplyTarget();
    await fetchMessages();
    await fetchUsersPresence();
    setStatus("Message sent");
  } catch (error) {
    setStatus(`Send error: ${error.message}`);
  } finally {
    setUploadingState(false);
    if (hasFileUpload) {
      setTimeout(resetUploadProgress, 250);
    } else {
      resetUploadProgress();
    }
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
      setStatus(parseErrorDetail(data, "Failed to delete message"));
      return;
    }

    setStatus(parseErrorDetail(data, "Message deleted"));
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
      setPasswordFeedback(parseErrorDetail(data, "Password change failed."), true);
      return;
    }

    changePasswordForm.reset();
    setPasswordFeedback(parseErrorDetail(data, "Password changed successfully"), false);
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
  clearReplyTarget();
  clearSelectedFile();
  resetUploadProgress();
  setUploadingState(false);
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
      clearReplyTarget();
      clearSelectedFile();
      resetUploadProgress();
      setUploadingState(false);
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

if (filePickerBtn && fileInput) {
  filePickerBtn.addEventListener("click", () => {
    fileInput.click();
  });
}
if (fileInput) {
  fileInput.addEventListener("change", updateSelectedFileLabel);
}
if (messageInput && sendForm) {
  messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      if (typeof sendForm.requestSubmit === "function") {
        sendForm.requestSubmit(sendBtn || undefined);
      } else if (sendBtn) {
        sendBtn.click();
      }
    }
  });
}
if (cancelReplyBtn) {
  cancelReplyBtn.addEventListener("click", clearReplyTarget);
}
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

updateSelectedFileLabel();
resetUploadProgress();
setUploadingState(false);
void tryRestoreSession();

