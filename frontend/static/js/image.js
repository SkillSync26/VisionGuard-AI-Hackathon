const file = document.getElementById("file");
const run = document.getElementById("run");
const preview = document.getElementById("preview");
const results = document.getElementById("results");
const status = document.getElementById("status");
const download = document.getElementById("download");

run.onclick = async () => {
  if (!file.files[0]) return alert("Choose an image first.");
  const form = new FormData();
  form.append("file", file.files[0]);
  run.disabled = true; status.textContent = "Running YOLO inference...";
  try {
    const res = await fetch("/detect/image", {method:"POST", body:form});
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Detection failed");
    preview.src = data.download_url;
    results.textContent = JSON.stringify({
      total_objects: data.statistics.total_objects,
      average_confidence: `${(data.statistics.average_confidence*100).toFixed(1)}%`,
      counts: data.statistics.counts
    }, null, 2);
    download.href = data.download_url;
    download.classList.remove("hidden");
    status.textContent = "Complete.";
  } catch(e) { status.textContent = e.message; }
  finally { run.disabled = false; }
};
