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
    filters: [],
  };
}

async function renderTemplate() {
  const payload = currentPayload();
  const response = await fetch("/api/render", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  document.getElementById("render_results").textContent = data.render_result || "";
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
}

document.getElementById("request_render").addEventListener("click", renderTemplate);
document.getElementById("create_share").addEventListener("click", createShare);

document.getElementById("reset_render").addEventListener("click", function () {
  document.getElementById("render_results").textContent = "";
});

document.getElementById("copy_render").addEventListener("click", function () {
  navigator.clipboard.writeText(document.getElementById("render_results").textContent || "");
});

loadShare(window.__INITIAL_SHARE_TOKEN__);
