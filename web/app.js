const state = {
  board: null,
  job: null,
  vehicle: null,
  ask: null,
  view: "job",
  charger: null,
};

const SVG = "http://www.w3.org/2000/svg";
const motion = Object.create(null);
let motionGen = 0;
let lastFrame = 0;

function hypot2(a, b) {
  return Math.hypot(b[0] - a[0], b[1] - a[1]);
}

function pointAlong(points, t) {
  if (!points || !points.length) return [0, 0];
  if (points.length === 1 || t <= 0) return [points[0][0], points[0][1]];
  if (t >= 1) {
    const last = points[points.length - 1];
    return [last[0], last[1]];
  }
  const lengths = [];
  let total = 0;
  for (let i = 1; i < points.length; i += 1) {
    const len = hypot2(points[i - 1], points[i]);
    lengths.push(len);
    total += len;
  }
  if (total <= 0) return [points[0][0], points[0][1]];
  let target = t * total;
  let acc = 0;
  for (let i = 0; i < lengths.length; i += 1) {
    const length = lengths[i];
    if (acc + length >= target) {
      const u = length === 0 ? 0 : (target - acc) / length;
      const a = points[i];
      const b = points[i + 1];
      return [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u];
    }
    acc += length;
  }
  const last = points[points.length - 1];
  return [last[0], last[1]];
}

function headingOf(prev, cur, fallback) {
  if (hypot2(prev, cur) < 0.4) return fallback;
  return (Math.atan2(cur[1] - prev[1], cur[0] - prev[0]) * 180) / Math.PI;
}

function pathKey(path) {
  if (!path || path.length < 2) return "";
  const a = path[0];
  const b = path[path.length - 1];
  return `${path.length}:${a[0]},${a[1]}:${b[0]},${b[1]}`;
}

function poseOf(row) {
  const id = row.id;
  const path = row.path && row.path.length > 1 ? row.path : null;
  const pathKm = Number(row.path_km) || 0;
  const pathDone = Number(row.path_done) || 0;
  const speedKmh = Number(row.speed_kmh) || 0;
  let m = motion[id];
  if (!m || m.gen !== motionGen) {
    const t = pathKm > 0 ? Math.min(1, pathDone / pathKm) : 0;
    const p = path ? pointAlong(path, t) : [row.x, row.y];
    m = {
      gen: motionGen,
      x: p[0],
      y: p[1],
      heading: row.heading || 0,
      path,
      pathKey: pathKey(path),
      pathKm,
      pathDone: path ? pathDone : 0,
      speedKmh,
    };
    motion[id] = m;
    return m;
  }
  m.speedKmh = speedKmh;
  const key = pathKey(path);
  if (path && key !== m.pathKey) {
    m.path = path;
    m.pathKey = key;
    m.pathKm = pathKm;
    m.pathDone = pathDone;
    const p = pointAlong(path, pathKm > 0 ? Math.min(1, pathDone / pathKm) : 0);
    m.x = p[0];
    m.y = p[1];
  } else if (path) {
    m.path = path;
    m.pathKm = pathKm;
  } else {
    m.path = null;
    m.pathKey = "";
    m.pathKm = 0;
    m.speedKmh = 0;
  }
  return m;
}

function stepMotion(dt) {
  const sim = (state.board && state.board.sim) || {};
  const scale = Number(sim.speed || 0) * Number(sim.sim_per_wall_1x || 90);
  if (dt <= 0) return;
  for (const id of Object.keys(motion)) {
    const m = motion[id];
    if (!m.path || m.path.length < 2 || m.pathKm <= 0 || m.speedKmh <= 0 || scale <= 0) continue;
    const km = (m.speedKmh / 3600) * dt * scale;
    m.pathDone = Math.min(m.pathKm, m.pathDone + km);
    const t = m.pathDone / m.pathKm;
    const prev = [m.x, m.y];
    const nxt = pointAlong(m.path, t);
    m.x = nxt[0];
    m.y = nxt[1];
    m.heading = headingOf(prev, nxt, m.heading);
  }
}

