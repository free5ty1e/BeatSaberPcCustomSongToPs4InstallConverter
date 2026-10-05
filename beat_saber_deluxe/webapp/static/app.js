/* Beat Saber Deluxe web app — Phase 1 client.
 * Vanilla JS (plan §7.1): no build step, same bundle runs on GitHub Pages.
 * Mode detection: /api/ping answers only in local-backend mode; the Pages
 * build stubs it and the app switches to command-builder mode.
 */

"use strict";

// ---------------------------------------------------------------- state
const state = {
  mode: "detecting",           // local-backend | pages
  dumpOk: false,
  connOk: false,
  pickedSong: null,            // slim BeatSaver doc
  catalog: [],                  // albums from /api/catalog
  pollTimer: null,
};

const $ = (id) => document.getElementById(id);

// ---------------------------------------------------------------- mode detection
async function detectMode() {
  try {
    const r = await fetch("/api/ping", { signal: AbortSignal.timeout(2500) });
    const j = await r.json();
    state.mode = j.mode === "local-backend" ? "local-backend" : "unknown";
  } catch {
    state.mode = "pages"; // no backend → command-builder mode
  }
  const badge = $("mode-badge");
  badge.textContent =
    state.mode === "local-backend" ? "● local backend (full function)"
    : state.mode === "pages" ? "◐ pages mode (command builder)"
    : "● checking…";
  badge.className = state.mode === "local-backend" ? "local" : "pages";
  if (state.mode === "pages") {
    document.querySelectorAll(".local-only").forEach(el => el.classList.add("hidden"));
  }
}

// ---------------------------------------------------------------- nav
function showPage(name) {
  document.querySelectorAll("main .page").forEach(p => p.classList.add("hidden"));
  $(`page-${name}`).classList.remove("hidden");
  document.querySelectorAll("#nav button").forEach(b =>
    b.classList.toggle("active", b.dataset.page === name));
}
document.querySelectorAll("#nav button").forEach(b =>
  b.addEventListener("click", () => showPage(b.dataset.page)));
document.addEventListener("click", e => {
  if (e.target.dataset && e.target.dataset.nav) { e.preventDefault(); showPage(e.target.dataset.nav); }
});

// ---------------------------------------------------------------- helpers
async function api(path, opts) {
  const r = await fetch(path, opts);
  if (!r.ok) {
    let msg = `${r.status} ${r.statusText}`;
    try { msg = (await r.json()).detail || msg; } catch { /* keep default */ }
    throw new Error(msg);
  }
  return r.json();
}

function setResult(id, text, cls) {
  const el = $(id);
  el.textContent = text;
  el.className = `result ${cls || ""}`;
}

function nativeDiffBadges(song) {
  const want = ["Easy", "Normal", "Hard"];
  const missing = want.filter(d => !(song.nativeDifficulties || []).includes(d));
  const ok = missing.length === 0;
  return `<span class="badge ${ok ? "ok" : "miss"}">${
    ok ? "E/N/H native" : `missing ${missing.join("/")}`}</span>`;
}

function renderPickedSong() {
  const box = $("picked-song");
  if (!state.pickedSong) { box.classList.add("hidden"); return; }
  const s = state.pickedSong;
  box.classList.remove("hidden");
  $("picked-song-body").innerHTML =
    `<div class="song"><div class="meta"><b>${esc(s.name)}</b>
     <span class="muted">${esc(s.songAuthorName || "?")} — mapped by ${esc(s.levelAuthorName || "?")} ·
     BPM ${s.bpm ?? "?"} · ${s.downloads ?? "?"} downloads</span></div>
     <div class="badges">${nativeDiffBadges(s)}</div></div>
     <div class="muted" style="margin-top:.4rem">Map ID <code>${esc(s.id)}</code>
     ${s.hash ? `· hash <code>${esc(s.hash.slice(0, 12))}…</code>` : ""}</div>`;
}

function esc(s) {
  const d = document.createElement('div');
  d.textContent = String(s ?? '');
  return d.innerHTML;
}

// ---------------------------------------------------------------- wizard
async function checkDump(path) {
  if (!path) { setResult("dump-result", "Enter a dump folder path first.", "bad"); return; }
  setResult("dump-result", "Validating…", "");
  try {
    const j = await api(`/api/dump/validate?path=${encodeURIComponent(path)}`);
    state.dumpOk = j.ok;
    if (j.ok) {
      setResult("dump-result",
        `✅ Valid dump.\nFound DLC packs (${j.dlc_packs_found.length}): ${j.dlc_packs_found.join(", ") || "none"}`,
        "ok");
    } else {
      setResult("dump-result", `❌ Problems found:\n${j.errors.map(e => "• " + e).join("\n")}`, "bad");
    }
    if (j.warnings && j.warnings.length)
      $("dump-result").textContent += `\n⚠ ${j.warnings.join("\n⚠ ")}`;
    updateSaveButton();
  } catch (e) { setResult("dump-result", "Validation failed: " + e.message, "bad"); }
}

async function loadDumpDefault() {
  try {
    const j = await api("/api/dump/default-location");
    $("dump-default-path").textContent = j.default_path;
    if (j.exists) { $("dump-path").value = j.default_path; checkDump(j.default_path); }
  } catch { /* Pages mode: skip */ }
}

async function testConnection() {
  setResult("conn-result", "Testing…", "");
  try {
    const j = await api("/api/ps4/test");
    if (j.ok) {
      state.connOk = true;
      setResult("conn-result",
        `✅ PS4 reachable — ${j.count} files in the AFR dir.`, "ok");
    } else {
      state.connOk = false;
      setResult("conn-result",
        `❌ Couldn't reach the PS4 (${j.error || "no response"}). ` +
        `Check the IP, that GoldHEN's FTP server is running (Settings → GoldHEN → FTP), ` +
        `and that this machine can reach it.`, "bad");
    }
    updateSaveButton();
  } catch (e) { setResult("conn-result", "Test failed: " + e.message, "bad"); }
}

