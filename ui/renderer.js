const BACKEND_URL = "http://localhost:5050";

const els = {
  publicKeyText: document.getElementById("publicKeyText"),
  fingerprint: document.getElementById("fingerprint"),
  comment: document.getElementById("comment"),
  passphrase: document.getElementById("passphrase"),
  generateBtn: document.getElementById("generateBtn"),
  loadInput: document.getElementById("loadInput"),
  savePublicBtn: document.getElementById("savePublicBtn"),
  savePrivateBtn: document.getElementById("savePrivateBtn"),
  paramNote: document.getElementById("paramNote"),
  statusText: document.getElementById("statusText"),
  statusbar: document.querySelector(".statusbar"),
  tabBtns: document.querySelectorAll(".tab-btn"),
  sshHost: document.getElementById("sshHost"),
  sshPort: document.getElementById("sshPort"),
  sshUsername: document.getElementById("sshUsername"),
  sshTimeout: document.getElementById("sshTimeout"),
  sshKeyInput: document.getElementById("sshKeyInput"),
  sshKeyFileName: document.getElementById("sshKeyFileName"),
  testConnectionBtn: document.getElementById("testConnectionBtn"),
  sshTestResult: document.getElementById("sshTestResult"),
  refreshKeyUsageBtn: document.getElementById("refreshKeyUsageBtn"),
  keyUsageBody: document.getElementById("keyUsageBody"),
};

const PARAM_NOTES = {
  rsa: "RSA — 4096 bits (fixed by the server)",
  ecdsa: "ECDSA — SECP256k1 curve (fixed by the server)",
  ed25519: "ED25519 — fixed key size, no parameters to choose",
};

// in-memory state for whatever key is currently loaded/generated
const state = {
  keyType: null,
  privateBytes: null, // Uint8Array, only present after Generate
  originalFileBytes: null, // Uint8Array, only present after Load
  originalFileName: null,
};

function setStatus(message, kind) {
  els.statusText.textContent = message;
  els.statusbar.classList.remove("error", "success");
  if (kind) els.statusbar.classList.add(kind);
}

function selectedKeyType() {
  const checked = document.querySelector('input[name="keyType"]:checked');
  return checked ? checked.value : "rsa";
}

document.querySelectorAll('input[name="keyType"]').forEach((radio) => {
  radio.addEventListener("change", () => {
    els.paramNote.textContent = PARAM_NOTES[selectedKeyType()];
  });
});

