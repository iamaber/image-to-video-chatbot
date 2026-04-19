const STORAGE_KEYS = {
  apiBase: "motion-console-api-base",
  token: "motion-console-token",
  username: "motion-console-username",
};

const elements = {
  apiBaseInput: document.getElementById("api-base"),
  consoleOutput: document.getElementById("console-output"),
  activeUser: document.getElementById("active-user"),
  statusJobIdInput: document.getElementById("status-job-id"),
  jobsList: document.getElementById("jobs-list"),
  statusMetrics: document.getElementById("status-metrics"),
  saveBaseButton: document.getElementById("save-base"),
  clearTokenButton: document.getElementById("clear-token"),
  registerForm: document.getElementById("register-form"),
  loginForm: document.getElementById("login-form"),
  meButton: document.getElementById("me-button"),
  generateForm: document.getElementById("generate-form"),
  statusForm: document.getElementById("status-form"),
  loadJobsButton: document.getElementById("load-jobs"),
};

bootstrapUi();
bindEvents();

function bootstrapUi() {
  elements.apiBaseInput.value = getStoredValue(STORAGE_KEYS.apiBase) || elements.apiBaseInput.value;
  elements.activeUser.textContent = getStoredValue(STORAGE_KEYS.username) || "none";
}

function bindEvents() {
  elements.saveBaseButton.addEventListener("click", saveApiBase);
  elements.clearTokenButton.addEventListener("click", clearAuthState);
  elements.registerForm.addEventListener("submit", handleRegister);
  elements.loginForm.addEventListener("submit", handleLogin);
  elements.meButton.addEventListener("click", handleFetchCurrentUser);
  elements.generateForm.addEventListener("submit", handleGenerate);
  elements.statusForm.addEventListener("submit", handleStatusCheck);
  elements.loadJobsButton.addEventListener("click", handleLoadJobs);
}

function getStoredValue(key) {
  return localStorage.getItem(key);
}

function setStoredValue(key, value) {
  localStorage.setItem(key, value);
}

function removeStoredValue(key) {
  localStorage.removeItem(key);
}

function getApiBase() {
  return elements.apiBaseInput.value.trim().replace(/\/$/, "");
}

function getToken() {
  return getStoredValue(STORAGE_KEYS.token);
}

function setActiveUser(username) {
  elements.activeUser.textContent = username || "none";
}

function saveAuthState({ username, token }) {
  if (username) {
    setStoredValue(STORAGE_KEYS.username, username);
    setActiveUser(username);
  }

  if (token) {
    setStoredValue(STORAGE_KEYS.token, token);
  }
}

function clearStoredAuthState() {
  removeStoredValue(STORAGE_KEYS.token);
  removeStoredValue(STORAGE_KEYS.username);
  setActiveUser(null);
}

function formToObject(formElement) {
  return Object.fromEntries(new FormData(formElement).entries());
}

function logLine(title, payload) {
  const block = typeof payload === "string" ? payload : JSON.stringify(payload, null, 2);
  elements.consoleOutput.textContent = `[${new Date().toLocaleTimeString()}] ${title}\n${block}\n\n${elements.consoleOutput.textContent}`.trim();
}

async function apiFetch(path, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("Accept", "application/json");

  if (options.body && !headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${getApiBase()}${path}`, {
    ...options,
    headers,
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    throw new Error(typeof payload === "string" ? payload : payload.error || payload.detail || "Request failed");
  }

  return payload;
}

function renderStatus(data) {
  elements.statusMetrics.innerHTML = `
    <div><dt>Status</dt><dd>${data.status}</dd></div>
    <div><dt>Provider</dt><dd>${data.provider}</dd></div>
    <div><dt>Progress</dt><dd>${data.progress}%</dd></div>
    <div><dt>Video</dt><dd>${data.video_url ? `<a href="${data.video_url}" target="_blank" rel="noreferrer">open output</a>` : "not ready"}</dd></div>
  `;
}

function renderJobs(items) {
  if (!items.length) {
    elements.jobsList.innerHTML = "<p>No jobs yet.</p>";
    return;
  }

  elements.jobsList.innerHTML = items.map((job) => `
    <article class="job-row">
      <div class="label">${job.provider}</div>
      <div>
        <div class="prompt">${job.prompt}</div>
        <div class="meta">${job.job_id}</div>
      </div>
      <div>
        <div>${job.status}</div>
        <div class="meta">${job.duration}s</div>
      </div>
    </article>
  `).join("");
}

function saveApiBase() {
  setStoredValue(STORAGE_KEYS.apiBase, getApiBase());
  logLine("Saved backend endpoint", { apiBase: getApiBase() });
}

function clearAuthState() {
  clearStoredAuthState();
  logLine("Cleared auth state", "Token removed from localStorage.");
}

async function handleRegister(event) {
  event.preventDefault();
  const payload = formToObject(event.currentTarget);

  try {
    const data = await apiFetch("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    saveAuthState({ username: data.username });
    logLine("Registered user", data);
  } catch (error) {
    logLine("Register failed", error.message);
  }
}

async function handleLogin(event) {
  event.preventDefault();
  const payload = formToObject(event.currentTarget);

  try {
    const data = await apiFetch("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    saveAuthState({ username: payload.username, token: data.access_token });
    logLine("Logged in", { username: payload.username, token_type: data.token_type });
  } catch (error) {
    logLine("Login failed", error.message);
  }
}

async function handleFetchCurrentUser() {
  try {
    const data = await apiFetch("/auth/me");
    saveAuthState({ username: data.username });
    logLine("Fetched current user", data);
  } catch (error) {
    logLine("Auth check failed", error.message);
  }
}

function buildGenerationPayload(formElement) {
  const payload = formToObject(formElement);
  payload.duration = Number(payload.duration);

  if (!payload.image_url) {
    throw new Error("image_url required for free Stable Video Diffusion provider.");
  }

  return payload;
}

async function handleGenerate(event) {
  event.preventDefault();

  try {
    const payload = buildGenerationPayload(event.currentTarget);
    const data = await apiFetch("/api/v1/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    elements.statusJobIdInput.value = data.job_id;
    logLine("Generation started", data);
  } catch (error) {
    logLine("Generation failed", error.message);
  }
}

async function handleStatusCheck(event) {
  event.preventDefault();
  const { job_id: jobId } = formToObject(event.currentTarget);

  try {
    const data = await apiFetch(`/api/v1/status/${jobId}`);
    renderStatus(data);
    logLine("Status response", data);
  } catch (error) {
    logLine("Status failed", error.message);
  }
}

async function handleLoadJobs() {
  try {
    const data = await apiFetch("/api/v1/jobs");
    renderJobs(data);
    logLine("Loaded jobs", data);
  } catch (error) {
    logLine("Load jobs failed", error.message);
  }
}