function updateSaveButton() {
  $("btn-save-config").disabled = !state.dumpOk;
  if (state.dumpOk)
    $("btn-save-config").textContent = state.connOk
      ? "Save ps4_config.json" : "Save ps4_config.json (PS4 not verified — that's OK)";
}

async function saveConfig() {
  try {
    const j = await api("/api/config/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dump_root: $("dump-path").value.trim(),
        ps4_ip: $("ps4-ip").value.trim(),
        ftp_port: parseInt($("ps4-port").value, 10) || 2121,
      }),
    });
    setResult("save-result",
      `✅ Saved ${j.config_path}\nSetup complete — go pick a song!`, "ok");
  } catch (e) { setResult("save-result", "Save failed: " + e.message, "bad"); }
}

// ---------------------------------------------------------------- song picker
async function searchBeatSaver() {
  const q = $("bs-query").value.trim();
  if (!q) return;
  $("bs-results").innerHTML = "<p class='muted'>Searching…</p>";
  let docs;
  try {
    const j = await api(`/api/beatsaver/search?q=${encodeURIComponent(q)}&per_page=30`);
    docs = j.docs;
  } catch (e) {
    $("bs-results").innerHTML = `<p class='result bad'>Search failed: ${esc(e.message)}</p>`;
    return;
  }
  const filter = $("bs-filter-enh").checked;
  if (filter) docs = docs.filter(s => s.nativeDifficulties.length === 3);
  if (!docs.length) {
    $("bs-results").innerHTML = "<p class='muted'>No results" +
      (filter ? " with native Easy/Normal/Hard — try unchecking the filter." : ".") + "</p>";
    return;
  }
  $("bs-results").innerHTML = docs.map(s =>
    `<div class="song">
       <div class="meta">
         <b>${esc(s.name)}</b>
         <span class="muted">${esc(s.songAuthorName || "?")} · mapped by ${esc(s.levelAuthorName || "?")} ·
         BPM ${s.bpm ?? "?"} · ${s.downloads ?? "?"} downloads</span>
       </div>
       <div class="badges">${nativeDiffBadges(s)}</div>
       <button class="pick" data-mapid="${esc(s.id)}">Pick</button>
     </div>`).join("");
  $("bs-results").querySelectorAll("button.pick").forEach(b =>
    b.addEventListener("click", () => pickSong(b.dataset.mapid)));
}

async function pickSong(mapId) {
  try {
    state.pickedSong = await api(`/api/beatsaver/map/${encodeURIComponent(mapId)}`);
    renderPickedSong();
    showPage("deployPage");
  } catch (e) {
    alert("Couldn't load map " + mapId + ":\n" + e.message +
      "\n\nMaps do get deleted from BeatSaver — search for the song and pick another upload.");
  }
}

async function lookupMapId() {
  const id = $("bs-mapid").value.trim();
  if (!id) return;
  setResult("bs-mapid-result", "Looking up…", "");
  try {
    state.pickedSong = await api(`/api/beatsaver/map/${encodeURIComponent(id)}`);
    setResult("bs-mapid-result", `✅ Found: ${state.pickedSong.name}`, "ok");
    renderPickedSong();
    showPage("deployPage");
  } catch (e) { setResult("bs-mapid-result", "❌ " + e.message, "bad"); }
}

// ---------------------------------------------------------------- deploy
function loadCatalogIntoPicker() {
  const packSel = $("deploy-pack");
  packSel.innerHTML = "<option value=''>Pack…</option>";
  const slotSel = $("deploy-slot");
  slotSel.innerHTML = "<option value=''>Slot…</option>";
  state.catalog.forEach(album => {
    const opt = document.createElement("option");
    opt.value = album.pack;
    opt.textContent = `${album.pack} (${album.songs.length} songs)`;
    packSel.appendChild(opt);
  });
  packSel.onchange = () => {
    slotSel.innerHTML = "<option value=''>Slot…</option>";
    const album = state.catalog.find(a => a.pack === packSel.value);
    (album ? album.songs : []).forEach(s => {
      const opt = document.createElement("option");
      opt.value = s.songID;
      opt.textContent = `${s.songID} — ${s.songName} (${s.songAuthorName})`;
      slotSel.appendChild(opt);
    });
    slotSel.onchange = updateDeployPreview;
    updateDeployPreview();
  };
  updateDeployPreview();
}

function currentOpts() {
  return {
    map_id: state.pickedSong ? state.pickedSong.id : "",
    target: $("deploy-slot").value,
    audio: $("opt-audio").value,
    pad_fsb5: $("opt-pad").checked,
    convert_to_v3: $("opt-v3").checked,
    deploy_full: true,
    skip_plugin: $("opt-skip-plugin").checked,
    song_name: $("opt-songname").value.trim(),
    artist: $("opt-artist").value.trim(),
  };
}

async function updateDeployPreview() {
  const slotSel = $("deploy-slot");
  const info = $("deploy-slot-info");
  const album = state.catalog.find(a => a.pack === $("deploy-pack").value);
  const song = album && album.songs.find(s => s.songID === slotSel.value);
  info.textContent = song
    ? `Stock song: "${song.songName}" by ${song.songAuthorName}`
    : "";
  $("deploy-slot-label").textContent = song
    ? `"${song.songName}" (${song.songID})` : "…";
  const o = currentOpts();
  if (!o.map_id || !o.target) {
    $("deploy-command").textContent = state.pickedSong
      ? "→ pick a target slot to preview the command"
      : "→ pick a song first (Pick a Song tab)";
    return;
  }
  try {
    const j = await api(`/api/command-preview?map_id=${encodeURIComponent(o.map_id)}` +
      `&target=${encodeURIComponent(o.target)}&audio=${o.audio}` +
      `&pad_fsb5=${o.pad_fsb5}&convert_to_v3=${o.convert_to_v3}` +
      `&skip_plugin=${o.skip_plugin}`);
    $("deploy-command").textContent = "→ " + j.command;
  } catch (e) { $("deploy-command").textContent = "→ " + e.message; }
}