function base64ToBytes(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

async function computeFingerprint(publicKeyLine) {
  const parts = publicKeyLine.trim().split(/\s+/);
  if (parts.length < 2) return null;

  const keyBytes = base64ToBytes(parts[1]);
  const digest = await crypto.subtle.digest("SHA-256", keyBytes);
  const digestBytes = new Uint8Array(digest);

  let binary = "";
  digestBytes.forEach((b) => (binary += String.fromCharCode(b)));
  const b64 = btoa(binary).replace(/=+$/, "");

  return `SHA256:${b64}`;
}

async function refreshFingerprint() {
  const text = els.publicKeyText.value.trim();
  if (!text) {
    els.fingerprint.value = "";
    return;
  }
  try {
    els.fingerprint.value = await computeFingerprint(text);
  } catch (_err) {
    els.fingerprint.value = "unable to compute";
  }
}

function enableSaveButtons({ pub, priv }) {
  els.savePublicBtn.disabled = !pub;
  els.savePrivateBtn.disabled = !priv;
}

function extractCommentFromLine(publicKeyLine) {
  const parts = publicKeyLine.trim().split(/\s+/);
  return parts.length >= 3 ? parts.slice(2).join(" ") : "";
}

els.generateBtn.addEventListener("click", async () => {
  const keyType = selectedKeyType();
  const comment = els.comment.value.trim();

  setStatus("Generating key…");
  els.generateBtn.disabled = true;

  try {
    const res = await fetch(`${BACKEND_URL}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key_type: keyType, comment }),
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error || `Server returned ${res.status}`);
    }

    const zipBlob = await res.blob();
    const zip = await JSZip.loadAsync(zipBlob);

    const privateEntry = Object.values(zip.files).find((f) => !f.name.endsWith(".pub"));
    const publicEntry = Object.values(zip.files).find((f) => f.name.endsWith(".pub"));

    if (!privateEntry || !publicEntry) {
      throw new Error("Server response was missing a key file.");
    }

    state.keyType = keyType;
    state.privateBytes = await privateEntry.async("uint8array");
    state.originalFileBytes = null;
    state.originalFileName = null;

    const publicText = await publicEntry.async("text");
    els.publicKeyText.value = publicText.trim();
    if (!comment) {
      els.comment.value = extractCommentFromLine(publicText);
    }

    await refreshFingerprint();
    enableSaveButtons({ pub: true, priv: true });
    setStatus(`Generated a new ${keyType.toUpperCase()} key pair.`, "success");
  } catch (err) {
    setStatus(`Couldn't generate a key: ${err.message}`, "error");
  } finally {
    els.generateBtn.disabled = false;
  }
});


els.loadInput.addEventListener("change", async () => {
  const file = els.loadInput.files[0];
  if (!file) return;

  setStatus(`Loading ${file.name}…`);

  try {
    const arrayBuffer = await file.arrayBuffer();
    state.originalFileBytes = new Uint8Array(arrayBuffer);
    state.originalFileName = file.name;
    state.privateBytes = null;

    const formData = new FormData();
    formData.append("file", file);
    if (els.passphrase.value) formData.append("password", els.passphrase.value);

    const res = await fetch(`${BACKEND_URL}/upload`, {
      method: "POST",
      body: formData,
    });

    const body = await res.json();
    if (!res.ok) {
      throw new Error(body.error || `Server returned ${res.status}`);
    }

    state.keyType = body.key_type.toLowerCase();
    els.publicKeyText.value = body.public_key.trim();
    els.comment.value = extractCommentFromLine(body.public_key);

    await refreshFingerprint();
    enableSaveButtons({ pub: true, priv: true });
    setStatus(`Loaded a ${body.key_type} key from ${file.name}.`, "success");
  } catch (err) {
    setStatus(`Couldn't load that key: ${err.message}`, "error");
    state.originalFileBytes = null;
    state.originalFileName = null;
  } finally {
    els.loadInput.value = "";
  }
});

els.savePublicBtn.addEventListener("click", async () => {
  const currentText = els.publicKeyText.value.trim();
  if (!currentText) return;

  setStatus("Saving public key…");

  try {
    const formData = new FormData();
    formData.append("file", new Blob([currentText], { type: "text/plain" }), "key.pub");
    formData.append("comment", els.comment.value.trim() || "MacPuTTY");

    const res = await fetch(`${BACKEND_URL}/comment`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error || `Server returned ${res.status}`);
    }

    const updatedText = await res.text();
    els.publicKeyText.value = updatedText.trim();

    const bytes = new TextEncoder().encode(updatedText);
    const suggestedName = `id_${state.keyType || "key"}.pub`;
    const result = await window.electronAPI.saveFile(suggestedName, bytes);

    if (result.canceled) {
      setStatus("Save canceled.");
    } else {
      setStatus(`Saved public key to ${result.filePath}`, "success");
    }
  } catch (err) {
    setStatus(`Couldn't save the public key: ${err.message}`, "error");
  }
});


els.savePrivateBtn.addEventListener("click", async () => {
  const bytes = state.privateBytes || state.originalFileBytes;
  if (!bytes) return;

  const suggestedName = state.originalFileName || `id_${state.keyType || "key"}`;

  setStatus("Saving private key…");

  try {
    const result = await window.electronAPI.saveFile(suggestedName, bytes);
    if (result.canceled) {
      setStatus("Save canceled.");
    } else {
      setStatus(`Saved private key to ${result.filePath}`, "success");
    }
  } catch (err) {
    setStatus(`Couldn't save the private key: ${err.message}`, "error");
  }
});


els.publicKeyText.addEventListener("input", refreshFingerprint);

// ---------- Tabs ----------

els.tabBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    els.tabBtns.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");

    document.getElementById("tab-keygen").classList.add("hidden");
    document.getElementById("tab-sshtest").classList.add("hidden");
    document.getElementById("tab-keyusage").classList.add("hidden");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.remove("hidden");

    if (btn.dataset.tab === "keyusage") loadKeyUsage();
  });
});

// ---------- SSH connection test ----------

const sshState = {
  keyFile: null,
};

function refreshTestConnectionBtn() {
  els.testConnectionBtn.disabled = !(
    els.sshHost.value.trim() &&
    els.sshPort.value.trim() &&
    els.sshUsername.value.trim() &&
    sshState.keyFile
  );
}