function paintUnits() {
  const units = $("map-units");
  if (!units) return;
  for (const g of units.querySelectorAll("[data-id]")) {
    const m = motion[g.getAttribute("data-id")];
    if (!m) continue;
    g.setAttribute("transform", `translate(${m.x} ${m.y}) rotate(${m.heading})`);
    const lab = g.querySelector("text");
    if (lab) lab.setAttribute("transform", `rotate(${-m.heading})`);
  }
  const ring = $("map-range") && $("map-range").querySelector("circle");
  const selectedId = state.board && state.board.map && state.board.map.selected_id;
  const sel = selectedId ? motion[selectedId] : null;
  if (ring && sel) {
    ring.setAttribute("cx", String(sel.x));
    ring.setAttribute("cy", String(sel.y));
  }
}

function motionFrame(ts) {
  const dt = lastFrame ? Math.min(0.05, (ts - lastFrame) / 1000) : 0;
  lastFrame = ts;
  stepMotion(dt);
  paintUnits();
  requestAnimationFrame(motionFrame);
}
requestAnimationFrame(motionFrame);

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

function jobStateLabel(row) {
  if (row.state === "assigned") return `On ${row.vehicle_id}`;
  if (row.state === "done") return "Done";
  return "Open";
}

function etaText(seconds) {
  const s = Math.max(0, Math.round(seconds || 0));
  if (s <= 0) return "Free now";
  const m = Math.floor(s / 60);
  const r = s % 60;
  if (m <= 0) return `Free in ${r}s`;
  return `Free in ${m}m ${r}s`;
}

function parseHash() {
  const raw = decodeURIComponent(location.hash.replace("#", ""));
  const parts = raw.split("/").filter(Boolean);
  if (parts[0] === "vehicle" && parts[1]) return { view: "vehicle", vehicle: parts[1], job: state.job };
  if (parts[0] === "job" && parts[1]) return { view: "job", job: parts[1], vehicle: null };
  if (parts[0] && /^J-/.test(parts[0])) return { view: "job", job: parts[0], vehicle: null };
  return { view: "job", job: "J-01", vehicle: null };
}

function writeHash() {
  if (state.view === "vehicle" && state.vehicle) {
    location.hash = `/vehicle/${state.vehicle}`;
    return;
  }
  location.hash = `/job/${state.job || "J-01"}`;
}

function svg(name, attrs) {
  const node = document.createElementNS(SVG, name);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === null || value === undefined) continue;
    node.setAttribute(key, String(value));
  }
  return node;
}

function pts(list) {
  return (list || []).map((p) => `${p[0]},${p[1]}`).join(" ");
}

function renderLists() {
  const board = state.board;
  const jobs = $("job-list");
  jobs.innerHTML = "";
  for (const job of board.jobs) {
    const rec = job.id === board.selected_job && state.view === "job" ? board.recommendation : null;
    const label = job.state === "open" && rec ? rec.decision : jobStateLabel(job);
    const t = tone(job.state === "done" ? "Assign" : label);
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = job.id === board.selected_job && state.view === "job" ? "on" : "off";
    btn.innerHTML = `
      <div class="row">
        <span class="mono">${job.id}</span>
        <span class="badge" style="background:${t.bg};color:${t.fg}">${label}</span>
      </div>
      <p class="who">${job.city}</p>
      <p class="proc">${job.km} km${job.vehicle_id ? " · " + job.vehicle_id : ""}</p>
    `;
    btn.addEventListener("click", () => {
      state.view = "job";
      loadBoard(job.id, null);
    });
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
    const eta = row.status === "busy" ? ` · ${etaText(row.eta_free_s)}` : "";
    btn.innerHTML = `
      <div class="row">
        <span class="mono">${row.id}</span>
        <span class="badge" style="background:${st.bg};color:${st.fg}">${statusLabel(row.status)}</span>
      </div>
      <p class="proc">${row.activity_label || ""}</p>
      <p class="proc">range ${Math.round(row.range_km)} km · hours_ok ${row.hours_ok ? "true" : "false"}${eta}</p>
    `;
    btn.addEventListener("click", () => {
      state.view = "vehicle";
      loadBoard(board.selected_job, row.id);
    });
    const li = document.createElement("li");
    li.appendChild(btn);
    vehicles.appendChild(li);
  }
}

