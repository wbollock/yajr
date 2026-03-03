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
  ].join("\\n");

  document.getElementById("j2_data").value = [
    "interfaces:",
    "  - name: Ethernet1",
    "    description: Uplink to core",
    "    ip: 192.0.2.10/24",
    "  - name: Ethernet2",
    "    description: Server VLAN",
    "    ip: 198.51.100.5/24",
  ].join("\\n");

  document.getElementById("opt_strict").checked = true;
  document.getElementById("opt_trim").checked = true;
  document.getElementById("opt_lstrip").checked = true;
  document.getElementById("filter_hash").checked = false;
  document.getElementById("filter_ipaddr").checked = true;
  document.querySelector(\"input[name='render_mode'][value='base']\").checked = true;
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

async function renderTemplate() {
  const payload = currentPayload();
  const response = await fetch("/api/render", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();

  const pre = document.getElementById("render_results");
  pre.innerHTML = "";
  pre.append(classifyWhitespaces(data.render_result || ""));
  applyWhitespaceToggle();
}

async function createShare() {
  const payload = currentPayload();
  const response = await fetch("/api/share", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  document.getElementById("share_url").value = data.share_url || "";
}

async function loadShare(token) {
  if (!token) {
    return;
  }
  const response = await fetch(`/api/share/${token}`);
  if (!response.ok) {
    return;
  }
  const payload = await response.json();
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
}

document.getElementById("request_render").addEventListener("click", renderTemplate);
document.getElementById("create_share").addEventListener("click", createShare);
document.getElementById("toggle_whitespaces").addEventListener("change", applyWhitespaceToggle);
document.getElementById("load_defaults").addEventListener("click", loadDefaults);

document.getElementById("reset_render").addEventListener("click", function () {
  document.getElementById("render_results").textContent = "";
});

document.getElementById("copy_render").addEventListener("click", function () {
  navigator.clipboard.writeText(document.getElementById("render_results").innerText || "");
});

loadShare(window.__INITIAL_SHARE_TOKEN__);