async function deploy() {
  const o = currentOpts();
  if (!o.map_id || !o.target) {
    setResult("deploy-status", "Pick a song and a target slot first.", "bad");
    return;
  }
  const label = $("deploy-slot-label").textContent;
  if (!confirm(
    `Deploy "${state.pickedSong.name}" over ${label}?\n\n` +
    `This downloads the map, builds the bundle (all modes), deploys it to the PS4 ` +
    `with the plugin + features + pack bundle, regenerates redirects, and runs ` +
    `post-deploy validation. The other songs in the pack and every other pack ` +
    `stay untouched.`)) return;

  setResult("deploy-status", "", "");
  $("deploy-log").classList.remove("hidden");
  $("deploy-log").textContent = "";
  $("deploy-progress").scrollIntoView({ behavior: "smooth", block: "start" });
  const deployBtn = $("btn-deploy");
  deployBtn.disabled = true;
  deployBtn.innerHTML = '<span class="spinner spinning"></span> Deploying…';
  $("btn-deploy-cancel").classList.remove("hidden");
  setDeployProgress(true, "Deploying", `${state.pickedSong.name} → ${label}`);
  try {
    const j = await api("/api/jobs/deploy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(o),
    });
    pollLog(0);
  } catch (e) {
    setResult("deploy-status", "❌ " + e.message, "bad");
    deployBtn.disabled = false;
    deployBtn.innerHTML = "Deploy to PS4";
    $("btn-deploy-cancel").classList.add("hidden");
    setDeployProgress(false);
  }
}

function setDeployProgress(show, status, label) {
  const row = $("deploy-progress");
  if (!row) return;
  row.hidden = !show;
  row.classList.toggle("hidden", !show);
  if (show) {
    $("deploy-progress-status").textContent = status || "Working…";
    $("deploy-progress-label").textContent = label || "";
  }
}

let pollIndex = 0;
function pollLog() {
  api(`/api/jobs/lines?after=${pollIndex}`)
    .then(j => {
      if (j.lines && j.lines.length) {
        const logEl = $("deploy-log");
        logEl.textContent += j.lines.join("\n") + "\n";
        logEl.scrollTop = logEl.scrollHeight;
      }
      pollIndex = j.index || pollIndex;
      if (j.running) {
        state.pollTimer = setTimeout(pollLog, 900);
      } else if (j.job) {
        finishJob(j.job);
      }
    })
    .catch(() => { state.pollTimer = setTimeout(pollLog, 1500); });
}

function finishJob(job) {
  $("btn-deploy").disabled = false;
  $("btn-deploy").innerHTML = "Deploy to PS4";
  $("btn-deploy-cancel").classList.add("hidden");
  setDeployProgress(false);
  if (job.cancelled) {
    setResult("deploy-status", "⛔ Cancelled. The PS4 may hold a partial deploy — " +
      "run Verify, or re-deploy to complete it.", "warn");
    return;
  }
  if (job.exit_code === 0) {
    setResult("deploy-status", "✅ Deploy PASSED (post-deploy validation green). " +
      "Launch the game and check your song!", "ok");
    $("btn-verify").classList.remove("hidden");
  } else {
    setResult("deploy-status", `❌ Deploy FAILED (exit ${job.exit_code}). ` +
      "Read the log above — the pipeline prints exactly what went wrong.", "bad");
  }
}

async function cancelJob() {
  try { await api("/api/jobs/cancel", { method: "POST" }); }
  catch (e) { /* runner gone — poll loop will notice */ }
}

// ---------------------------------------------------------------- manage + loadout
let loadoutData = null;   // last /api/loadout payload (re-render on filter change)

async function fetchLoadout() {
  const errs = [];
  try {
    loadoutData = await api("/api/loadout");
  } catch (e) {
    loadoutData = null;
    errs.push(e.message);
  }
  return loadoutData;
}

function renderReadErrors(status, el) {
  if (!status) { el.innerHTML = ""; return; }
  const bits = [];
  if (status.redirectsReadError)
    bits.push(`<span class="result bad">⚠ Couldn't read redirects.json from the PS4
      (${esc(status.redirectsReadError)}). "Served" status unknown — check the
      connection and refresh.</span>`);
  if (status.afrReadError)
    bits.push(`<span class="result warn">⚠ Couldn't list the AFR folder on the PS4
      (${esc(status.afrReadError)}). Stale-bundle detection unavailable.</span>`);
  if (status.metadataReadError)
    bits.push(`<span class="result warn">⚠ Couldn't read song_metadata.json from the PS4
      (${esc(status.metadataReadError)}). Custom names unavailable — showing slots only.</span>`);
  el.innerHTML = bits.join(" ");
}

function customCell(row) {
  if (row.customDeployed) {
    const name = row.customName || "(name unavailable)";
    const artist = row.customArtist || "";
    return `<td><span class="badge ok">custom</span></td>
            <td><b>${esc(name)}</b>${artist ? ` <span class="muted">/ ${esc(artist)}</span>` : ""}</td>`;
  }
  if (row.staleBundle) {
    return `<td><span class="badge miss" title="Bundle file on PS4 but no redirect — uploaded by an earlier deploy, not currently served">stale</span></td>
            <td class="muted">bundle on PS4, not served (no redirect)</td>`;
  }
  if (row.customName) {
    return `<td><span class="badge miss" title="Name/artist relabeled in the UI but no custom bundle is served over this slot">label only</span></td>
            <td><b>${esc(row.customName)}</b>${row.customArtist ? ` <span class="muted">/ ${esc(row.customArtist)}</span>` : ""}</td>`;
  }
  return `<td class="muted">—</td><td class="muted">stock</td>`;
}