function renderMap() {
  const map = state.board.map;
  if (!map) return;
  const land = $("map-land");
  land.replaceChildren();
  for (const poly of map.land || []) {
    land.appendChild(svg("polygon", { points: pts(poly), fill: "url(#land-fill)" }));
  }
  const river = $("map-river");
  river.replaceChildren(svg("polyline", { points: pts(map.river), class: "river" }));

  const grid = $("map-grid");
  grid.replaceChildren();
  for (let x = 50; x < 1000; x += 50) grid.appendChild(svg("line", { x1: x, y1: 0, x2: x, y2: 520, class: "grid-line" }));
  for (let y = 50; y < 520; y += 50) grid.appendChild(svg("line", { x1: 0, y1: y, x2: 1000, y2: y, class: "grid-line" }));

  const road = $("map-road");
  road.replaceChildren();
  road.appendChild(svg("polyline", { points: pts(map.corridor), class: "road-line" }));
  road.appendChild(svg("polyline", { points: pts(map.corridor), class: "road-core" }));

  const trails = $("map-trails");
  trails.replaceChildren();
  for (const row of map.vehicles || []) {
    const color = row.status === "red" ? "#e24b4b" : row.status === "busy" ? "#e8a317" : "#3dcc8a";
    if (row.trail && row.trail.length > 1) {
      trails.appendChild(svg("polyline", { points: pts(row.trail), class: "trail", stroke: color }));
    }
  }
  if (map.van && map.van.trail && map.van.trail.length > 1) {
    trails.appendChild(svg("polyline", { points: pts(map.van.trail), class: "trail", stroke: "#7ec8ff" }));
  }

  const active = $("map-active");
  active.replaceChildren();
  if (map.selected_path && map.selected_path.length > 1) {
    active.appendChild(svg("polyline", { points: pts(map.selected_path), class: "active-path" }));
  }

  const range = $("map-range");
  range.replaceChildren();
  const selected = (map.vehicles || []).find((row) => row.id === map.selected_id);
  if (selected && map.px_per_km) {
    const pose = poseOf(selected);
    const r = Math.min(260, selected.range_km * map.px_per_km);
    range.appendChild(svg("circle", { cx: pose.x, cy: pose.y, r, class: "range-ring" }));
  }

  const chargers = $("map-chargers");
  chargers.replaceChildren();
  for (const row of map.chargers || []) {
    const far = row.reachable === false;
    const g = svg("g", { class: `charger${state.charger === row.id ? " on" : ""}${far ? " far" : ""}`, "data-id": row.id });
    g.appendChild(svg("circle", { class: "pad", cx: row.x, cy: row.y, r: 11, fill: "#10222a", stroke: far ? "#6b7c86" : "#7ec8ff", "stroke-width": 2 }));
    g.appendChild(svg("polygon", {
      points: `${row.x - 2},${row.y - 6} ${row.x + 4},${row.y - 6} ${row.x},${row.y - 1} ${row.x + 5},${row.y - 1} ${row.x - 3},${row.y + 7} ${row.x},${row.y + 1} ${row.x - 4},${row.y + 1}`,
      fill: far ? "#6b7c86" : "#7ec8ff",
    }));
    const label = svg("text", { x: row.x + 14, y: row.y + 4, class: "map-sublabel", fill: "#9aa8b0" });
    label.textContent = row.power_kw ? `${row.id} · ${row.power_kw} kW` : row.id;
    g.appendChild(label);
    g.addEventListener("click", (event) => {
      event.stopPropagation();
      state.charger = row.id;
      if (state.vehicle) {
        state.view = "vehicle";
        renderVehicle();
        renderMap();
      }
    });
    chargers.appendChild(g);
  }

  const cities = $("map-cities");
  cities.replaceChildren();
  for (const row of map.cities || []) {
    cities.appendChild(svg("circle", { cx: row.x, cy: row.y, r: 11, class: "city-ring" }));
    cities.appendChild(svg("circle", { cx: row.x, cy: row.y, r: 5, fill: "#e8a317" }));
    const label = svg("text", { x: row.x + 14, y: row.y - 6, class: "map-label" });
    label.textContent = row.name;
    cities.appendChild(label);
    const sub = svg("text", { x: row.x + 14, y: row.y + 10, class: "map-sublabel" });
    sub.textContent = row.sub;
    cities.appendChild(sub);
  }

  const units = $("map-units");
  units.replaceChildren();
  for (const row of map.vehicles || []) {
    const pose = poseOf(row);
    const color = row.status === "red" ? "#e24b4b" : row.status === "busy" ? "#e8a317" : "#3dcc8a";
    const g = svg("g", {
      class: `unit${row.id === map.selected_id ? " selected" : ""}${row.activity === "servicing" ? " pulse" : ""}`,
      "data-id": row.id,
      transform: `translate(${pose.x} ${pose.y}) rotate(${pose.heading})`,
    });
    g.appendChild(svg("rect", { class: "body", x: -12, y: -7, width: 24, height: 14, rx: 4, fill: color }));
    g.appendChild(svg("rect", { x: 6, y: -4, width: 8, height: 8, rx: 2, fill: "#0e1418", opacity: "0.35" }));
    const lab = svg("text", {
      x: 16,
      y: 4,
      class: "map-label",
      fill: color,
      transform: `rotate(${-pose.heading})`,
    });
    lab.textContent = row.id;
    g.appendChild(lab);
    g.addEventListener("click", (event) => {
      event.stopPropagation();
      state.view = "vehicle";
      loadBoard(state.job, row.id);
    });
    units.appendChild(g);
  }
  if (map.van) {
    const pose = poseOf(map.van);
    const g = svg("g", {
      class: "unit crew",
      "data-id": "crew",
      transform: `translate(${pose.x} ${pose.y}) rotate(${pose.heading})`,
    });
    g.appendChild(svg("rect", { class: "body", x: -11, y: -6, width: 22, height: 12, rx: 3, fill: "#7ec8ff" }));
    g.appendChild(svg("circle", { class: "wrench-spin", cx: 0, cy: 0, r: 3, fill: "#10222a" }));
    const lab = svg("text", {
      x: 14,
      y: 4,
      class: "map-label",
      fill: "#7ec8ff",
      transform: `rotate(${-pose.heading})`,
    });
    lab.textContent = "CREW";
    g.appendChild(lab);
    units.appendChild(g);
  }
}

