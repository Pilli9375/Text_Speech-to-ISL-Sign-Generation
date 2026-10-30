const $ = (id) => document.getElementById(id);
const state = {
  queue: [],
  index: 0,
  generation: 0,
  playing: false,
  completed: false,
  inventory: null,
  conversion: null,
  controller: null,
  speechController: null,
  speechGeneration: 0,
  recorder: null,
  stream: null,
  recordTimer: null,
  mediaTimer: null,
  speechTimer: null,
  nextVideo: null,
  libraryPage: 1,
};
let toastTimer;
// In-memory timing only: no text, audio or source labels are retained here.
const quality = { schema_version: 1, runs: [] };
let qualityRun = null;
function closeStall() {
  if (qualityRun?._stallStart != null) {
    qualityRun.stall_ms += performance.now() - qualityRun._stallStart;
    qualityRun._stallStart = null;
  }
}
function finishQuality(outcome) {
  if (!qualityRun) return;
  closeStall();
  qualityRun.outcome = outcome;
  qualityRun.elapsed_ms = performance.now() - qualityRun._submit;
  for (const key of Object.keys(qualityRun)) if (key.startsWith('_')) delete qualityRun[key];
  qualityRun = null;
}
function beginQuality() {
  qualityRun = { outcome: 'loading', clip_count: 0, ended_clips: 0, started_playback: false,
    submit_to_loaded_ms: null, stall_count: 0, stall_ms: 0, media_errors: 0,
    transition_gaps_ms: [], dropped_video_frames: 0, _submit: performance.now() };
  quality.runs.push(qualityRun);
  if (quality.runs.length > 200) quality.runs.shift();
}
window.SignBridgeDiagnostics = {
  snapshot: () => JSON.parse(JSON.stringify(quality, (k, v) => k.startsWith('_') ? undefined : v)),
};
$("download-quality").addEventListener("click", () => {
  const blob = new Blob([JSON.stringify(window.SignBridgeDiagnostics.snapshot(), null, 2)], {type:'application/json'});
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob); link.download = 'signbridge-browser-quality.json'; link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
});
function toast(text) {
  $("toast").textContent = text;
  $("toast").hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => ($("toast").hidden = true), 6000);
}
async function api(url, options = {}) {
  let response;
  try {
    response = await fetch(url, options);
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new Error(
      "The local server is unavailable. Start SignBridge and try again.",
    );
  }
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error(
      "The server could not complete this request. Please try again.",
    );
  }
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Please check your input and try again.",
    );
  return data;
}
function setView(name) {
  ["workspace", "library", "about"].forEach(
    (view) => ($(view + "-view").hidden = view !== name),
  );
  document
    .querySelectorAll("[data-view]")
    .forEach((button) =>
      button.classList.toggle("active", button.dataset.view === name),
    );
  $("breadcrumb").textContent = {
    workspace: "Converter",
    library: "Sign library",
    about: "About the project",
  }[name];
  if (name !== "workspace") {
    const index = state.index;
    invalidate();
    if (state.queue.length) loadClip(index, false);
    pause();
    cancelSpeech();
  }
}
document
  .querySelectorAll("[data-view]")
  .forEach((button) =>
    button.addEventListener("click", () => setView(button.dataset.view)),
  );
