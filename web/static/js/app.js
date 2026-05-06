let templateEditor, dataEditor, outputEditor;

const wsOverlay = {
  token(stream) {
    const ch = stream.peek();
    if (ch === " ") { stream.next(); return "ws-space"; }
    if (ch === "\t") { stream.next(); return "ws-tab"; }
    stream.skipTo(" ") || stream.skipTo("\t") || stream.skipToEnd();
    return null;
  },
};
let wsOverlayActive = false;

// CodeMirror 5 misidentifies apostrophes inside YAML-style comments as string
// delimiters (e.g. "job's" turns everything yellow). This factory wraps any
// mode with a fix: when a line's first non-whitespace char is '#', consume the
// whole line as "comment" and restore the inner mode's state to the snapshot
// taken at the start of that line so the apostrophe never poisons future lines.
function makeCommentFixedMode(innerModeName) {
  CodeMirror.defineMode(innerModeName + "-comment-fixed", function(config) {
    const inner = CodeMirror.getMode(config, innerModeName);
    return {
      startState: function() {
        return {
          inner: CodeMirror.startState(inner),
          solState: null,
          lineIsComment: false,
          inLineComment: false,
        };
      },
      copyState: function(state) {
        return {
          inner: CodeMirror.copyState(inner, state.inner),
          solState: state.solState ? CodeMirror.copyState(inner, state.solState) : null,
          lineIsComment: state.lineIsComment,
          inLineComment: state.inLineComment,
        };
      },
      token: function(stream, state) {
        if (stream.sol()) {
          state.solState = CodeMirror.copyState(inner, state.inner);
          const startPos = stream.pos;
          stream.eatSpace();
          state.lineIsComment = (stream.peek() === "#");
          stream.pos = startPos;
          state.inLineComment = false;
        }
        if (state.lineIsComment || state.inLineComment) {
          if (state.lineIsComment) {
            state.inner = CodeMirror.copyState(inner, state.solState);
          }
          stream.skipToEnd();
          return "comment";
        }
        const tok = inner.token(stream, state.inner);
        if (tok === "comment") {
          state.inLineComment = true;
        }
        return tok;
      },
      indent: inner.indent ? function(state, textAfter) {
        return inner.indent(state.inner, textAfter);
      } : null,
      electricChars: inner.electricChars,
      lineComment: "#",
    };
  });
}

makeCommentFixedMode("yaml");
makeCommentFixedMode("jinja2");

function makeResizable(editor) {
  const cm = editor.getWrapperElement();
  if (typeof ResizeObserver !== "undefined") {
    new ResizeObserver(function() { editor.refresh(); }).observe(cm);
  }
}

function initEditors() {
  const isDark = document.body.getAttribute("data-theme") !== "light";
  const theme = isDark ? "dracula" : "eclipse";

  templateEditor = CodeMirror.fromTextArea(document.getElementById("j2_template"), {
    mode: "jinja2-comment-fixed",
    theme,
    lineNumbers: true,
    lineWrapping: true,
    autofocus: false,
  });
  makeResizable(templateEditor);

  dataEditor = CodeMirror.fromTextArea(document.getElementById("j2_data"), {
    mode: "yaml-comment-fixed",
    theme,
    lineNumbers: true,
    lineWrapping: true,
    indentWithTabs: false,
    tabSize: 4,
    extraKeys: { Tab: "insertSoftTab" },
  });
  makeResizable(dataEditor);
  // Convert tabs to spaces on paste so YAML indentation is never broken
  // by tab characters (YAML forbids tabs for indentation).
  dataEditor.on("beforeChange", function(cm, change) {
    if (change.origin === "paste") {
      change.text = change.text.map(function(line) {
        return line.replace(/\t/g, "    ");
      });
    }
  });

  outputEditor = CodeMirror(document.getElementById("render_results"), {
    mode: "text/plain",
    theme,
    lineNumbers: true,
    lineWrapping: true,
    readOnly: true,
  });
  outputEditor.setSize(null, "100%");
  makeResizable(outputEditor);

  requestAnimationFrame(function() {
    requestAnimationFrame(function() {
      [templateEditor, dataEditor, outputEditor].forEach(function(ed) {
        if (ed) ed.refresh();
      });
    });
  });
}