function renderCase() {
  const board = state.board;
  const rec = board.recommendation;
  const phase = rec.phase || "open";
  const label = phase === "assigned" ? "On job" : phase === "done" ? "Done" : rec.decision;
  const t = tone(rec.decision);
  $("case-id").textContent = rec.job_id || "";
  $("case-name").textContent = rec.city || "";
  $("case-sub").textContent = rec.vehicle_id
    ? `${rec.km} km · vehicle ${rec.vehicle_id}`
    : `${rec.km || ""} km`;
  const card = $("decision-card");
  card.style.background = t.bg;
  card.style.color = t.fg;
  $("case-decision").textContent =
    phase === "assigned"
      ? `On job ${rec.vehicle_id}`
      : phase === "done"
        ? `Done ${rec.vehicle_id}`
        : rec.decision === "Assign"
          ? `Assign ${rec.vehicle_id}`
          : rec.decision;
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
  const warns = $("warn-list");
  warns.innerHTML = "";
  for (const note of board.warnings || []) {
    const li = document.createElement("li");
    li.textContent = note;
    warns.appendChild(li);
  }
  void label;
}

function renderVehicle() {
  const detail = state.board.vehicle_detail;
  if (!detail) return;
  const st = statusTone(detail.status);
  $("veh-id").textContent = detail.id;
  $("veh-place").textContent = detail.place || "";
  const badge = $("veh-status");
  badge.textContent = statusLabel(detail.status);
  badge.style.background = st.bg;
  badge.style.color = st.fg;
  const pct = detail.range_full ? (detail.range_km / detail.range_full) * 100 : 0;
  $("range-text").textContent = `${Math.round(detail.range_km)} / ${Math.round(detail.range_full)} km`;
  const fill = $("range-fill");
  fill.style.width = `${Math.max(2, pct)}%`;
  fill.className = pct < 18 ? "dead" : pct < 40 ? "low" : "";
  const holding =
    detail.status === "red" ||
    detail.status === "free" ||
    ["idle", "dwelling", "charging", "servicing", "stranded"].includes(detail.activity) ||
    !detail.speed_kmh;
  $("range-drain").textContent = holding
    ? "Idle / stopped. Range holds."
    : `Moving ${detail.speed_kmh | 0} km/h · range drains 1 km per km driven.`;
  $("work-title").textContent = (detail.work && detail.work.title) || detail.activity_label;
  $("work-detail").textContent = (detail.work && detail.work.detail) || "";
  $("work-fill").style.width = `${Math.round(((detail.work && detail.work.progress) || 0) * 100)}%`;
  $("work-eta").textContent =
    detail.status === "red"
      ? "Out of service. Call yard crew to return it to the roster."
      : detail.status === "free"
        ? "Standing by · can authorize a job"
        : `${etaText(detail.eta_free_s)} · ${detail.eta_free_clock}`;
  const sked = $("veh-schedule");
  sked.innerHTML = "";
  for (const row of detail.schedule || []) {
    const li = document.createElement("li");
    li.innerHTML = `<span class="when">${row.clock}</span><span>${row.label}</span>`;
    sked.appendChild(li);
  }
  $("veh-advice").textContent = detail.ops.charge_advice || "Confirm is still required before anything goes out.";
  const actions = $("veh-actions");
  actions.innerHTML = "";
  const rec = state.board.recommendation;
  if (state.board.can_send && rec.vehicle_id === detail.id) {
    addAction(actions, `Confirm ${rec.job_id} → ${detail.id}`, "primary", () => confirmSend());
  }
  if (detail.ops.can_service) {
    addAction(actions, "Call yard service", "warn", () => postOp("/api/service", { vehicle_id: detail.id }));
  }
  if (detail.ops.can_charge) {
    const charger = state.charger || (detail.ops.nearest_charger && detail.ops.nearest_charger.id);
    const name = (state.board.map.chargers || []).find((row) => row.id === charger);
    addAction(
      actions,
      `Send to ${name ? name.name : "charger"}`,
      "primary",
      () => postOp("/api/charge", { vehicle_id: detail.id, charger_id: charger }),
    );
  }
  if (detail.ops.can_return) {
    addAction(actions, "Return to yard", "ghost", () => postOp("/api/return", { vehicle_id: detail.id }));
  }
  addAction(actions, "Undo last send", "ghost", () => undoSend(), state.board.can_undo);
}