function clearButton(row, refreshFn) {
  if (!row.customDeployed && !row.staleBundle && !row.customName) return "<td></td>";
  return `<td><button class="clear-slot danger" data-slot="${esc(row.songID)}"
      data-stock="${esc(row.songName)}">Clear</button></td>`;
}

function wireClearButtons(container, refreshFn, panelId) {
  container.querySelectorAll("button.clear-slot").forEach(b =>
    b.addEventListener("click", async () => {
      const slot = b.dataset.slot, stock = b.dataset.stock;
      if (!confirm(
        `Revert "${stock}" (${slot}) back to stock?\n\n` +
        `This removes ONLY this song's custom bundle, redirect, and metadata — ` +
        `the other songs in its pack and every other pack stay untouched.`))
        return;
      b.disabled = true;
      b.textContent = "clearing…";
      try {
        const j = await api("/api/jobs/clear-target", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ slot }),
        });
        if (panelId) {
          showJobPanel(panelId, { label: `clear ${stock} (${slot})`, command: j.command });
          await runJobWithPanel(panelId, j, { doneLabel: `${stock} reverted to stock` });
          await refreshFn();
        } else {
          // legacy inline poll (no panel on this page)
          pollIndex = 0;
          const poll = async () => {
            try {
              const j2 = await api(`/api/jobs/lines?after=${pollIndex}`);
              pollIndex = j2.index || pollIndex;
              if (j2.running) { setTimeout(poll, 900); return; }
              if (j2.job && j2.job.exit_code === 0) { await refreshFn(); }
              else { b.disabled = false; b.textContent = "Clear";
                     alert(`Clear failed (exit ${j2.job ? j2.job.exit_code : "?"}) — see the job output.`); }
            } catch { setTimeout(poll, 1500); }
          };
          poll();
        }
      } catch (e) {
        b.disabled = false; b.textContent = "Clear";
        alert("Couldn't start the clear job: " + e.message);
      }
      b.disabled = false; b.textContent = "Clear";
    }));
}

async function manageRefresh() {
  const packSel = $("manage-pack");
  const body = $("manage-table").querySelector("tbody");
  body.innerHTML = "<tr><td colspan='6' class='muted'>Reading PS4 state…</td></tr>";
  await fetchLoadout();
  if (!loadoutData) {
    body.innerHTML = `<tr><td colspan='6' class='result bad'>Couldn't load: ${esc("see errors above")}</td></tr>`;
    return;
  }
  renderReadErrors(loadoutData.readStatus, $("manage-read-errors"));
  const pack = packSel.value;
  const album = loadoutData.packs.find(p => p.pack === pack);
  const named = album ? album.songs.filter(s => s.customName).length : 0;
  $("manage-pack-title").textContent = album
    ? `${album.pack} — ${album.deployedCount} served / ${named} labeled / ${album.songs.length} songs`
    : "Songs";
  if (!album) { body.innerHTML = ""; return; }
  body.innerHTML = album.songs.map(row =>
    `<tr class="${row.customDeployed ? "has-custom" : ""}">
       <td><code>${esc(row.songID)}</code></td>
       <td>${esc(row.songName)}</td>
       <td>${esc(row.songAuthorName)}</td>
       ${customCell(row)}
       ${clearButton(row)}
     </tr>`).join("");
  wireClearButtons(body, manageRefresh, "manage-job-panel");
}

async function loadManagePacks() {
  const packSel = $("manage-pack");
  try {
    const j = await api("/api/loadout/packs");
    packSel.innerHTML = "";
    j.packs.forEach(p => {
      const opt = document.createElement("option");
      opt.value = p;
      opt.textContent = `${p} (${j.songCounts[p]} songs)`;
      packSel.appendChild(opt);
    });
  } catch (e) {
    packSel.innerHTML = `<option value=''>couldn't load packs: ${esc(e.message)}</option>`;
    return;
  }
  packSel.onchange = manageRefresh;
  // default to the first pack with anything custom (served or labeled)
  await fetchLoadout();
  if (loadoutData) {
    const withCustoms = loadoutData.packs.find(
      p => p.deployedCount > 0 || p.songs.some(s => s.customName || s.staleBundle));
    if (withCustoms) packSel.value = withCustoms.pack;
  }
  manageRefresh();
}

