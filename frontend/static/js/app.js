async function api(url, options={}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try { const data = await res.json(); message = data.detail || message; } catch {}
    throw new Error(message);
  }
  return res.json();
}
