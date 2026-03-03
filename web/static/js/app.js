function statusLine() {
  return document.getElementById("status_line");
}

function setStatus(message, isError) {
  const el = statusLine();
  el.textContent = message || "";
  if (isError) {
    el.classList.add("error");
  } else {
    el.classList.remove("error");
  }
}


function applyTheme(theme) {
  const body = document.body;
  const toggle = document.getElementById("theme_toggle");
  const mode = theme === "light" ? "light" : "dark";
  body.setAttribute("data-theme", mode);
  toggle.checked = mode === "dark";
  localStorage.setItem("yajr_theme", mode);
}

function initTheme() {
  const saved = localStorage.getItem("yajr_theme");
  applyTheme(saved || "dark");
}

function toggleTheme(event) {
  applyTheme(event.target.checked ? "dark" : "light");
}

function selectedFilters() {
  const filters = [];
  document.querySelectorAll(".add_filters").forEach((el) => {
    if (el.checked) {
      filters.push(el.id.replace("filter_", ""));
    }
  });
  return filters;
}

function currentPayload() {
  const mode = document.querySelector("input[name='render_mode']:checked").value;
  return {
    template: document.getElementById("j2_template").value,
    data: document.getElementById("j2_data").value,
    render_mode: mode,
    options: {
      strict: document.getElementById("opt_strict").checked,
      trim: document.getElementById("opt_trim").checked,
      lstrip: document.getElementById("opt_lstrip").checked,
    },
    filters: selectedFilters(),
  };
}

function loadDefaults() {
  document.getElementById("j2_template").value = [
    "{% for iface in interfaces %}",
    "interface {{ iface.name }}",
    "  description {{ iface.description | default('N/A') }}",
    "  ip address {{ iface.ip | ipaddr('address') }} {{ iface.ip | ipaddr('network') }}",
    "{% endfor %}",
  ].join("\n");

  document.getElementById("j2_data").value = [
    "interfaces:",
    "  - name: Ethernet1",
    "    description: Uplink to core",
    "    ip: 192.0.2.10/24",
    "  - name: Ethernet2",
    "    description: Server VLAN",
    "    ip: 198.51.100.5/24",
  ].join("\n");

  document.getElementById("opt_strict").checked = true;
  document.getElementById("opt_trim").checked = true;
  document.getElementById("opt_lstrip").checked = true;
  document.getElementById("filter_hash").checked = false;
  document.getElementById("filter_ipaddr").checked = true;
  document.querySelector("input[name='render_mode'][value='base']").checked = true;
  setStatus("Loaded defaults.", false);
}

function classifyWhitespaces(text) {
  const wrap = document.createElement("span");
  const normal = [];

  function flush() {
    if (normal.length > 0) {
      wrap.append(document.createTextNode(normal.join("")));
      normal.length = 0;
    }
  }

  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (ch === " " || ch === "\t" || ch === "\n") {
      flush();
      const marker = document.createElement("span");
      if (ch === " ") {
        marker.className = "ws_space";
        marker.textContent = " ";
      } else if (ch === "\t") {
        marker.className = "ws_tab";
        marker.textContent = "\t";
      } else {
        marker.className = "ws_newline";
        marker.textContent = "\n";
      }
      wrap.append(marker);
    } else {
      normal.push(ch);
    }
  }

  flush();
  return wrap;
}

function applyWhitespaceToggle() {
  const enabled = document.getElementById("toggle_whitespaces").checked;
  document.querySelectorAll(".ws_space,.ws_tab,.ws_newline").forEach((el) => {
    if (enabled) {
      el.classList.add("ws_vis");
    } else {
      el.classList.remove("ws_vis");
    }
  });
}

async function jsonFetch(url, payload) {
  const response = await fetch(url, {
    method: payload ? "POST" : "GET",
    headers: payload ? { "Content-Type": "application/json" } : undefined,
    body: payload ? JSON.stringify(payload) : undefined,
  });

  const data = await response.json();
  if (!response.ok) {
    const detail = data.detail || "Request failed.";
    throw new Error(detail);
  }
  return data;
}

async function renderTemplate() {
  try {
    const data = await jsonFetch("/api/render", currentPayload());
    const pre = document.getElementById("render_results");
    pre.innerHTML = "";
    pre.append(classifyWhitespaces(data.render_result || ""));
    applyWhitespaceToggle();
    setStatus("Rendered template.", false);
  } catch (error) {
    setStatus(`Render failed: ${error.message}`, true);
  }
}

async function createShare() {
  try {
    const data = await jsonFetch("/api/share", currentPayload());
    document.getElementById("share_url").value = data.share_url || "";
    setStatus("Share link created.", false);
  } catch (error) {
    setStatus(`Share failed: ${error.message}`, true);
  }
}

async function loadShare(token) {
  if (!token) {
    return;
  }

  try {
    const payload = await jsonFetch(`/api/share/${token}`);
    document.getElementById("j2_template").value = payload.template || "";
    document.getElementById("j2_data").value = payload.data || "";

    const target = document.querySelector(`input[name='render_mode'][value='${payload.render_mode}']`);
    if (target) {
      target.checked = true;
    }

    const options = payload.options || {};
    document.getElementById("opt_strict").checked = !!options.strict;
    document.getElementById("opt_trim").checked = !!options.trim;
    document.getElementById("opt_lstrip").checked = !!options.lstrip;

    const activeFilters = payload.filters || [];
    document.querySelectorAll(".add_filters").forEach((el) => {
      const key = el.id.replace("filter_", "");
      el.checked = activeFilters.includes(key);
    });

    setStatus("Loaded shared template.", false);
  } catch (error) {
    setStatus(`Could not load share link: ${error.message}`, true);
  }
}

function clearRender() {
  document.getElementById("render_results").textContent = "";
  setStatus("Render output cleared.", false);
}

async function copyRender() {
  try {
    await navigator.clipboard.writeText(document.getElementById("render_results").innerText || "");
    setStatus("Rendered output copied.", false);
  } catch (error) {
    setStatus("Copy failed. Browser clipboard access is unavailable.", true);
  }
}

document.getElementById("load_defaults").addEventListener("click", loadDefaults);
document.getElementById("request_render").addEventListener("click", renderTemplate);
document.getElementById("reset_render").addEventListener("click", clearRender);
document.getElementById("copy_render").addEventListener("click", copyRender);
document.getElementById("create_share").addEventListener("click", createShare);
document.getElementById("toggle_whitespaces").addEventListener("change", applyWhitespaceToggle);
document.getElementById("theme_toggle").addEventListener("change", toggleTheme);

initTheme();
loadShare(window.__INITIAL_SHARE_TOKEN__);