function renderLoadoutTables() {
  const host = $("loadout-tables");
  if (!loadoutData) { host.innerHTML = "<p class='result bad'>No data — refresh.</p>"; return; }
  renderReadErrors(loadoutData.readStatus, $("loadout-read-errors"));
  const onlyCustom = $("loadout-only-custom").checked;
  const packs = onlyCustom
    ? loadoutData.packs.filter(
        p => p.deployedCount > 0 || p.songs.some(s => s.customName || s.staleBundle))
    : loadoutData.packs;
  $("loadout-summary").textContent =
    `${loadoutData.redirectedSlotCount} custom songs served · ` +
    `${loadoutData.staleBundleCount} stale bundles (uploaded, not served) · ` +
    `${loadoutData.customNameCount} metadata entries · ${loadoutData.packs.length} packs total` +
    (loadoutData.unmatchedMetadata.length
      ? ` · ${loadoutData.unmatchedMetadata.length} metadata entries matched no slot` : "");
  $("loadout-generated").textContent = new Date().toLocaleString();

  host.innerHTML = packs.map(album => `
    <div class="card loadout-pack">
      <h3>${esc(album.pack)} <span class="muted">(${album.deployedCount} served /
        ${album.songs.filter(s => s.customName).length} labeled / ${album.songs.length} songs)</span></h3>
      <table class="loadout">
        <thead><tr><th>Slot</th><th>Stock song</th><th>Stock artist</th>
          <th>Custom?</th><th>Custom song / artist</th><th></th></tr></thead>
        <tbody>
          ${album.songs.map(row =>
            `<tr class="${row.customDeployed ? "has-custom" : ""}">
               <td><code>${esc(row.songID)}</code></td>
               <td>${esc(row.songName)}</td>
               <td>${esc(row.songAuthorName)}</td>
               ${customCell(row)}
               ${clearButton(row)}
             </tr>`).join("")}
        </tbody>
      </table>
    </div>`).join("")
    || "<p class='muted'>No packs match the current filter.</p>";
  wireClearButtons(host, async () => { await fetchLoadout(); renderLoadoutTables(); }, "loadout-job-panel");
}

async function loadoutRefresh() {
  const btn = $("btn-loadout-refresh");
  btn.disabled = true; btn.textContent = "Reading PS4…";
  await fetchLoadout();
  renderLoadoutTables();
  btn.disabled = false; btn.textContent = "Refresh from PS4";
}

// ---------------------------------------------------------------- feature flags
const FLAG_ORDER = ["enable_plugin", "enable_custom_song_replacements",
                     "enable_song_metadata_modification", "enable_beatmap_mode_mapping"];
// NOTE: the pipeline's canonical key is the PLURAL enable_custom_song_replacements.
let flagsDirty = false;

// Simulated PS4 launch toast — mirrors the plugin's exact format
// (main.cpp module_start): "BS Deluxe vX (ON)\nBy Chris Primeish\n(N/3 features ON)"
// — or "(OFF) … (official songs only)" when the kill switch is off.
const TOAST_VERSION = "v0.8047";
const FEATURE_FLAG_KEYS = ["enable_custom_song_replacements",
                           "enable_song_metadata_modification",
                           "enable_beatmap_mode_mapping"];

function updateToastSim() {
  const checks = $("flags-list").querySelectorAll("input[type=checkbox]");
  if (!checks.length) return;
  const state = {};
  checks.forEach(cb => { state[cb.dataset.flag] = cb.checked; });
  const on = state["enable_plugin"];
  const count = FEATURE_FLAG_KEYS.filter(k => state[k]).length;
  $("toast-title").textContent = `BS Deluxe ${TOAST_VERSION} ${on ? "(ON)" : "(OFF)"}`;
  $("toast-count").textContent = on
    ? `(${count}/3 features ON)`
    : "(official songs only)";
  $("toast-note").textContent = on
    ? "With these toggles, the next boot shows this toast and the features above are active."
    : "Kill switch OFF: the toast reads (official songs only) and the game is 100% stock — your deployments stay on the PS4 untouched.";
}

async function flagsRefresh() {
  const host = $("flags-list");
  host.innerHTML = "<p class='muted'>Reading flags from the PS4…</p>";
  try {
    const j = await api("/api/flags");
    if (!j.ok) {
      host.innerHTML = `<span class="result bad">Couldn't read flags from the PS4
        (${esc(j.error)}). Check the connection, then refresh.</span>`;
      $("btn-flags-apply").disabled = true;
      return;
    }
    host.innerHTML = j.flags
      .sort((a, b) => FLAG_ORDER.indexOf(a.name) - FLAG_ORDER.indexOf(b.name))
      .map(f => `
        <div class="flag-row">
          <label class="chk">
            <input type="checkbox" data-flag="${esc(f.name)}" ${f.value ? "checked" : ""}
                   ${f.name === "enable_plugin" ? "data-killswitch='1'" : ""}>
            <b>${esc(f.name)}</b> ${f.pending ? `<span class="badge miss">pending → ${f.pendingValue ? "ON" : "OFF"}</span>` : ""}
          </label>
          <div class="muted flag-desc">${esc(f.description)}</div>
        </div>`).join("");
    host.querySelectorAll("input[type=checkbox]").forEach(cb =>
      cb.addEventListener("change", () => {
        flagsDirty = true;
        $("btn-flags-apply").disabled = false;
        $("flags-apply-status").textContent = "";
        if (cb.dataset.killswitch && !cb.checked) {
          $("flags-apply-status").innerHTML =
            "<span class='result warn'>⚠ Kill switch going OFF — the game will play 100% official songs next boot.</span>";
        }
        updateToastSim();
      }));
    flagsDirty = false;
    $("btn-flags-apply").disabled = true;
    $("flags-read-error").textContent = "";
    updateToastSim();
  } catch (e) {
    host.innerHTML = `<span class="result bad">${esc(e.message)}</span>`;
  }
}

async function flagsApply() {
  const wanted = {};
  $("flags-list").querySelectorAll("input[type=checkbox]").forEach(cb => {
    wanted[cb.dataset.flag] = cb.checked;
  });
  const turningOff = wanted["enable_plugin"] === false;
  const msg = turningOff
    ? "Turn the ENTIRE plugin OFF?\n\nNext boot plays 100% official songs (your customs stay deployed and come back the moment you re-enable)."
    : "Apply this flag loadout to the PS4?\n\nTakes effect on the next game boot.";
  if (!confirm(msg)) return;
  const applyBtn = $("btn-flags-apply");
  applyBtn.disabled = true;
  applyBtn.innerHTML = '<span class="spinner spinning"></span> Applying…';
  $("flags-apply-status").textContent = "";
  try {
    const j = await api("/api/jobs/flags-apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ flags: wanted }),
    });
    if (j.job_id === null) {
      applyBtn.innerHTML = "Apply to PS4";
      $("flags-apply-status").innerHTML =
        `<span class="result ok">✅ ${esc(j.message)}</span>`;
      flagsRefresh();
      return;
    }
    flagsDirty = false;
    pollJobInto("flags-log", "flags-apply-status", () => {
      applyBtn.innerHTML = "Apply to PS4";
      flagsRefresh();
    });
  } catch (e) {
    applyBtn.disabled = false;
    applyBtn.innerHTML = "Apply to PS4";
    $("flags-apply-status").innerHTML = `<span class="result bad">❌ ${esc(e.message)}</span>`;
  }
}

