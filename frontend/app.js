const STORAGE_KEYS = {
  apiBase: "motion-console-api-base",
};

const elements = {
  apiBaseInput: document.getElementById("api-base"),
  saveBaseButton: document.getElementById("save-base"),
  backendResult: document.getElementById("backend-result"),
  generateForm: document.getElementById("generate-form"),
  generateResult: document.getElementById("generate-result"),
};

init();

function init() {
  const savedBase = localStorage.getItem(STORAGE_KEYS.apiBase);

  if (savedBase) {
    elements.apiBaseInput.value = savedBase;
  }

  elements.saveBaseButton.addEventListener("click", handleSaveBase);
  elements.generateForm.addEventListener("submit", handleGenerate);
}

function getApiBase() {
  return elements.apiBaseInput.value.trim().replace(/\/$/, "");
}

function setText(el, text, isError = false) {
  el.textContent = text;
  el.classList.toggle("error", isError);
}

function handleSaveBase() {
  const base = getApiBase();
  localStorage.setItem(STORAGE_KEYS.apiBase, base);
  setText(elements.backendResult, `Saved API URL: ${base}`);
}

async function apiFetch(path, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("Accept", "application/json");

  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
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

function formDataToObject(form) {
  return Object.fromEntries(new FormData(form).entries());
}

async function handleGenerate(event) {
  event.preventDefault();
  const payload = formDataToObject(event.currentTarget);
  payload.duration = Number(payload.duration);

  try {
    const data = await apiFetch("/api/v1/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    const videoPart = data.video_url ? ` | Video: ${data.video_url}` : "";
    setText(
      elements.generateResult,
      `Generation ${data.status}${videoPart}`,
    );
  } catch (error) {
    setText(elements.generateResult, `Generation failed: ${error.message}`, true);
  }
}