function addAction(root, label, kind, fn, enabled) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = kind === "primary" ? "primary" : kind === "warn" ? "warn" : "ghost";
  btn.textContent = label;
  if (enabled === false) btn.disabled = true;
  btn.addEventListener("click", fn);
  root.appendChild(btn);
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
    li.innerHTML = `<span class="when">${row.clock || row.ts}</span> · ${row.dispatcher} · ${row.decision} ${row.vehicle_id || ""} ${row.job_id || ""} · ${row.rule || row.quote || ""}`;
    list.appendChild(li);
  }
}

function renderEvents() {
  const list = $("event-list");
  const rows = (state.board.events || []).slice(0, 6);
  list.innerHTML = "";
  for (const row of rows) {
    const li = document.createElement("li");
    li.innerHTML = `<span class="when">${row.clock}</span>${row.text}`;
    list.appendChild(li);
  }
  if (rows[0]) $("ticker-text").textContent = `${rows[0].clock} · ${rows[0].text}`;
}

function renderAgents() {
  const pack = (state.board && state.board.agents) || {};
  const llm = pack.llm || {};
  $("agents-plugin").textContent = pack.model_label || pack.model || "Grok 4.20 fast";
  $("agents-note").textContent = pack.note || "Live Grok agents on the radio. Engine still runs dispatch_job.";
  const ticket = pack.dispatcher;
  const reply = pack.driver;
  const dispPane = $("dispatcher-pane");
  const drvPane = $("driver-pane");
  dispPane.classList.remove("assign", "refuse", "calling");
  drvPane.classList.remove("accept", "decline", "calling");
  if (llm.status === "calling") {
    dispPane.classList.add("calling");
    drvPane.classList.add("calling");
  }
  if (ticket) {
    const kind = ticket.kind || ticket.decision;
    dispPane.classList.add(ticket.decision === "Assign" ? "assign" : "refuse");
    $("dispatcher-line").textContent = `${kind} ${ticket.vehicle_id} · ${ticket.job_id} ${ticket.city}`;
    $("dispatcher-rule").textContent = ticket.rule || "";
    $("dispatcher-quoted").textContent = ticket.say || ticket.quoted || "";
  } else {
    $("dispatcher-line").textContent = "No ticket for this pair.";
    $("dispatcher-rule").textContent = "";
    $("dispatcher-quoted").textContent = "";
  }
  if (reply) {
    drvPane.classList.add(reply.action === "Accept" ? "accept" : "decline");
    const live = (pack.started || []).find(
      (row) => row.job_id === reply.job_id && row.vehicle_id === reply.vehicle_id,
    );
    const status = reply.status || (live && live.status) || "idle";
    let line = `${reply.action} ${reply.vehicle_id} · ${status} · ${reply.city}`;
    if (reply.charger_id) {
      line += ` · ${reply.charger_id}`;
      if (reply.charger_power_kw) line += ` ${reply.charger_power_kw} kW`;
    }
    $("driver-line").textContent = line;
    $("driver-rule").textContent = reply.rule || "";
    $("driver-quoted").textContent = reply.say || reply.quoted || "";
  } else {
    $("driver-line").textContent = "Driver waits for a dispatcher ticket.";
    $("driver-rule").textContent = "";
    $("driver-quoted").textContent = "";
  }
  const list = $("agent-events");
  list.innerHTML = "";
  const selected = ticket || {};
  for (const row of pack.events || []) {
    const li = document.createElement("li");
    const kind = String(row.kind || "").toLowerCase();
    li.className = kind;
    if (row.job_id === selected.job_id && row.vehicle_id === selected.vehicle_id) li.classList.add("on");
    li.textContent = `${row.job_id} ${row.vehicle_id} ${row.kind}`;
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

function renderSim() {
  const sim = state.board.sim || {};
  $("sim-clock").textContent = sim.clock || "";
  $("shift-left").textContent = String(sim.shift_left_min ?? "");
  document.body.classList.toggle("night", Boolean(sim.night));
  for (const btn of document.querySelectorAll(".speed")) {
    btn.classList.toggle("on", Number(btn.dataset.speed) === Number(sim.speed));
  }
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
  $("job-view").hidden = state.view === "vehicle";
  $("vehicle-view").hidden = state.view !== "vehicle";
  renderLists();
  renderCase();
  if (state.view === "vehicle") renderVehicle();
  renderMap();
  renderLog();
  renderEvents();
  renderAgents();
  renderAsk();
  renderSim();
}

async function loadBoard(job, vehicle, opts) {
  const params = new URLSearchParams();
  if (job) params.set("job", job);
  if (vehicle) params.set("vehicle", vehicle);
  const data = await (await fetch("/api/board?" + params.toString())).json();
  state.board = data;
  state.job = data.selected_job;
  if (state.view === "vehicle") {
    state.vehicle = vehicle || data.selected_vehicle;
  } else if (!opts || !opts.soft) {
    state.vehicle = data.selected_vehicle;
  } else {
    state.vehicle = data.selected_vehicle;
  }
  if (!opts || !opts.soft) writeHash();
  render();
}

async function confirmSend() {
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
}

async function undoSend() {
  const data = await (await fetch("/api/undo", { method: "POST" })).json();
  state.board = data.board;
  render();
}

async function postOp(url, body) {
  const data = await (
    await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
  ).json();
  state.board = data.board;
  state.ask = data.ok ? null : { label: "Refuse", rule: data.rule || "", detail: data.error };
  render();
}

$("confirm-btn").addEventListener("click", confirmSend);
$("undo-btn").addEventListener("click", undoSend);
$("back-board").addEventListener("click", () => {
  state.view = "job";
  loadBoard(state.job, null);
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

document.querySelector(".speeds").addEventListener("click", async (event) => {
  const btn = event.target.closest(".speed");
  if (!btn) return;
  if (btn.id === "reset-yard") {
    const speed = Number((state.board && state.board.sim && state.board.sim.speed) ?? 1);
    const data = await (
      await fetch("/api/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ speed }),
      })
    ).json();
    motionGen += 1;
    lastFrame = 0;
    state.board = data.board;
    state.ask = null;
    state.charger = null;
    render();
    return;
  }
  const data = await (
    await fetch("/api/speed", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ speed: Number(btn.dataset.speed) }),
    })
  ).json();
  state.board = data.board;
  render();
});

window.addEventListener("hashchange", () => {
  const parsed = parseHash();
  state.view = parsed.view;
  loadBoard(parsed.job || state.job, parsed.vehicle);
});

const boot = parseHash();
state.view = boot.view;
loadBoard(boot.job, boot.vehicle);
setInterval(() => {
  if (!state.board) return;
  loadBoard(state.job, state.view === "vehicle" ? state.vehicle : state.board.selected_vehicle, { soft: true });
}, 400);