// ---------------------------------------------------------------- job panel
// The shared live-output surface: every command the app launches (deploy,
// verify, flags-apply, backup, restore, clear) renders here — spinner +
// status + the exact command + a live console. One job at a time (the
// runner enforces it; the UI makes it visible).
function showJobPanel(panelId, { label, command }) {
  const panel = $(panelId);
  panel.classList.remove("hidden");
  $(panelId + "-status").textContent = "Working…";
  $(panelId + "-label").textContent = label || "";
  $(panelId + "-spinner").classList.add("spinning");
  $(panelId + "-command").textContent = command ? "→ " + command : "";
  $(panelId + "-log").textContent = "";
  // The panels sit at the TOP of their pages (above long tables) so the
  // spinner + live output are always in view while a job runs (Exp 253:
  // they used to live below everything and the user saw nothing).
  window.scrollTo({ top: 0, behavior: "smooth" });
  panel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function finishJobPanel(panelId, job) {
  const spinner = $(panelId + "-spinner");
  spinner.classList.remove("spinning");
  const status = $(panelId + "-status");
  if (job.cancelled) {
    status.textContent = "⛔ Cancelled — the PS4 may hold partial state; verify or re-run.";
    status.className = "job-status warn";
  } else if (job.exit_code === 0) {
    status.textContent = "✅ Done";
    status.className = "job-status ok";
  } else {
    status.textContent = `❌ FAILED (exit ${job.exit_code}) — read the output above`;
    status.className = "job-status bad";
  }
}

function runJobWithPanel(panelId, startResponse, { doneLabel } = {}) {
  // Poll the runner's shared job lines into the panel's console.
  // Returns a Promise that resolves when the job ENDS — callers awaiting it
  // (clear → refresh) act at the right moment (Exp 253: the fire-and-forget
  // version resolved immediately and the table refreshed mid-job).
  return new Promise((resolve) => {
    let idx = 0;
    const logEl = $(panelId + "-log");
    const poll = async () => {
      try {
        const j = await api(`/api/jobs/lines?after=${idx}`);
        if (j.lines && j.lines.length) {
          logEl.textContent += j.lines.join("\n") + "\n";
          logEl.scrollTop = logEl.scrollHeight;
        }
        idx = j.index || idx;
        if (j.running) { setTimeout(poll, 900); return; }
        if (j.job) {
          finishJobPanel(panelId, j.job);
          if (doneLabel && j.job.exit_code === 0) {
            $(panelId + "-label").textContent = doneLabel;
          }
          resolve(j.job);
        } else {
          resolve(null);
        }
      } catch { setTimeout(poll, 1500); }
    };
    poll();
  });
}

// shared job poller for legacy call sites (flags page)
function pollJobInto(logId, statusId, afterFn) {
  let idx = 0;
  const poll = async () => {
    try {
      const j = await api(`/api/jobs/lines?after=${idx}`);
      if (j.lines && j.lines.length) {
        const el = $(logId);
        el.textContent += j.lines.join("\n") + "\n";
        el.classList.remove("hidden");
      }
      idx = j.index || idx;
      if (j.running) { setTimeout(poll, 900); return; }
      if (j.job) {
        const s = $(statusId);
        if (j.job.cancelled) {
          s.innerHTML = "<span class='result warn'>⛔ Job cancelled — the PS4 may hold partial state; run a backup or verify.</span>";
        } else if (j.job.exit_code === 0) {
          s.innerHTML = "<span class='result ok'>✅ Done.</span>";
        } else {
          s.innerHTML = `<span class='result bad'>❌ Job FAILED (exit ${j.job.exit_code}) — read the log above.</span>`;
        }
        $("btn-job-cancel") && $("btn-job-cancel").classList.add("hidden");
        afterFn && afterFn();
      }
    } catch { setTimeout(poll, 1500); }
  };
  poll();
}

// ---------------------------------------------------------------- backup / restore
async function backupRefresh() {
  const body = $("backup-table").querySelector("tbody");
  body.innerHTML = "<tr><td colspan='4' class='muted'>Listing backups…</td></tr>";
  try {
    const j = await api("/api/backup/list");
    $("backup-dir-display").textContent = j.backup_dir;
    if (!j.backups.length) {
      body.innerHTML = `<tr><td colspan='4' class='muted'>No backups yet in
        <code>${esc(j.backup_dir)}</code> — make one before experimenting.</td></tr>`;
      return;
    }
    body.innerHTML = j.backups.map(b => `
      <tr>
        <td><code>${esc(b.name)}</code></td>
        <td>${(b.size / 1024).toFixed(0)} KB</td>
        <td>${new Date(b.mtime * 1000).toLocaleString()}</td>
        <td><button class="restore-backup" data-name="${esc(b.name)}">Restore</button></td>
      </tr>`).join("");
    body.querySelectorAll("button.restore-backup").forEach(btn =>
      btn.addEventListener("click", () => backupRestore(btn.dataset.name)));
  } catch (e) {
    body.innerHTML = `<tr><td colspan='4' class='result bad'>${esc(e.message)}</td></tr>`;
  }
}

// backups-folder browser (server lists dirs; the picker is folder-only)
let browsePath = null;

async function browseLoad(path) {
  try {
    const j = await api(`/api/backup/browse?path=${encodeURIComponent(path || "")}`);
    browsePath = j.path;
    $("browse-crumbs").textContent = j.path;
    $("browse-path-input").value = j.path;
    $("browse-list").innerHTML = j.dirs.length
      ? j.dirs.map(d =>
          `<div class="browse-entry" data-path="${esc(d.path)}">📁 ${esc(d.name)}</div>`).join("")
      : "<p class='muted' style='padding:.4rem'>No subfolders here.</p>";
    $("browse-list").querySelectorAll(".browse-entry").forEach(el =>
      el.addEventListener("click", () => browseLoad(el.dataset.path)));
    $("btn-browse-up").disabled = !j.parent;
    $("btn-browse-up").onclick = () => j.parent && browseLoad(j.parent);
  } catch (e) {
    $("browse-crumbs").textContent = "couldn't browse: " + e.message;
  }
}

async function backupChooseFolder(path) {
  try {
    const j = await api("/api/backup/dir", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path }),
    });
    $("backup-browser").classList.add("hidden");
    $("backup-dir-display").textContent = j.backup_dir;
    backupRefresh();
  } catch (e) {
    alert("Couldn't set the backups folder: " + e.message);
  }
}

