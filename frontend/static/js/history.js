const rows = document.getElementById("rows");
async function load(){
  const params = new URLSearchParams();
  if(document.getElementById("date").value) params.set("date", document.getElementById("date").value);
  if(document.getElementById("type").value) params.set("object_type", document.getElementById("type").value);
  if(document.getElementById("source").value) params.set("source", document.getElementById("source").value);
  const res = await fetch("/detections?limit=500&"+params.toString());
  const data = await res.json();
  rows.innerHTML = data.items.map(x=>`<tr>
    <td>${x.timestamp}</td><td>${x.object_class}</td>
    <td>${(x.confidence*100).toFixed(1)}%</td><td>${x.source}</td>
    <td>${x.track_id ?? "-"}</td><td>${x.alert_status || "-"}</td>
  </tr>`).join("") || `<tr><td colspan="6">No detections found.</td></tr>`;
}
document.getElementById("filter").onclick=load;
document.getElementById("clear").onclick=async()=>{
  if(confirm("Delete all detection history and alerts?")){
    await fetch("/history",{method:"DELETE"}); load();
  }
};
load();