function initSplitter() {
  const workspace = document.querySelector(".workspace");
  const splitter = document.getElementById("panel_splitter");
  if (!workspace || !splitter) return;

  const STORAGE_KEY = "yajr_split_left";
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) workspace.style.setProperty("--split-left", saved);

  let dragging = false;

  splitter.addEventListener("mousedown", function(e) {
    e.preventDefault();
    dragging = true;
    splitter.classList.add("dragging");
  });

  document.addEventListener("mousemove", function(e) {
    if (!dragging) return;
    const rect = workspace.getBoundingClientRect();
    const newLeft = Math.max(280, Math.min(e.clientX - rect.left, rect.width - 290));
    const val = newLeft + "px";
    workspace.style.setProperty("--split-left", val);
    [templateEditor, dataEditor, outputEditor].forEach(function(ed) {
      if (ed) ed.refresh();
    });
  });

  document.addEventListener("mouseup", function() {
    if (!dragging) return;
    dragging = false;
    splitter.classList.remove("dragging");
    localStorage.setItem(STORAGE_KEY, getComputedStyle(workspace).getPropertyValue("--split-left").trim());
  });
}

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
  toggle.textContent = mode === "dark" ? "Dark mode" : "Light mode";
  toggle.setAttribute("aria-pressed", mode === "dark" ? "true" : "false");
  localStorage.setItem("yajr_theme", mode);

  const cmTheme = mode === "dark" ? "dracula" : "eclipse";
  [templateEditor, dataEditor, outputEditor].forEach((editor) => {
    if (editor) editor.setOption("theme", cmTheme);
  });
}

function initTheme() {
  const saved = localStorage.getItem("yajr_theme");
  applyTheme(saved || "dark");
}

function toggleTheme() {
  const current = document.body.getAttribute("data-theme") || "dark";
  applyTheme(current === "dark" ? "light" : "dark");
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
    template: templateEditor.getValue(),
    data: dataEditor.getValue(),
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
  const mode = document.querySelector("input[name='render_mode']:checked").value;

  document.getElementById("opt_strict").checked = true;
  document.getElementById("opt_trim").checked = true;
  document.getElementById("opt_lstrip").checked = true;
  document.getElementById("filter_hash").checked = false;
  document.getElementById("filter_ipaddr").checked = false;

  if (mode === "ansible") {
    templateEditor.setValue([
      "{% set ports = {'eth0': 'up', 'eth1': 'down'} | dict2items %}",
      "interfaces_total: {{ ports | length }}",
      "vlan_id: {{ 'vlan-123' | regex_search('[0-9]+') }}",
      "yaml_summary:",
      "{{ {'site': site_name, 'vlans': vlans} | to_nice_yaml(indent=2) }}",
    ].join("\n"));
    templateEditor.refresh();

    dataEditor.setValue([
      "site_name: edge-a",
      "vlans:",
      "  - 10",
      "  - 20",
      "  - 30",
    ].join("\n"));
    dataEditor.refresh();

    setStatus("Loaded Ansible-specific defaults.", false);
    return;
  }

  if (mode === "salt") {
    templateEditor.setValue([
      "{% load_yaml as cfg %}",
      "users:",
      "  - alice",
      "  - bob",
      "{% endload %}",
      "users_json: {{ cfg.users | json }}",
      "quoted_env: {{ env | yaml_dquote }}",
    ].join("\n"));
    templateEditor.refresh();

    dataEditor.setValue([
      "env: prod",
    ].join("\n"));
    dataEditor.refresh();

    setStatus("Loaded Salt-specific defaults.", false);
    return;
  }

  templateEditor.setValue([
    "{% for iface in interfaces %}",
    "interface {{ iface.name }}",
    "  description {{ iface.description | default('N/A') }}",
    "  ip address {{ iface.ip | ipaddr('address') }} {{ iface.ip | ipaddr('network') }}",
    "{% endfor %}",
  ].join("\n"));
  templateEditor.refresh();

  dataEditor.setValue([
    "interfaces:",
    "  - name: Ethernet1",
    "    description: Uplink to core",
    "    ip: 192.0.2.10/24",
    "  - name: Ethernet2",
    "    description: Server VLAN",
    "    ip: 198.51.100.5/24",
  ].join("\n"));
  dataEditor.refresh();
  document.getElementById("filter_ipaddr").checked = true;
  setStatus("Loaded Base Jinja defaults.", false);
}

