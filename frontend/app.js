const storageKeys = {
  apiBase: "motion-console-api-base",
  token: "motion-console-token",
  username: "motion-console-username",
};

const apiBaseInput = document.getElementById("api-base");
const consoleOutput = document.getElementById("console-output");
const activeUser = document.getElementById("active-user");
const statusJobIdInput = document.getElementById("status-job-id");
const jobsList = document.getElementById("jobs-list");
const statusMetrics = document.getElementById("status-metrics");

apiBaseInput.value = localStorage.getItem(storageKeys.apiBase) || apiBaseInput.value;
activeUser.textContent = localStorage.getItem(storageKeys.username) || "none";

function logLine(title, payload) {
  const block = typeof payload === "string" ? payload : JSON.stringify(payload, null, 2);
  consoleOutput.textContent = `[${new Date().toLocaleTimeString()}] ${title}\n${block}\n\n${consoleOutput.textContent}`.trim();
}

function getApiBase() {
  return apiBaseInput.value.replace(/\/$/, "");
}

function getToken() {
  return localStorage.getItem(storageKeys.token);
}

function setAuthState(username, token) {
  if (username) {
    localStorage.setItem(storageKeys.username, username);
    activeUser.textContent = username;
  }
  if (token) {
    localStorage.setItem(storageKeys.token, token);
  }
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
  const data = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    throw new Error(typeof data === "string" ? data : data.error || data.detail || "Request failed");
  }

  return data;
}

function renderStatus(data) {
  statusMetrics.innerHTML = `
    <div><dt>Status</dt><dd>${data.status}</dd></div>
    <div><dt>Provider</dt><dd>${data.provider}</dd></div>
    <div><dt>Progress</dt><dd>${data.progress}%</dd></div>
    <div><dt>Video</dt><dd>${data.video_url ? `<a href="${data.video_url}" target="_blank" rel="noreferrer">open output</a>` : "not ready"}</dd></div>
  `;
}

function renderJobs(items) {
  if (!items.length) {
    jobsList.innerHTML = "<p>No jobs yet.</p>";
    return;
  }

  jobsList.innerHTML = items.map((job) => `
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

document.getElementById("save-base").addEventListener("click", () => {
  localStorage.setItem(storageKeys.apiBase, getApiBase());
  logLine("Saved backend endpoint", { apiBase: getApiBase() });
});

document.getElementById("clear-token").addEventListener("click", () => {
  localStorage.removeItem(storageKeys.token);
  localStorage.removeItem(storageKeys.username);
  activeUser.textContent = "none";
  logLine("Cleared auth state", "Token removed from localStorage.");
});

document.getElementById("register-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = Object.fromEntries(form.entries());

  try {
    const data = await apiFetch("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setAuthState(data.username);
    logLine("Registered user", data);
  } catch (error) {
    logLine("Register failed", error.message);
  }
});

document.getElementById("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = Object.fromEntries(form.entries());

  try {
    const data = await apiFetch("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setAuthState(payload.username, data.access_token);
    logLine("Logged in", { username: payload.username, token_type: data.token_type });
  } catch (error) {
    logLine("Login failed", error.message);
  }
});

document.getElementById("me-button").addEventListener("click", async () => {
  try {
    const data = await apiFetch("/auth/me");
    setAuthState(data.username);
    logLine("Fetched current user", data);
  } catch (error) {
    logLine("Auth check failed", error.message);
  }
});

document.getElementById("generate-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = Object.fromEntries(form.entries());
  payload.duration = Number(payload.duration);
  if (!payload.image_url) {
    delete payload.image_url;
  }

  try {
    const data = await apiFetch("/api/v1/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    statusJobIdInput.value = data.job_id;
    logLine("Generation started", data);
  } catch (error) {
    logLine("Generation failed", error.message);
  }
});

document.getElementById("status-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const jobId = form.get("job_id");

  try {
    const data = await apiFetch(`/api/v1/status/${jobId}`);
    renderStatus(data);
    logLine("Status response", data);
  } catch (error) {
    logLine("Status failed", error.message);
  }
});

document.getElementById("load-jobs").addEventListener("click", async () => {
  try {
    const data = await apiFetch("/api/v1/jobs");
    renderJobs(data);
    logLine("Loaded jobs", data);
  } catch (error) {
    logLine("Load jobs failed", error.message);
  }
});