async function backupNow() {
  const clean = $("backup-clean-ps4").checked;
  if (clean && !confirm(
    "Backup AND clean the PS4?\n\nThe backup will be made first, then every BS " +
    "Deluxe file is wiped from the console (fresh-slate redeploy posture). " +
    "The backup zip is your only safety net — make sure it completes."))
    return;
  if (!clean && !confirm("Backup the PS4's BS Deluxe state now?")) return;
  const btn = $("btn-backup-now");
  btn.disabled = true; btn.textContent = "Backing up…";
  try {
    const j = await api("/api/jobs/backup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ clean_ps4: clean }),
    });
    showJobPanel("backup-job-panel", {
      label: clean ? "backup + clean PS4" : "backup",
      command: j.command,
    });
    await runJobWithPanel("backup-job-panel", j, { doneLabel: "backup complete" });
    // refresh the list when the job ends (poll resolves only at completion)
    setTimeout(backupRefresh, 1500);
    btn.disabled = false; btn.textContent = "Backup now";
  } catch (e) {
    btn.disabled = false; btn.textContent = "Backup now";
    alert("Couldn't start the backup: " + e.message);
  }
}

async function backupRestore(name) {
  if (!confirm(
    `Restore "${name}" to the PS4?\n\n` +
    `This overwrites the console's current BS Deluxe state (bundles, redirects, ` +
    `metadata, features) with the backup's contents. The current state is NOT ` +
    `saved automatically — make a fresh backup first if you might want it back.`))
    return;
  try {
    const j = await api("/api/jobs/restore", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ backup: name, clean_ps4: false }),
    });
    showJobPanel("backup-job-panel", { label: `restore ${name}`, command: j.command });
    await runJobWithPanel("backup-job-panel", j, { doneLabel: `restored ${name}` });
    setTimeout(backupRefresh, 1500);
  } catch (e) {
    alert("Couldn't start the restore: " + e.message);
  }
}

// ---------------------------------------------------------------- feature request
const FR_REPO = "free5ty1e/BeatSaberPcCustomSongToPs4InstallConverter";

function frCompose() {
  const title = $("fr-title").value.trim();
  const body = $("fr-body").value.trim();
  if (!title || !body) {
    $("fr-status").textContent = "Fill in both the summary and the details first.";
    return null;
  }
  let text = `### Feature request (from the web app)\n\n${body}\n`;
  if ($("fr-include-state").checked) {
    text += `\n---\n**App context:** web app mode=${state.mode}`;
    if (loadoutData) {
      const packs = loadoutData.packs.filter(p => p.deployedCount > 0)
        .map(p => `${p.pack} (${p.deployedCount})`).join(", ");
      text += ` · deployed packs: ${packs || "none read yet"}`;
    }
    text += `\n`;
  }
  return { title, body: text };
}

function frPreview() {
  const issue = frCompose();
  if (!issue) return;
  $("fr-preview").textContent =
    `Title: [webapp] ${issue.title}\n\n${issue.body}`;
  $("fr-preview-box").classList.remove("hidden");
  $("btn-fr-open").classList.remove("hidden");
  $("fr-status").textContent = "";
}

function frOpen() {
  const issue = frCompose();
  if (!issue) return;
  const url = `https://github.com/${FR_REPO}/issues/new`
    + `?title=${encodeURIComponent("[webapp] " + issue.title)}`
    + `&body=${encodeURIComponent(issue.body)}`;
  window.open(url, "_blank", "noopener");
}

// ---------------------------------------------------------------- ps4 page
async function refreshPs4() {
  const el = $("ps4-state");
  el.innerHTML = '<div class="row"><span class="spinner spinning"></span> ' +
    'Reading PS4 state (banner-free transport)…</div>';
  try {
    const j = await api("/api/ps4/state");
    const rows = [];
    const red = j.redirects, feat = j.features, meta = j.song_metadata;
    rows.push(["PS4 redirects", red.ok
      ? `${red.song_count} song redirects · ${red.pack_count} pack redirects · catalog redirect ${red.catalog_redirect_present ? "present" : "absent"}`
      : `couldn't read (${red.error})`]);
    rows.push(["Feature flags", feat.ok
      ? Object.entries(feat).filter(([k]) => k.startsWith("enable_"))
          .map(([k, v]) => `${k}=${v ? "ON" : "OFF"}`).join(" · ")
      : `couldn't read (${feat.error})`]);
    rows.push(["Song metadata", meta.ok
      ? `${meta.custom_song_count} custom song names deployed`
      : `couldn't read (${meta.error})`]);
    el.innerHTML = "<table>" + rows.map(([k, v]) =>
      `<tr><th>${esc(k)}</th><td>${esc(v)}</td></tr>`).join("") + "</table>";
  } catch (e) {
    el.innerHTML = `<span class='result bad'>Couldn't read PS4 state: ${esc(e.message)}</span>`;
  }
}