$("library-link").addEventListener("click", () => setView("library"));
function inputTab(speech) {
  $("speech-panel").hidden = !speech;
  $("text-tab").classList.toggle("active", !speech);
  $("speech-tab").classList.toggle("active", speech);
  $("text-tab").setAttribute("aria-selected", String(!speech));
  $("speech-tab").setAttribute("aria-selected", String(speech));
  $("text-panel").setAttribute(
    "aria-labelledby",
    speech ? "speech-tab" : "text-tab",
  );
  if (!speech) cancelSpeech();
}
$("text-tab").addEventListener("click", () => inputTab(false));
$("speech-tab").addEventListener("click", () => inputTab(true));
[$("text-tab"), $("speech-tab")].forEach((tab, i) =>
  tab.addEventListener("keydown", (e) => {
    if (["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key)) {
      e.preventDefault();
      const next = e.key === "Home" ? 0 : e.key === "End" ? 1 : 1 - i;
      inputTab(next === 1);
      $(next ? "speech-tab" : "text-tab").focus();
    }
  }),
);
function wordCount() {
  const count = $("message").value.trim().split(/\s+/).filter(Boolean).length;
  $("word-count").textContent = `${count} word${count === 1 ? "" : "s"}`;
}
$("message").addEventListener("input", () => {
  if (
    state.speechController ||
    state.recorder?.state === "recording" ||
    $("record-button").disabled
  ) {
    cancelSpeech();
    toast("Speech input cancelled so your typed changes are kept.");
  }
  wordCount();
});
$("message").addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    e.preventDefault();
    convert();
  }
});
document.querySelectorAll("[data-example]").forEach((button) =>
  button.addEventListener("click", () => {
    inputTab(false);
    $("message").value = button.dataset.example;
    wordCount();
    $("message").focus();
  }),
);
function setPlayerState(text) {
  $("player-state").textContent = text;
}
function playerControls() {
  const hasQueue = state.queue.length > 0;
  ["play-button", "stop-button", "next-button"].forEach(
    (id) => ($(id).disabled = !hasQueue),
  );
  $("play-button").setAttribute(
    "aria-label",
    state.playing ? "Pause playback" : "Play sequence",
  );
  $("play-button")
    .querySelector("use")
    .setAttribute("href", state.playing ? "#i-pause" : "#i-play");
}
function pause() {
  closeStall();
  clearTimeout(state.mediaTimer);
  $("sign-video").pause();
  state.playing = false;
  playerControls();
  if (state.queue.length) setPlayerState("PAUSED");
}
function invalidate() {
  finishQuality('cancelled');
  clearTimeout(state.mediaTimer);
  if (state.nextVideo) {
    state.nextVideo.video.removeAttribute("src");
    state.nextVideo.video.load();
    state.nextVideo = null;
  }
  state.generation++;
  state.controller?.abort();
  state.controller = null;
  $("sign-video").pause();
  state.playing = false;
  playerControls();
  $("convert-button").disabled = false;
  $("convert-button").firstChild.textContent = "Convert to signs ";
}
function reset() {
  invalidate();
  state.queue = [];
  state.index = 0;
  state.conversion = null;
  state.completed = false;
  const video = $("sign-video");
  video.removeAttribute("src");
  video.load();
  video.hidden = true;
  $("empty-stage").hidden = false;
  $("video-caption").hidden = true;
  $("sequence-list").replaceChildren();
  const p = document.createElement("p");
  p.className = "sequence-placeholder";
  p.textContent =
    "Each sign becomes a step. Your sequence will be shown here after conversion.";
  $("sequence-list").append(p);
  $("sequence-count").textContent = "0 signs";
  $("sequence-metric").textContent = "PHRASE → WORD → LETTER";
  $("normalized").hidden = true;
  $("warnings").hidden = true;
  $("time-label").textContent = "No sequence yet";
  $("source-credit").textContent =
    "Sign videos retain their original source attribution.";
  setPlayerState("READY WHEN YOU ARE");
  playerControls();
  $("convert-button").disabled = false;
  $("convert-button").firstChild.textContent = "Convert to signs ";
}
$("clear-button").addEventListener("click", () => {
  cancelSpeech();
  reset();
  $("message").value = "";
  wordCount();
  $("message").focus();
});
$("preview-mode").addEventListener("change", () => {
  reset();
  updateCapabilities();
  toast(
    $("preview-mode").checked
      ? "Source preview enabled. Clips still require independent ISL review."
      : "Approved mode enabled. Only fully reviewed signs will play.",
  );
});
$("enable-preview").addEventListener("click", () => {
  $("preview-mode").checked = true;
  $("preview-mode").dispatchEvent(new Event("change"));
  $("message").focus();
});
function updateCapabilities() {
  if (!state.inventory) return;
  const letters = $("preview-mode").checked
    ? state.inventory.alphabet_previewable
    : state.inventory.alphabet_ready;
  $("alphabet-status").textContent =
    `${letters || 0}/26 letter assets available in this mode`;
  $("source-onboarding").hidden =
    !!state.inventory.ready ||
    !state.inventory.previewable ||
    $("preview-mode").checked;
}
$("fingerspell").addEventListener("change", reset);
$("sentence-mode").addEventListener("change", reset);
function warning(message) {
  const p = document.createElement("p");
  p.textContent = message;
  $("warnings").append(p);
  $("warnings").hidden = false;
}
function renderQueue() {
  $("sequence-list").replaceChildren();
  state.queue.forEach((item, index) => {
    if (index) {
      const arrow = document.createElement("span");
      arrow.className = "queue-arrow";
      arrow.textContent = "→";
      arrow.setAttribute("aria-hidden", "true");
      $("sequence-list").append(arrow);
    }
    const button = document.createElement("button");
    button.className = "queue-item" + (item.ready ? "" : " pending");
    button.setAttribute(
      "aria-label",
      `Sign ${index + 1}: ${item.text}${item.ready ? "" : ", source preview"}`,
    );
    const number = document.createElement("span");
    number.textContent = String(index + 1).padStart(2, "0");
    button.append(number, document.createTextNode(item.text));
    button.addEventListener("click", () => {
      invalidate();
      loadClip(index, false);
    });
    $("sequence-list").append(button);
  });
  $("sequence-count").textContent =
    `${state.queue.length} sign${state.queue.length === 1 ? "" : "s"}`;
}
async function convert() {
  const text = $("message").value.trim();
  if (!text) {
    toast("Please enter text to convert.");
    $("message").focus();
    return;
  }
  cancelSpeech();
  invalidate();
  const generation = state.generation;
  beginQuality();
  state.controller = new AbortController();
  $("convert-button").disabled = true;
  $("convert-button").firstChild.textContent = "Building sequence… ";
  try {
    const result = await api("/api/convert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        fingerspell: $("fingerspell").checked,
        preview: $("preview-mode").checked,
        mode: $("sentence-mode").checked ? 'reviewed_sentence' : 'dictionary',
      }),
      signal: state.controller.signal,
    });
    if (generation !== state.generation) return;
    state.queue = result.sequence;
    if (qualityRun) qualityRun.clip_count = result.sequence.length;
    state.conversion = result;
    state.index = 0;
    $("warnings").replaceChildren();
    $("warnings").hidden = true;
    if (result.preview && result.sequence.some((item) => !item.ready))
      warning("Source preview · these clips await independent ISL review.");
    result.warnings.forEach((w) => warning(w.message));
    $("normalized").hidden = false;
    $("normalized").textContent = `Normalized input: ${result.normalized}`;
    $("sequence-metric").textContent =
      `${result.matched_words}/${result.input_words} WORDS MATCHED · ${result.elapsed_ms} MS LOOKUP`;
    renderQueue();
    playerControls();
    if (state.queue.length) {
      loadClip(0, false);
    } else {
      finishQuality('unsupported');
      $("sign-video").removeAttribute("src");
      $("sign-video").load();
      $("sign-video").hidden = true;
      $("empty-stage").hidden = false;
      $("video-caption").hidden = true;
      const p = document.createElement("p");
      p.className = "sequence-placeholder";
      p.textContent =
        "No available signs matched. Check the library or enable source preview for pending clips.";
      $("sequence-list").append(p);
      $("time-label").textContent = "No available signs";
      setPlayerState("NO MATCHES");
    }
  } catch (error) {
    if (error.name !== "AbortError" && generation === state.generation) {
      finishQuality('conversion_error');
      toast(error.message);
      if (state.queue.length) loadClip(state.index, false);
    }
  } finally {
    if (generation === state.generation) {
      $("convert-button").disabled = false;
      $("convert-button").firstChild.textContent = "Convert to signs ";
    }
  }
}
$("convert-button").addEventListener("click", convert);
function loadClip(index, autoplay) {
  clearTimeout(state.mediaTimer);
  if (!state.queue.length) return;
  if (index >= state.queue.length) {
    finishQuality('completed');
    state.playing = false;
    state.completed = true;
    setPlayerState("SEQUENCE COMPLETE");
    $("time-label").textContent = "Sequence complete";
    playerControls();
    return;
  }
  state.index = index;
  state.playing = autoplay;
  state.completed = false;
  const item = state.queue[index],
    generation = state.generation;
  // A fresh element isolates late media events from a previous clip or conversion.
  const previous = $("sign-video");
  previous.pause();
  const video =
    state.nextVideo?.index === index
      ? state.nextVideo.video
      : document.createElement("video");
  state.nextVideo = null;
  video.id = "sign-video";
  video.playsInline = true;
  video.muted = true;
  video.preload = "auto";
  video.setAttribute("aria-label", `Sign: ${item.text}`);
  previous.replaceWith(video);
  if (!video.getAttribute("src")) video.src = item.url;
  video.playbackRate = Number($("playback-speed").value);
  $("empty-stage").hidden = true;
  $("video-caption").hidden = false;
  $("current-label").textContent =
    item.type === "alphabet"
      ? `${item.text.toUpperCase()} · spelling “${item.input}”`
      : item.text;
  $("current-counter").textContent =
    `Sign ${index + 1} of ${state.queue.length}`;
  $("time-label").textContent = `${index + 1} / ${state.queue.length} signs`;
  $("source-credit").replaceChildren(
    document.createTextNode(
      item.attribution || "Source attribution unavailable.",
    ),
  );
  if (/^https:\/\//.test(item.source_url)) {
    const link = document.createElement("a");
    link.href = item.source_url;
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent = " · View source ↗";
    $("source-credit").append(link);
  }
  document.querySelectorAll(".queue-item").forEach((button, i) => {
    button.classList.toggle("active", i === index);
    button.setAttribute("aria-current", String(i === index));
  });
  const active = () =>
    generation === state.generation && $("sign-video") === video;
  video.addEventListener('loadeddata', () => {
    if (active() && qualityRun && qualityRun.submit_to_loaded_ms == null)
      qualityRun.submit_to_loaded_ms = performance.now() - qualityRun._submit;
  });
  video.addEventListener("ended", () => {
    if (active() && qualityRun) {
      closeStall();
      qualityRun.ended_clips++;
      qualityRun._endedAt = performance.now();
      qualityRun.dropped_video_frames += video.getVideoPlaybackQuality?.().droppedVideoFrames || 0;
    }
    if (active() && state.playing) loadClip(index + 1, true);
  });
  function failedMedia() {
    if (!active()) return;
    if (qualityRun) qualityRun.media_errors++;
    closeStall();
    clearTimeout(state.mediaTimer);
    const continuePlayback = state.playing;
    warning(
      `Asset unavailable: ${item.text}.${continuePlayback ? " Skipping to the next sign." : " Use Next to skip this clip."}`,
    );
    state.playing = false;
    setPlayerState("MEDIA UNAVAILABLE");
    playerControls();
    if (continuePlayback) loadClip(index + 1, true);
  }
  video.addEventListener("error", () => {
    failedMedia();
  });
  video.addEventListener("waiting", () => {
    if (active() && state.playing) {
      if (qualityRun && qualityRun._stallStart == null) {
        qualityRun.stall_count++;
        qualityRun._stallStart = performance.now();
      }
      setPlayerState("BUFFERING");
      clearTimeout(state.mediaTimer);
      state.mediaTimer = setTimeout(failedMedia, 15000);
    }
  });
  video.addEventListener("playing", () => {
    if (active()) {
      closeStall();
      if (qualityRun?._endedAt != null) {
        qualityRun.transition_gaps_ms.push(performance.now() - qualityRun._endedAt);
        qualityRun._endedAt = null;
      }
      clearTimeout(state.mediaTimer);
      state.playing = true;
      setPlayerState(item.ready ? "PLAYING" : "PLAYING · SOURCE PREVIEW");
      playerControls();
    }
  });
  setPlayerState(item.ready ? "READY TO PLAY" : "SOURCE PREVIEW");
  playerControls();
  if (state.queue[index + 1]) {
    const next = document.createElement("video");
    next.preload = "auto";
    next.muted = true;
    next.src = state.queue[index + 1].url;
    state.nextVideo = { index: index + 1, video: next };
  }
  if (autoplay) startVideo(video, generation);
}
async function startVideo(
  video = $("sign-video"),
  generation = state.generation,
) {
  try {
    if (qualityRun) qualityRun.started_playback = true;
    state.playing = true;
    playerControls();
    clearTimeout(state.mediaTimer);
    state.mediaTimer = setTimeout(() => {
      if (generation === state.generation && $("sign-video") === video) {
        if (qualityRun) qualityRun.media_errors++;
        warning(
          `Playback timed out for ${state.queue[state.index].text}; skipping this sign.`,
        );
        loadClip(state.index + 1, true);
      }
    }, 15000);
    await video.play();
  } catch (error) {
    if (generation === state.generation && $("sign-video") === video) {
      clearTimeout(state.mediaTimer);
      if (video.error) {
        if (qualityRun) qualityRun.media_errors++;
        warning(
          `Asset unavailable: ${state.queue[state.index].text}. Skipping to the next sign.`,
        );
        loadClip(state.index + 1, true);
        return;
      }
      state.playing = false;
      playerControls();
      setPlayerState("PRESS PLAY TO CONTINUE");
      if (error.name !== "AbortError")
        toast(
          "Playback needs your attention. Press Play, or Next to skip an unavailable clip.",
        );
    }
  }
}
$("play-button").addEventListener("click", () => {
  if (state.playing) pause();
  else if (
    state.completed ||
    ($("sign-video").ended && state.index === state.queue.length - 1)
  ) {
    invalidate();
    loadClip(0, true);
  } else startVideo();
});
$("stop-button").addEventListener("click", () => {
  invalidate();
  loadClip(0, false);
  setPlayerState("STOPPED");
});
$("next-button").addEventListener("click", () => {
  const autoplay = state.playing;
  invalidate();
  loadClip(state.index + 1, autoplay);
});
$("playback-speed").addEventListener(
  "change",
  () => ($("sign-video").playbackRate = Number($("playback-speed").value)),
);
function renderLibrary() {
  const search = $("library-search").value.trim().toLowerCase();
  const kind = $("library-type").value,
    category = $("library-category").value;
  const entries = state.inventory.entries
    .filter(
      (e) =>
        (e.text + " " + e.meaning + " " + (e.aliases || []).join(" "))
          .toLowerCase()
          .includes(search) &&
        (kind === "all" || e.type === kind) &&
        (category === "all" || e.category === category),
    )
    .sort(
      (a, b) =>
        Number(a.type === "alphabet") - Number(b.type === "alphabet") ||
        a.text.localeCompare(b.text),
    );
  const pageSize = 24,
    pages = Math.max(1, Math.ceil(entries.length / pageSize));
  state.libraryPage = Math.min(state.libraryPage, pages);
  const start = (state.libraryPage - 1) * pageSize;
  const visible = entries.slice(start, start + pageSize);
  $("library-grid").replaceChildren();
  $("library-summary").textContent =
    `${entries.length} ${entries.length === 1 ? "entry" : "entries"} · ${state.inventory.ready} approved for playback`;
  $("library-pagination").hidden = entries.length <= pageSize;
  $("library-page").textContent =
    `Page ${state.libraryPage} of ${pages} · ${entries.length ? start + 1 : 0}–${Math.min(start + pageSize, entries.length)} of ${entries.length}`;
  $("library-previous").disabled = state.libraryPage === 1;
  $("library-next").disabled = state.libraryPage === pages;
  for (const entry of visible) {
    const card = document.createElement("article");
    card.className = "card library-item";
    const status = document.createElement("span");
    status.className = "library-status";
    status.textContent = entry.ready
      ? "Approved"
      : entry.previewable
        ? "Source clip · ISL review pending"
        : "Media not available";
    const title = document.createElement("h2");
    title.textContent = entry.text;
    const description = document.createElement("p");
    description.textContent = entry.meaning || "Meaning awaiting review.";
    const button = document.createElement("button");
    button.textContent = entry.ready
      ? "Use this sign ↗"
      : "Preview this source clip ↗";
    button.disabled = !entry.previewable;
    button.addEventListener("click", () => {
      $("message").value = entry.text;
      $("preview-mode").checked = !entry.ready;
      wordCount();
      setView("workspace");
      inputTab(false);
      $("sentence-mode").checked = false;
      updateCapabilities();
      if (entry.type === "alphabet") {
        reset();
        state.queue = [
          { ...entry, input: entry.text, url: `/api/media/${entry.id}` },
        ];
        $("warnings").replaceChildren();
        if (!entry.ready)
          warning(
            "Source preview · this letter awaits independent ISL review.",
          );
        renderQueue();
        loadClip(0, false);
      } else convert();
    });
    const categoryLabel = document.createElement("span");
    categoryLabel.className = "library-category-label";
    categoryLabel.textContent =
      entry.category ||
      (entry.type === "alphabet" ? "Alphabet" : "Everyday signs");
    card.append(status, title, categoryLabel, description, button);
    if (/^https:\/\//.test(entry.source_url)) {
      const source = document.createElement("a");
      source.href = entry.source_url;
      source.target = "_blank";
      source.rel = "noopener";
      source.textContent = "View original source ↗";
      card.append(source);
    }
    $("library-grid").append(card);
  }
  if (!entries.length) {
    const p = document.createElement("p");
    p.className = "card library-empty";
    p.textContent = search
      ? "No signs match your search."
      : "The sign collection is being prepared. Add reviewed media using the asset tools in the README.";
    $("library-grid").append(p);
  }
}
function resetLibraryPage() {
  state.libraryPage = 1;
  renderLibrary();
}
$("library-search").addEventListener("input", resetLibraryPage);
$("library-type").addEventListener("change", resetLibraryPage);
$("library-category").addEventListener("change", resetLibraryPage);
$("library-previous").addEventListener("click", () => {
  state.libraryPage--;
  renderLibrary();
});
$("library-next").addEventListener("click", () => {
  state.libraryPage++;
  renderLibrary();
});
async function loadInventory() {
  try {
    state.inventory = await api("/api/dictionary");
    const categories = [
      ...new Set(
        state.inventory.entries.map((e) => e.category).filter(Boolean),
      ),
    ].sort();
    $("library-category").replaceChildren();
    for (const value of ["all", ...categories]) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value === "all" ? "All categories" : value;
      $("library-category").append(option);
    }
    const words = state.inventory.entries.filter(
      (e) => e.type === "word",
    ).length;
    const phrases = state.inventory.entries.filter(
      (e) => e.type === "phrase",
    ).length;
    const letters = state.inventory.entries.filter(
      (e) => e.type === "alphabet",
    ).length;
    $("library-coverage").textContent =
      `${words} words · ${phrases} phrases · ${letters} letters`;
    $("nav-count").textContent = state.inventory.total;
    $("review-summary").textContent =
      `${state.inventory.ready} approved signs · ${state.inventory.previewable - state.inventory.ready} source clips awaiting review`;
    renderLibrary();
    updateCapabilities();
  } catch (error) {
    $("review-summary").textContent =
      "Library unavailable. Check the local server.";
    toast(error.message);
  }
}
function stopTracks() {
  state.stream?.getTracks().forEach((track) => track.stop());
  state.stream = null;
  clearInterval(state.recordTimer);
}
function resetRecordingUI() {
  $("record-button").classList.remove("recording");
  $("record-button").setAttribute("aria-label", "Start recording");
  $("record-heading").textContent = "Start with your voice";
  $("record-hint").textContent = "Record up to 60 seconds in English.";
}
function cancelSpeech() {
  clearTimeout(state.speechTimer);
  $("cancel-speech").hidden = true;
  state.speechGeneration++;
  state.speechController?.abort();
  state.speechController = null;
  if (state.recorder && state.recorder.state !== "inactive")
    state.recorder.stop();
  stopTracks();
  resetRecordingUI();
  $("record-button").disabled = false;
  $("upload-button").disabled = false;
}
$("cancel-speech").addEventListener("click", () => {
  cancelSpeech();
  toast("Transcription cancelled. Your message is unchanged.");
});
async function transcribe(file, generation) {
  if (generation !== state.speechGeneration) return;
  $("record-heading").textContent = "Turning speech into text…";
  $("record-hint").textContent =
    "First use may take longer while the model downloads.";
  $("record-button").disabled = true;
  $("upload-button").disabled = true;
  $("cancel-speech").hidden = false;
  state.speechController = new AbortController();
  state.speechTimer = setTimeout(() => {
    if (generation === state.speechGeneration) {
      cancelSpeech();
      toast(
        "Transcription took too long. The first model download may still be running; retry shortly or type your message.",
      );
    }
  }, 180000);
  try {
    const data = new FormData();
    data.append("audio", file, file.name || "recording.webm");
    const result = await api("/api/transcribe", {
      method: "POST",
      body: data,
      signal: state.speechController.signal,
    });
    if (generation !== state.speechGeneration) return;
    $("message").value = result.text;
    wordCount();
    $("message").focus();
    $("record-heading").textContent = "Your transcript is ready";
    $("record-hint").textContent =
      "Review the text below, then select Convert to signs.";
    toast("Transcript ready. Edit it before converting to signs.");
  } catch (error) {
    if (generation === state.speechGeneration && error.name !== "AbortError") {
      resetRecordingUI();
      toast(error.message);
    }
  } finally {
    if (generation === state.speechGeneration) {
      clearTimeout(state.speechTimer);
      $("cancel-speech").hidden = true;
      $("record-button").disabled = false;
      $("upload-button").disabled = false;
    }
  }
}
$("record-button").addEventListener("click", async () => {
  if (state.recorder?.state === "recording") {
    state.recorder.stop();
    stopTracks();
    return;
  }
  cancelSpeech();
  pause();
  const generation = state.speechGeneration;
  $("record-button").disabled = true;
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    toast(
      "Microphone recording is unavailable in this browser. Upload an audio file instead.",
    );
    $("record-button").disabled = false;
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    if (generation !== state.speechGeneration) {
      stream.getTracks().forEach((t) => t.stop());
      return;
    }
    state.stream = stream;
    const mime = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/mp4",
      "audio/ogg;codecs=opus",
    ].find((m) => MediaRecorder.isTypeSupported(m));
    const recorder = new MediaRecorder(
      stream,
      mime ? { mimeType: mime } : undefined,
    );
    state.recorder = recorder;
    const chunks = [];
    recorder.addEventListener("dataavailable", (e) => {
      if (e.data.size) chunks.push(e.data);
    });
    recorder.addEventListener("stop", () => {
      if (generation !== state.speechGeneration) return;
      stopTracks();
      $("record-button").classList.remove("recording");
      const blob = new Blob(chunks, { type: recorder.mimeType });
      const ext = recorder.mimeType.includes("mp4")
        ? "m4a"
        : recorder.mimeType.includes("ogg")
          ? "ogg"
          : "webm";
      transcribe(
        new File([blob], `recording.${ext}`, { type: recorder.mimeType }),
        generation,
      );
    });
    recorder.addEventListener("error", () => {
      if (generation === state.speechGeneration) {
        cancelSpeech();
        toast("Recording failed. Please try again or upload audio.");
      }
    });
    recorder.start();
    $("record-button").disabled = false;
    $("record-button").classList.add("recording");
    $("record-button").setAttribute("aria-label", "Stop recording");
    $("record-heading").textContent = "Listening. Take your time.";
    const started = Date.now();
    state.recordTimer = setInterval(() => {
      const seconds = Math.floor((Date.now() - started) / 1000);
      $("record-hint").textContent =
        `${seconds}s / 60s · Tap the microphone to finish`;
      if (seconds >= 59 && recorder.state === "recording") {
        recorder.stop();
        stopTracks();
      }
    }, 250);
  } catch (error) {
    if (generation !== state.speechGeneration) return;
    stopTracks();
    resetRecordingUI();
    $("record-button").disabled = false;
    toast(
      error.name === "NotAllowedError"
        ? "Microphone permission was declined. You can upload audio or type your message."
        : "No microphone is available. Upload audio or type your message.",
    );
  }
});
$("upload-button").addEventListener("click", () => $("audio-file").click());
$("audio-file").addEventListener("change", () => {
  const file = $("audio-file").files[0];
  if (!file) return;
  cancelSpeech();
  pause();
  if (file.size > 20 * 1024 * 1024) toast("Choose audio smaller than 20 MB.");
  else transcribe(file, state.speechGeneration);
  $("audio-file").value = "";
});
window.addEventListener("beforeunload", () => {
  cancelSpeech();
  invalidate();
});
loadInventory();
wordCount();