[els.sshHost, els.sshPort, els.sshUsername].forEach((input) => {
  input.addEventListener("input", refreshTestConnectionBtn);
});

els.sshKeyInput.addEventListener("change", () => {
  const file = els.sshKeyInput.files[0];
  sshState.keyFile = file || null;
  els.sshKeyFileName.textContent = file ? file.name : "No private key file selected";
  refreshTestConnectionBtn();
});

els.testConnectionBtn.addEventListener("click", async () => {
  els.sshTestResult.textContent = "";
  setStatus("Testing SSH connection…");
  els.testConnectionBtn.disabled = true;

  try {
    const formData = new FormData();
    formData.append("host", els.sshHost.value.trim());
    formData.append("port", els.sshPort.value.trim());
    formData.append("username", els.sshUsername.value.trim());
    formData.append("timeout", els.sshTimeout.value.trim() || "5");
    formData.append("file", sshState.keyFile);

    const res = await fetch(`${BACKEND_URL}/test-connection`, {
      method: "POST",
      body: formData,
    });

    const body = await res.json();
    if (!res.ok) {
      throw new Error(body.error || `Server returned ${res.status}`);
    }

    if (body.success) {
      els.sshTestResult.textContent = "Connection succeeded.";
      setStatus("SSH connection succeeded.", "success");
    } else {
      els.sshTestResult.textContent = `Connection failed: ${body.error}`;
      setStatus("SSH connection failed.", "error");
    }
  } catch (err) {
    els.sshTestResult.textContent = `Connection failed: ${err.message}`;
    setStatus(`Couldn't test the connection: ${err.message}`, "error");
  } finally {
    refreshTestConnectionBtn();
  }
});

function emptyStateRow(message) {
  els.keyUsageBody.innerHTML = "";
  const tr = document.createElement("tr");
  const td = document.createElement("td");
  td.colSpan = 4;
  td.className = "empty-state";
  td.textContent = message;
  tr.appendChild(td);
  els.keyUsageBody.appendChild(tr);
}

function renderKeyUsage(data) {
  els.keyUsageBody.innerHTML = "";

  if (!data.config_exists) {
    emptyStateRow(`No SSH config file found at ${data.config_path}`);
    return;
  }

  if (data.hosts.length === 0) {
    emptyStateRow("Config file found, but no Host entries are defined.");
    return;
  }

  data.hosts.forEach((h) => {
    const tr = document.createElement("tr");

    const hostTd = document.createElement("td");
    hostTd.textContent = h.host;
    tr.appendChild(hostTd);

    const hostnameTd = document.createElement("td");
    hostnameTd.textContent = h.port ? `${h.hostname}:${h.port}` : h.hostname;
    tr.appendChild(hostnameTd);

    const userTd = document.createElement("td");
    userTd.textContent = h.user || "—";
    tr.appendChild(userTd);

    const keysTd = document.createElement("td");
    keysTd.className = "mono";
    if (h.identity_files.length === 0) {
      const span = document.createElement("span");
      span.className = "field-hint";
      span.textContent = "none configured";
      keysTd.appendChild(span);
    } else {
      h.identity_files.forEach((f) => {
        const div = document.createElement("div");
        div.className = f.exists ? "key-ok" : "key-missing";
        div.textContent = `${f.exists ? "✓" : "✗"} ${f.path}`;
        keysTd.appendChild(div);
      });
    }
    tr.appendChild(keysTd);

    els.keyUsageBody.appendChild(tr);
  });
}

async function loadKeyUsage() {
  setStatus("Loading SSH config usage…");
  try {
    const res = await fetch(`${BACKEND_URL}/ssh-config-usage`);
    const body = await res.json();
    if (!res.ok) {
      throw new Error(body.error || `Server returned ${res.status}`);
    }

    renderKeyUsage(body);
    setStatus(
      `Loaded ${body.hosts.length} host${body.hosts.length === 1 ? "" : "s"} from ${body.config_path}`,
      "success"
    );
  } catch (err) {
    emptyStateRow(`Couldn't load SSH config usage: ${err.message}`);
    setStatus(`Couldn't load SSH config usage: ${err.message}`, "error");
  }
}

els.refreshKeyUsageBtn.addEventListener("click", loadKeyUsage);