// ---------------------------------------------------------------- boot
async function boot() {
  await detectMode();
  if (state.mode === "local-backend") {
    loadDumpDefault();
    try {
      const cfg = await api("/api/config");
      if (cfg.ps4 && cfg.ps4.ip) $("ps4-ip").value = cfg.ps4.ip;
      if (cfg.ps4 && cfg.ps4.ftp_port) $("ps4-port").value = cfg.ps4.ftp_port;
      state.catalog = (await api("/api/catalog")).albums;
      loadCatalogIntoPicker();
    } catch { /* wizard-first flow */ }
    loadManagePacks();   // Manage Songs dropdown (catalog-only — works offline)
    fillVersionBadge();  // live versions from the running server
  }
}

// ---------------------------------------------------------------- versions
async function fillVersionBadge() {
  try {
    const j = await api("/api/ping");
    if (j.webapp_version) $("ver-webapp").innerHTML = `web app <b>${esc(j.webapp_version)}</b>`;
    if (j.pipeline_version) $("ver-pipeline").innerHTML = `pipeline <b>${esc(j.pipeline_version)}</b>`;
    if (j.plugin_version) $("ver-plugin").innerHTML = `plugin <b>${esc(j.plugin_version)}</b>`;
  } catch { /* pages mode bakes versions at build time; badge hidden if absent */ }
}

document.addEventListener("DOMContentLoaded", () => {
  boot();
  $("btn-dump-check").addEventListener("click", () => checkDump($("dump-path").value.trim()));
  $("btn-dump-default").addEventListener("click", loadDumpDefault);
  $("btn-conn-test").addEventListener("click", testConnection);
  $("btn-save-config").addEventListener("click", saveConfig);
  $("btn-bs-search").addEventListener("click", searchBeatSaver);
  $("bs-query").addEventListener("keydown", e => { if (e.key === "Enter") searchBeatSaver(); });
  $("bs-filter-enh").addEventListener("change", searchBeatSaver);
  $("btn-bs-lookup").addEventListener("click", lookupMapId);
  $("deploy-pack").addEventListener("change", () => {});
  ["opt-audio", "opt-v3", "opt-skip-plugin", "opt-pad", "opt-songname", "opt-artist"]
    .forEach(id => $(id).addEventListener("change", updateDeployPreview));
  $("opt-songname").addEventListener("input", updateDeployPreview);
  $("opt-artist").addEventListener("input", updateDeployPreview);
  $("btn-deploy").addEventListener("click", deploy);
  $("btn-deploy-cancel").addEventListener("click", cancelJob);
  $("btn-verify").addEventListener("click", async () => {
    const btn = $("btn-verify");
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner spinning"></span> Verifying…';
    setDeployProgress(true, "Verifying", "read-only PS4 validation");
    $("deploy-log").classList.remove("hidden");
    $("deploy-log").textContent = "";
    setResult("deploy-status", "", "");
    try {
      await api("/api/jobs/verify", { method: "POST" });
      pollIndex = 0;
      // pollLog's finishJob re-enables the deploy button; restore verify's too
      const origFinish = finishJob;
      pollLog();
      const restore = setInterval(() => {
        if (!btn.isConnected || btn.disabled === false) return;
        btn.disabled = false; btn.innerHTML = "Verify PS4";
      }, 1000);
      setTimeout(() => clearInterval(restore), 120000);
    } catch (e) {
      btn.disabled = false; btn.innerHTML = "Verify PS4";
      setDeployProgress(false);
      setResult("deploy-status", "❌ " + e.message, "bad");
    }
  });
  $("btn-ps4-refresh").addEventListener("click", refreshPs4);
  $("btn-manage-refresh").addEventListener("click", manageRefresh);
  $("btn-loadout-refresh").addEventListener("click", loadoutRefresh);
  $("loadout-only-custom").addEventListener("change", renderLoadoutTables);
  $("btn-flags-refresh").addEventListener("click", flagsRefresh);
  $("btn-flags-apply").addEventListener("click", flagsApply);
  $("btn-backup-now").addEventListener("click", backupNow);
  $("btn-backup-refresh").addEventListener("click", backupRefresh);
  $("btn-backup-browse").addEventListener("click", () => {
    const box = $("backup-browser");
    box.classList.toggle("hidden");
    if (!box.classList.contains("hidden")) browseLoad("");
  });
  $("btn-browse-go").addEventListener("click", () =>
    browseLoad($("browse-path-input").value.trim()));
  $("btn-browse-choose").addEventListener("click", () =>
    browsePath && backupChooseFolder(browsePath));
  $("btn-backup-reset-dir").addEventListener("click", async () => {
    try {
      const def = await api("/api/backup/dir");
      await backupChooseFolder(def.default);
    } catch (e) { alert(e.message); }
  });
  $("btn-job-cancel").addEventListener("click", cancelJob);
  $("btn-fr-preview").addEventListener("click", frPreview);
  $("btn-fr-open").addEventListener("click", frOpen);
  // lazy-load tab data on first visit
  document.querySelectorAll("#nav button").forEach(b =>
    b.addEventListener("click", () => {
      if (b.dataset.page === "flagsPage") flagsRefresh();
      if (b.dataset.page === "backupPage") backupRefresh();
    }));
  showPage("wizard");
});
