const state = {
  board: null,
  job: null,
  vehicle: null,
  ask: null,
};

function tone(label) {
  if (label === "Assign") return { bg: "#16352c", fg: "#b7f0d2", ring: "#3dcc8a" };
  if (label === "Refuse" || label === "Off desk") return { bg: "#3a1d1d", fg: "#f4c2c0", ring: "#e24b4b" };
  if (label === "Undo") return { bg: "#2a2416", fg: "#f3e0b0", ring: "#e8a317" };
  return { bg: "#1c2a32", fg: "#e7edf2", ring: "#3a5360" };
}

function statusTone(status) {
  if (status === "free") return { bg: "#16352c", fg: "#3dcc8a" };
  if (status === "busy") return { bg: "#2a2416", fg: "#e8a317" };
  if (status === "red") return { bg: "#3a1d1d", fg: "#e24b4b" };
  return { bg: "#1c2a32", fg: "#9aa8b0" };
}

function $(id) {
  return document.getElementById(id);
}

function statusLabel(status) {
  if (status === "red") return "Out of service";
  if (status === "busy") return "Busy";
  if (status === "free") return "Free";
  return status || "";
}

function renderLists() {
  const board = state.board;
  const jobs = $("job-list");
  jobs.innerHTML = "";
  for (const job of board.jobs) {
    const rec = job.id === board.selected_job ? board.recommendation : null;
    const label = rec ? rec.decision : "Open";
    const t = tone(label);
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = job.id === board.selected_job ? "on" : "off";
    btn.innerHTML = `
      <div class="row">
        <span class="mono">${job.id}</span>
        <span class="badge" style="background:${t.bg};color:${t.fg}">${label}</span>
      </div>
      <p class="who">${job.city}</p>
      <p class="proc">${job.km} km</p>
    `;
    btn.addEventListener("click", () => loadBoard(job.id, null));
    const li = document.createElement("li");
    li.appendChild(btn);
    jobs.appendChild(li);
  }

  const vehicles = $("vehicle-list");
  vehicles.innerHTML = "";
  for (const row of board.vehicles) {
    const st = statusTone(row.status);
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = row.id === board.selected_vehicle ? "on" : "off";
    btn.innerHTML = `
      <div class="row">
        <span class="mono">${row.id}</span>
        <span class="badge" style="background:${st.bg};color:${st.fg}">${statusLabel(row.status)}</span>
      </div>
      <p class="proc">hours_ok ${row.hours_ok ? "true" : "false"} · range ${row.range_km} km</p>
    `;
    btn.addEventListener("click", () => loadBoard(board.selected_job, row.id));
    const li = document.createElement("li");
    li.appendChild(btn);
    vehicles.appendChild(li);
  }
}

function renderMap() {
  const board = state.board;
  const rec = board.recommendation;
  $("city-cluj").classList.toggle("on", rec.city === "Cluj");
  $("city-oradea").classList.toggle("on", rec.city === "Oradea");
  const dots = $("truck-dots");
  while (dots.firstChild) dots.removeChild(dots.firstChild);
  const places = { "T-11": [300, 132], "T-12": [186, 70], "T-14": [70, 132] };
  const svg = "http://www.w3.org/2000/svg";
  for (const row of board.vehicles) {
    const [x, y] = places[row.id] || [200, 90];
    const color = row.status === "red" ? "#e24b4b" : row.status === "busy" ? "#e8a317" : "#3dcc8a";
    const circle = document.createElementNS(svg, "circle");
    circle.setAttribute("cx", String(x));
    circle.setAttribute("cy", String(y));
    circle.setAttribute("r", row.id === board.selected_vehicle ? "9" : "6");
    circle.setAttribute("fill", color);
    const label = document.createElementNS(svg, "text");
    label.setAttribute("x", String(x + 12));
    label.setAttribute("y", String(y + 4));
    label.setAttribute("class", "truck");
    label.setAttribute("fill", color);
    label.textContent = row.id;
    dots.appendChild(circle);
    dots.appendChild(label);
  }
}

