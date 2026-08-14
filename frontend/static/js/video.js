const file = document.getElementById("file");
const run = document.getElementById("run");
const status = document.getElementById("status");
const result = document.getElementById("result");
const stats = document.getElementById("stats");
const download = document.getElementById("download");

run.onclick = async () => {
  if (!file.files[0]) return alert("Choose a video first.");
  const form = new FormData(); form.append("file", file.files[0]);
  run.disabled = true; status.textContent = "Processing video frame-by-frame. This may take a while...";
  try {
    const res = await fetch("/detect/video", {method:"POST",body:form});
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Video processing failed");
    stats.textContent = JSON.stringify(data.result, null, 2);
    download.href = data.download_url;
    result.classList.remove("hidden");
    status.textContent = "Complete.";
  } catch(e) { status.textContent = e.message; }
  finally { run.disabled = false; }
};
