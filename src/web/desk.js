(function () {
  "use strict";

  const FALLBACK_DISPATCH = {
    note: "Embedded S-00 DispatchEvent fixture. Used when fetch is blocked.",
    events: [
      {
        job_id: "J-01",
        city: "Cluj",
        km: 40,
        vehicle_id: "T-11",
        kind: "ASSIGN",
        dsp_ids: ["DSP-1", "DSP-2"],
        quotes: {
          "DSP-1": "DSP-1. Assign only a vehicle with status free and hours_ok true.",
          "DSP-2": "DSP-2. Job distance must be less than vehicle range_km."
        }
      },
      {
        job_id: "J-01",
        city: "Cluj",
        km: 40,
        vehicle_id: "T-12",
        kind: "SKIP",
        dsp_ids: ["DSP-1"],
        quotes: {
          "DSP-1": "DSP-1. Assign only a vehicle with status free and hours_ok true."
        }
      },
      {
        job_id: "J-01",
        city: "Cluj",
        km: 40,
        vehicle_id: "T-14",
        kind: "REFUSE",
        dsp_ids: ["DSP-3"],
        quotes: {
          "DSP-3": "DSP-3. Status red is out of service. Do not assign. Quote this rule."
        }
      },
      {
        job_id: "J-02",
        city: "Oradea",
        km: 160,
        vehicle_id: "T-11",
        kind: "ASSIGN",
        dsp_ids: ["DSP-1", "DSP-2"],
        quotes: {
          "DSP-1": "DSP-1. Assign only a vehicle with status free and hours_ok true.",
          "DSP-2": "DSP-2. Job distance must be less than vehicle range_km."
        }
      },
      {
        job_id: "J-02",
        city: "Oradea",
        km: 160,
        vehicle_id: "T-12",
        kind: "SKIP",
        dsp_ids: ["DSP-1"],
        quotes: {
          "DSP-1": "DSP-1. Assign only a vehicle with status free and hours_ok true."
        }
      },
      {
        job_id: "J-02",
        city: "Oradea",
        km: 160,
        vehicle_id: "T-14",
        kind: "REFUSE",
        dsp_ids: ["DSP-3"],
        quotes: {
          "DSP-3": "DSP-3. Status red is out of service. Do not assign. Quote this rule."
        }
      }
    ]
  };

  const FALLBACK_LOCATIONS = {
    garage: { id: "G-0", name: "Garage", km_from_garage: 0, power_kw: 22 },
    charging_stations: [
      { id: "CS-1", name: "Cluj peri-urban DC", km_from: { Cluj: 20, Oradea: 40 }, power_kw: 50 },
      { id: "CS-2", name: "Oradea highway DC", km_from: { Cluj: 60, Oradea: 20 }, power_kw: 150 },
      { id: "CS-3", name: "Corridor DC", km_from: { Cluj: 100, Oradea: 47 }, power_kw: 50 },
      { id: "CS-4", name: "Ultra-fast (out of range)", km_from: { Cluj: 300, Oradea: 200 }, power_kw: 350 },
      { id: "CS-5", name: "Remote AC", km_from: { Cluj: 350, Oradea: 74 }, power_kw: 22 }
    ]
  };

  const FALLBACK_TELEMETRY = {
    events: [
      {
        vehicle_id: "T-11",
        job_id: "J-02",
        status: "en_route",
        speed_kmh: 72,
        drive_power_kw: 45,
        soc_pct: 38.0,
        range_km: 68.0,
        km_from_garage: 90.0,
        charger_id: null,
        charger_power_kw: null
      }
    ]
  };

  const DISPATCH_URLS = [
    "/api/dispatch",
    "../../pipelines/fixtures/dispatch_events.json",
    "/pipelines/fixtures/dispatch_events.json"
  ];

  const LOCATION_URLS = [
    "/api/locations",
    "../../.docs/reference/locations.json",
    "/.docs/reference/locations.json"
  ];

  const TELEMETRY_URLS = [
    "/api/telemetry",
    "../../pipelines/fixtures/telemetry_events.json",
    "/pipelines/fixtures/telemetry_events.json"
  ];

  const CHARGER_ROLES = {
    "G-0": "depot start / return",
    "CS-1": "nearest after Cluj",
    "CS-2": "nearest after Oradea",
    "CS-3": "backup",
    "CS-4": "unreachable",
    "CS-5": "too far / slow"
  };

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function dash(value, unit) {
    if (value === null || value === undefined || value === "") {
      return "—";
    }
    return unit ? `${value} ${unit}` : String(value);
  }

  function asList(payload) {
    if (!payload) {
      return [];
    }
    if (Array.isArray(payload)) {
      return payload;
    }
    if (Array.isArray(payload.events)) {
      return payload.events;
    }
    if (payload.vehicle_id) {
      return [payload];
    }
    return [];
  }

  async function tryFetch(url) {
    const ctrl = new AbortController();
    const timer = setTimeout(function () { ctrl.abort(); }, 2500);
    try {
      const res = await fetch(url, { cache: "no-store", signal: ctrl.signal });
      if (!res.ok) {
        throw new Error(String(res.status));
      }
      return await res.json();
    } finally {
      clearTimeout(timer);
    }
  }

  async function loadFirst(urls, fallback) {
    for (let i = 0; i < urls.length; i += 1) {
      try {
        const data = await tryFetch(urls[i]);
        return { data: data, source: urls[i] };
      } catch (err) {
        /* try next candidate */
      }
    }
    return { data: fallback, source: "embedded fallback" };
  }

  function setSource(id, label) {
    const node = document.getElementById(id);
    if (node) {
      node.textContent = label;
    }
  }

  function kindClass(kind) {
    if (kind === "ASSIGN") {
      return "kind kind--assign";
    }
    if (kind === "SKIP") {
      return "kind kind--skip";
    }
    return "kind kind--refuse";
  }

  function quoteBlocks(event) {
    const quotes = event.quotes || {};
    const ids = event.dsp_ids || Object.keys(quotes);
    if (!ids.length) {
      return "<span>—</span>";
    }
    return ids.map(function (id) {
      if (quotes[id]) {
        return "<blockquote>" + escapeHtml(quotes[id]) + "</blockquote>";
      }
      return "<blockquote>" + escapeHtml(id) + "</blockquote>";
    }).join("");
  }

  function renderDecisions(events) {
    const body = document.getElementById("decision-body");
    if (!body) {
      return;
    }
    body.innerHTML = events.map(function (event) {
      const kind = event.kind === "ASSIGN" || event.kind === "SKIP" || event.kind === "REFUSE"
        ? event.kind
        : "REFUSE";
      const vehicle = event.vehicle_id || "";
      const refuse = kind === "REFUSE" || vehicle === "T-14";
      const rowClass = refuse ? ' class="row-refuse"' : "";
      const shownKind = vehicle === "T-14" ? "REFUSE" : kind;
      return (
        "<tr" + rowClass + ' data-kind="' + escapeHtml(shownKind) +
        '" data-vehicle="' + escapeHtml(vehicle) + '">' +
        "<td>" + escapeHtml(event.job_id || "") + "</td>" +
        "<td>" + escapeHtml(event.city || "") + "</td>" +
        "<td>" + escapeHtml(event.km == null ? "" : event.km) + "</td>" +
        "<td>" + escapeHtml(vehicle) + "</td>" +
        '<td><span class="' + kindClass(shownKind) + '">' + escapeHtml(shownKind) + "</span></td>" +
        "<td>" + escapeHtml((event.dsp_ids || []).join(", ")) + "</td>" +
        "<td>" + quoteBlocks(event) + "</td>" +
        "</tr>"
      );
    }).join("");
  }

  function renderChargers(locations) {
    const body = document.getElementById("charge-body");
    if (!body) {
      return;
    }
    const garage = locations.garage || FALLBACK_LOCATIONS.garage;
    const stations = locations.charging_stations || FALLBACK_LOCATIONS.charging_stations;
    const rows = [];

    rows.push({
      id: garage.id,
      name: garage.name,
      power_kw: garage.power_kw,
      cluj: garage.km_from_garage,
      oradea: garage.km_from_garage,
      role: CHARGER_ROLES[garage.id] || "depot"
    });

    stations.forEach(function (station) {
      const km = station.km_from || {};
      rows.push({
        id: station.id,
        name: station.name,
        power_kw: station.power_kw,
        cluj: km.Cluj,
        oradea: km.Oradea,
        role: CHARGER_ROLES[station.id] || ""
      });
    });

    body.innerHTML = rows.map(function (row) {
      let cls = "";
      if (row.id === "CS-2") {
        cls = ' class="row-highlight"';
      } else if (row.id === "CS-4") {
        cls = ' class="row-unreachable"';
      }
      return (
        "<tr" + cls + ' data-charger="' + escapeHtml(row.id) + '">' +
        "<td>" + escapeHtml(row.id) + "</td>" +
        "<td>" + escapeHtml(row.name) + "</td>" +
        "<td>" + escapeHtml(row.power_kw) + " kW</td>" +
        "<td>" + escapeHtml(row.cluj) + "</td>" +
        "<td>" + escapeHtml(row.oradea) + "</td>" +
        "<td>" + escapeHtml(row.role) + "</td>" +
        "</tr>"
      );
    }).join("");
  }

  function emptyTelemetry() {
    return (
      '<div class="empty-panel" data-empty="true">' +
      "<p>No live driver telemetry yet.</p>" +
      "<p>Poll <code>/api/telemetry</code> when S-14 is up. T-12 SKIP and T-14 REFUSE never start a driver.</p>" +
      "</div>"
    );
  }

  function renderTelemetry(events) {
    const panel = document.getElementById("telemetry-panel");
    if (!panel) {
      return;
    }
    if (!events.length) {
      panel.innerHTML = emptyTelemetry();
      return;
    }
    panel.innerHTML = events.map(function (event) {
      const status = event.status || "en_route";
      const junction = status === "junction_stop" ? "yes" : "no";
      const charger = dash(event.charger_id);
      const chargerKw = event.charger_power_kw == null ? "—" : event.charger_power_kw + " kW";
      return (
        '<article class="telemetry-card" data-status="' + escapeHtml(status) + '">' +
        "<header>" +
        '<p class="ticket__id">' + escapeHtml(event.vehicle_id || "") + "</p>" +
        "<p><span class=\"status-pill status-pill--" + escapeHtml(status) + '">' +
        escapeHtml(status) + "</span> on " + escapeHtml(event.job_id || "—") + "</p>" +
        "</header>" +
        '<dl class="metrics">' +
        "<div><dt>Speed</dt><dd>" + escapeHtml(dash(event.speed_kmh, "km/h")) + "</dd></div>" +
        "<div><dt>Junction stop</dt><dd>" + junction + "</dd></div>" +
        "<div><dt>Drive</dt><dd>" + escapeHtml(dash(event.drive_power_kw, "kW")) + "</dd></div>" +
        "<div><dt>SOC</dt><dd>" + escapeHtml(event.soc_pct == null ? "—" : event.soc_pct + "%") + "</dd></div>" +
        "<div><dt>Remaining range</dt><dd>" + escapeHtml(dash(event.range_km, "km")) + "</dd></div>" +
        "<div><dt>From garage</dt><dd>" + escapeHtml(dash(event.km_from_garage, "km")) + "</dd></div>" +
        "<div><dt>Charger</dt><dd>" + escapeHtml(charger) + "</dd></div>" +
        "<div><dt>Charger power</dt><dd>" + escapeHtml(chargerKw) + "</dd></div>" +
        "</dl></article>"
      );
    }).join("");
  }

  function tickClock() {
    const node = document.getElementById("desk-clock");
    if (!node) {
      return;
    }
    const now = new Date();
    node.dateTime = now.toISOString();
    node.textContent = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  }

  async function refreshTelemetry(preferLiveEmpty) {
    const loaded = await loadFirst(TELEMETRY_URLS, FALLBACK_TELEMETRY);
    const fromApi = loaded.source.indexOf("/api/") === 0;
    const events = asList(loaded.data);
    if (fromApi) {
      renderTelemetry(events);
      setSource("telemetry-source", loaded.source);
      return;
    }
    if (preferLiveEmpty && events.length === 0) {
      renderTelemetry([]);
      setSource("telemetry-source", "empty");
      return;
    }
    renderTelemetry(events);
    setSource("telemetry-source", loaded.source);
  }

  async function boot() {
    tickClock();
    window.setInterval(tickClock, 1000);

    const dispatch = await loadFirst(DISPATCH_URLS, FALLBACK_DISPATCH);
    const events = asList(dispatch.data);
    renderDecisions(events.length ? events : FALLBACK_DISPATCH.events);
    setSource("dispatch-source", dispatch.source);

    const locations = await loadFirst(LOCATION_URLS, FALLBACK_LOCATIONS);
    renderChargers(locations.data && locations.data.charging_stations ? locations.data : FALLBACK_LOCATIONS);
    setSource("locations-source", locations.source);

    await refreshTelemetry(false);
    window.setInterval(function () { refreshTelemetry(true); }, 4000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