function renderCase() {
  const board = state.board;
  const rec = board.recommendation;
  const t = tone(rec.decision);
  $("case-id").textContent = rec.job_id || "";
  $("case-name").textContent = rec.city || "";
  $("case-sub").textContent = rec.vehicle_id
    ? `${rec.km} km · vehicle ${rec.vehicle_id}`
    : `${rec.km || ""} km`;
  const card = $("decision-card");
  card.style.background = t.bg;
  card.style.color = t.fg;
  $("case-decision").textContent = rec.decision === "Assign" ? `Assign ${rec.vehicle_id}` : rec.decision;
  $("case-rule").textContent = rec.rule || "";
  $("quote-from").textContent = rec.rule ? `Quoted from ${rec.rule}` : "Off desk";
  $("quote").textContent = rec.quote || rec.reason;
  const quoteBox = $("quote-box");
  quoteBox.style.background = t.bg;
  quoteBox.style.color = t.fg;
  quoteBox.style.borderLeftColor = t.ring;
  $("confirm-btn").disabled = !board.can_send;
  $("undo-btn").disabled = !board.can_undo;
  $("action-hint").textContent = board.can_send
    ? "Dispatcher must confirm before this assignment is sent."
    : rec.decision === "Refuse"
      ? "Nothing to send. Quote the rule and stop."
      : "A recommendation is not a send.";
  const gates = $("gates");
  gates.innerHTML = "";
  for (const row of rec.gates || []) {
    const li = document.createElement("li");
    li.innerHTML = `<span class="tick ${row.ok ? "yes" : "no"}">${row.ok ? "yes" : "no"}</span> ${row.label}`;
    gates.appendChild(li);
  }
}

function renderLog() {
  const list = $("log-list");
  const rows = state.board.log || [];
  if (!rows.length) {
    list.innerHTML = `<li class="empty">No sends yet.</li>`;
    return;
  }
  list.innerHTML = "";
  for (const row of rows) {
    const li = document.createElement("li");
    li.innerHTML = `<span class="when">${row.ts}</span> · ${row.dispatcher} · ${row.decision} ${row.vehicle_id || ""} on ${row.job_id || ""} · ${row.rule || "undo"}`;
    list.appendChild(li);
  }
}

function renderAsk() {
  const box = $("ask-result");
  if (!state.ask) {
    box.hidden = true;
    box.innerHTML = "";
    return;
  }
  const t = tone(state.ask.label);
  box.hidden = false;
  box.style.background = t.bg;
  box.style.color = t.fg;
  box.innerHTML = `<p class="lead">${state.ask.label}${state.ask.rule ? " · " + state.ask.rule : ""}</p><p class="body">${state.ask.detail}</p>`;
}

function render() {
  const board = state.board;
  if (!board) return;
  $("mark").textContent = board.mark;
  $("org").textContent = board.org;
  $("desk").textContent = board.desk;
  $("yard").textContent = board.yard;
  $("shift").textContent = board.shift;
  $("dispatcher").textContent = board.dispatcher;
  $("who-clicks").textContent = board.who_clicks;
  $("job-count").textContent = board.job_count;
  $("vehicle-count").textContent = board.vehicles.length;
  renderLists();
  renderCase();
  renderMap();
  renderLog();
  renderAsk();
}

async function loadBoard(job, vehicle) {
  const params = new URLSearchParams();
  if (job) params.set("job", job);
  if (vehicle) params.set("vehicle", vehicle);
  const data = await (await fetch("/api/board?" + params.toString())).json();
  state.board = data;
  state.job = data.selected_job;
  state.vehicle = data.selected_vehicle;
  location.hash = data.selected_job || "";
  render();
}

$("confirm-btn").addEventListener("click", async () => {
  const rec = state.board.recommendation;
  const data = await (
    await fetch("/api/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: rec.job_id, vehicle_id: rec.vehicle_id }),
    })
  ).json();
  state.board = data.board;
  state.ask = data.ok ? null : { label: "Refuse", rule: "", detail: data.error };
  render();
});

$("undo-btn").addEventListener("click", async () => {
  const data = await (await fetch("/api/undo", { method: "POST" })).json();
  state.board = data.board;
  render();
});

$("ask-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = $("ask-input").value.trim();
  if (!question) return;
  const data = await (
    await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        job_id: state.board.selected_job,
        vehicle_id: state.board.selected_vehicle,
      }),
    })
  ).json();
  state.ask = { label: data.label, rule: data.rule, detail: data.detail || data.error };
  renderAsk();
});

const wanted = decodeURIComponent(location.hash.replace("#", ""));
loadBoard(wanted || "J-01", null);
