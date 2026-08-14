async function loadDashboard(){
  const res = await fetch("/statistics"); const data = await res.json();
  document.getElementById("total").textContent = data.total_detections;
  document.getElementById("avg").textContent = `${(data.average_confidence*100).toFixed(1)}%`;
  document.getElementById("alerts").textContent = data.total_alerts;

  new Chart(document.getElementById("classChart"), {
    type:"bar",
    data:{labels:data.by_class.map(x=>x.class),datasets:[{label:"Detections",data:data.by_class.map(x=>x.count)}]},
    options:{responsive:true,plugins:{legend:{display:false}}}
  });
  new Chart(document.getElementById("sourceChart"), {
    type:"doughnut",
    data:{labels:data.by_source.map(x=>x.source),datasets:[{data:data.by_source.map(x=>x.count)}]},
    options:{responsive:true}
  });
}
loadDashboard();
