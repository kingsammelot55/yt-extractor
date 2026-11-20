const $ = (id) => document.getElementById(id);
const statusBox = $("status");
const details = $("details");

function settings() {
  const backend = $("backend").value.trim().replace(/\/+$/, "");
  const key = $("key").value.trim();
  const url = $("url").value.trim();
  const format = document.querySelector('input[name="format"]:checked').value;
  if (!backend || !/^https?:\/\//i.test(backend)) throw new Error("Enter a valid backend URL, including https://.");
  if (!key) throw new Error("Enter your backend API key.");
  if (!url || !/^https?:\/\//i.test(url)) throw new Error("Paste a valid video URL beginning with http:// or https://.");
  return { backend, key, url, format };
}

async function api(path, data) {
  const s = settings();
  const response = await fetch(s.backend + path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-API-Key": s.key },
    body: JSON.stringify(data)
  });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { message = (await response.json()).detail || message; } catch {}
    throw new Error(message);
  }
  return response;
}

$("info").addEventListener("click", async () => {
  try {
    const s = settings();
    setBusy(true, "Looking up video information…");
    details.hidden = true;
    const response = await api("/api/info", { url: s.url, format: s.format });
    const info = await response.json();
    details.replaceChildren();
    if (info.thumbnail) {
      const img = document.createElement("img");
      img.src = info.thumbnail;
      img.alt = "Video thumbnail";
      details.append(img);
    }
    const title = document.createElement("strong");
    title.textContent = info.title;
    details.append(title);
    if (info.duration) {
      const duration = document.createElement("div");
      duration.textContent = `Duration: ${Math.round(info.duration)} seconds`;
      details.append(duration);
    }
    details.hidden = false;
    setBusy(false, "Video information loaded.");
  } catch (error) { setBusy(false, error.message); }
});

$("download").addEventListener("click", async () => {
  try {
    const s = settings();
    setBusy(true, "Preparing your file. This can take a little while…");
    const response = await api("/api/download", { url: s.url, format: s.format });
    const blob = await response.blob();
    const disposition = response.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="?([^";]+)"?/i);
    const filename = match ? match[1] : `download.${s.format}`;
    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = objectUrl;
    a.download = filename;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 30000);
    setBusy(false, "Download started.");
  } catch (error) { setBusy(false, error.message); }
});

function setBusy(busy, message) {
  $("info").disabled = busy;
  $("download").disabled = busy;
  statusBox.textContent = message;
}