function applyWhitespaceToggle() {
  const enabled = document.getElementById("toggle_whitespaces").checked;
  if (enabled && !wsOverlayActive) {
    outputEditor.addOverlay(wsOverlay);
    wsOverlayActive = true;
  } else if (!enabled && wsOverlayActive) {
    outputEditor.removeOverlay(wsOverlay);
    wsOverlayActive = false;
  }
}

async function jsonFetch(url, payload) {
  const response = await fetch(url, {
    method: payload ? "POST" : "GET",
    headers: payload ? { "Content-Type": "application/json" } : undefined,
    body: payload ? JSON.stringify(payload) : undefined,
  });

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error(`Server error (${response.status})`);
  }
  if (!response.ok) {
    const detail = data.detail || "Request failed.";
    throw new Error(detail);
  }
  return data;
}

async function renderTemplate(showSuccessStatus) {
  const shouldShowStatus = showSuccessStatus !== false;
  try {
    const data = await jsonFetch("/api/render", currentPayload());
    outputEditor.setValue(data.render_result || "");
    applyWhitespaceToggle();
    if (shouldShowStatus) {
      setStatus("Rendered template.", false);
    }
  } catch (error) {
    setStatus(`Render failed: ${error.message}`, true);
    throw error;
  }
}

async function createShare() {
  try {
    const data = await jsonFetch("/api/share", currentPayload());
    const shareUrl = data.share_url || "";
    document.getElementById("share_url").value = shareUrl;

    if (!shareUrl) {
      setStatus("Share link created, but URL was empty.", true);
      return;
    }

    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(shareUrl);
      } else {
        const ta = document.createElement("textarea");
        ta.value = shareUrl;
        ta.setAttribute("readonly", "");
        ta.style.position = "fixed";
        ta.style.top = "-9999px";
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        const ok = document.execCommand("copy");
        document.body.removeChild(ta);
        if (!ok) {
          throw new Error("execCommand copy failed");
        }
      }
      setStatus("Share link created and copied to clipboard.", false);
    } catch (copyError) {
      setStatus("Share link created, but clipboard copy failed.", true);
    }
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
    templateEditor.setValue(payload.template || "");
    templateEditor.refresh();
    dataEditor.setValue((payload.data || "").replace(/\t/g, "    "));
    dataEditor.refresh();

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

    setStatus("Loaded shared template — click Render to execute.", false);
  } catch (error) {
    setStatus(`Could not load share link: ${error.message}`, true);
  }
}

function clearRender() {
  outputEditor.setValue("");
  setStatus("Render output cleared.", false);
}

async function copyRender() {
  const text = outputEditor.getValue() || "";
  if (!text) {
    setStatus("Nothing to copy yet.", true);
    return;
  }

  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      setStatus("Rendered output copied.", false);
      return;
    }

    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.top = "-9999px";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(ta);
    if (!ok) {
      throw new Error("execCommand copy failed");
    }
    setStatus("Rendered output copied.", false);
  } catch (error) {
    setStatus("Copy failed. Use Ctrl/Cmd+C as fallback.", true);
  }
}

document.getElementById("load_defaults").addEventListener("click", loadDefaults);
document.getElementById("request_render").addEventListener("click", renderTemplate);
document.getElementById("reset_render").addEventListener("click", clearRender);
document.getElementById("copy_render").addEventListener("click", copyRender);
document.getElementById("create_share").addEventListener("click", createShare);
document.getElementById("toggle_whitespaces").addEventListener("change", applyWhitespaceToggle);
document.getElementById("theme_toggle").addEventListener("click", toggleTheme);

initTheme();
initEditors();
initSplitter();
loadShare(window.__INITIAL_SHARE_TOKEN__);
