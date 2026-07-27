const urlInput = document.getElementById("video-url");
const downloadButton = document.getElementById("download-button");
const statusEl = document.getElementById("download-status");
const errorEl = document.getElementById("download-error");
const trimSection = document.getElementById("trim-section");
const trimStartLabel = document.getElementById("trim-start");
const trimEndLabel = document.getElementById("trim-end");
const previewButton = document.getElementById("preview-button");
const trimButton = document.getElementById("trim-button");
const trimStatusEl = document.getElementById("trim-status");
const trimErrorEl = document.getElementById("trim-error");
const playPauseButton = document.getElementById("play-pause-button");
const skipBackButton = document.getElementById("skip-back-button");
const skipForwardButton = document.getElementById("skip-forward-button");
const transcribeSection = document.getElementById("transcribe-section");
const transcribeButton = document.getElementById("transcribe-button");
const transcribeStatusEl = document.getElementById("transcribe-status");
const transcribeErrorEl = document.getElementById("transcribe-error");
const transcriptDisplayEl = document.getElementById("transcript-display");
const summarizeSection = document.getElementById("summarize-section");
const summarizeButton = document.getElementById("summarize-button");
const summarizeStatusEl = document.getElementById("summarize-status");
const summarizeErrorEl = document.getElementById("summarize-error");
const summaryDisplayEl = document.getElementById("summary-display");

const navNewSummaryButton = document.getElementById("nav-new-summary");
const navLibraryButton = document.getElementById("nav-library");
const newSummaryView = document.getElementById("new-summary-view");
const libraryView = document.getElementById("library-view");
const librarySearchInput = document.getElementById("library-search");
const libraryDateFromInput = document.getElementById("library-date-from");
const libraryDateToInput = document.getElementById("library-date-to");
const libraryFilterButton = document.getElementById("library-filter-button");
const libraryErrorEl = document.getElementById("library-error");
const libraryResultsEl = document.getElementById("library-results");
const libraryDetailSection = document.getElementById("library-detail-section");
const libraryDetailTitleEl = document.getElementById("library-detail-title");
const libraryDetailMetaEl = document.getElementById("library-detail-meta");
const libraryTranscriptDisplayEl = document.getElementById("library-transcript-display");
const librarySummariesEl = document.getElementById("library-summaries");
const librarySummarizeButton = document.getElementById("library-summarize-button");
const librarySummarizeStatusEl = document.getElementById("library-summarize-status");
const librarySummarizeErrorEl = document.getElementById("library-summarize-error");

const STATUS_POLL_INTERVAL_MS = 2000;
const SKIP_SECONDS = 5;
const ACTIVE_NAV_CLASSES = ["bg-terracotta", "text-cream", "hover:bg-terracotta-dark"];
const INACTIVE_NAV_CLASSES = ["bg-ivory", "text-espresso", "hover:bg-warm-gray/30"];

let wavesurfer = null;
let activeRegion = null;
let currentLibraryVideoId = null;

function formatTime(seconds) {
  const total = Math.max(0, Math.round(seconds));
  const minutes = Math.floor(total / 60);
  const secs = total % 60;
  return `${minutes}:${String(secs).padStart(2, "0")}`;
}

function updateTrimLabels(region) {
  trimStartLabel.textContent = formatTime(region.start);
  trimEndLabel.textContent = formatTime(region.end);
}

function setStatus(message) {
  statusEl.textContent = message;
}

function setError(message) {
  if (message) {
    errorEl.textContent = message;
    errorEl.classList.remove("hidden");
  } else {
    errorEl.classList.add("hidden");
    errorEl.textContent = "";
  }
}

async function pollDownloadStatus(videoId) {
  const response = await fetch(`/api/videos/${videoId}/status`);
  if (!response.ok) {
    throw new Error("Unable to check download status.");
  }
  const body = await response.json();

  if (body.status === "done") {
    setStatus("Download complete.");
    onVideoReady(videoId);
    return;
  }
  if (body.status === "error") {
    setError(body.error || "Download failed.");
    setStatus("");
    downloadButton.disabled = false;
    return;
  }

  setStatus(`Status: ${body.status}...`);
  setTimeout(() => pollDownloadStatus(videoId), STATUS_POLL_INTERVAL_MS);
}

function onVideoReady(videoId) {
  trimSection.classList.remove("hidden");
  trimSection.dataset.videoId = videoId;
  renderWaveform(videoId);
}

function renderWaveform(videoId) {
  if (wavesurfer) {
    wavesurfer.destroy();
  }

  const regions = WaveSurfer.Regions.create();

  wavesurfer = WaveSurfer.create({
    container: "#waveform",
    waveColor: "#8A7A6A",
    progressColor: "#C96F45",
    cursorColor: "#3A2A1E",
    height: 96,
    url: `/api/videos/${videoId}/audio?t=${Date.now()}`,
    plugins: [regions],
  });

  wavesurfer.on("decode", (duration) => {
    activeRegion = regions.addRegion({
      start: 0,
      end: duration,
      color: "rgba(201, 111, 69, 0.2)",
      drag: true,
      resize: true,
    });
    updateTrimLabels(activeRegion);
  });

  regions.on("region-updated", (region) => {
    activeRegion = region;
    updateTrimLabels(region);
  });

  wavesurfer.on("play", () => setPlayPauseLabel(true));
  wavesurfer.on("pause", () => setPlayPauseLabel(false));
  wavesurfer.on("finish", () => setPlayPauseLabel(false));
  setPlayPauseLabel(false);
}

function setPlayPauseLabel(isPlaying) {
  playPauseButton.textContent = isPlaying ? "Pause" : "Play";
  playPauseButton.setAttribute("aria-label", isPlaying ? "Pause" : "Play");
}

function togglePlayPause() {
  if (!wavesurfer) return;
  wavesurfer.playPause();
}

function skipBack() {
  if (!wavesurfer) return;
  wavesurfer.skip(-SKIP_SECONDS);
}

function skipForward() {
  if (!wavesurfer) return;
  wavesurfer.skip(SKIP_SECONDS);
}

async function startDownload() {
  const url = urlInput.value.trim();
  if (!url) {
    setError("Enter a YouTube URL first.");
    return;
  }

  setError(null);
  downloadButton.disabled = true;
  setStatus("Starting download...");

  try {
    const response = await fetch("/api/videos/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || "Download request failed.");
    }

    const body = await response.json();
    pollDownloadStatus(body.video_id);
  } catch (err) {
    setError(err.message);
    setStatus("");
    downloadButton.disabled = false;
  }
}

function previewSelection() {
  if (!wavesurfer || !activeRegion) return;
  wavesurfer.play(activeRegion.start, activeRegion.end);
}

function setTrimError(message) {
  if (message) {
    trimErrorEl.textContent = message;
    trimErrorEl.classList.remove("hidden");
  } else {
    trimErrorEl.classList.add("hidden");
    trimErrorEl.textContent = "";
  }
}

async function trimSelection() {
  if (!activeRegion) return;
  const videoId = trimSection.dataset.videoId;

  setTrimError(null);
  trimButton.disabled = true;
  trimStatusEl.textContent = "Trimming...";

  try {
    const response = await fetch(`/api/videos/${videoId}/trim`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        start_seconds: activeRegion.start,
        end_seconds: activeRegion.end,
      }),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || "Trim request failed.");
    }

    trimStatusEl.textContent = "Trim complete.";
    renderWaveform(videoId);
    transcribeSection.classList.remove("hidden");
    transcribeSection.dataset.videoId = videoId;
  } catch (err) {
    setTrimError(err.message);
    trimStatusEl.textContent = "";
  } finally {
    trimButton.disabled = false;
  }
}

function setTranscribeError(message) {
  if (message) {
    transcribeErrorEl.textContent = message;
    transcribeErrorEl.classList.remove("hidden");
  } else {
    transcribeErrorEl.classList.add("hidden");
    transcribeErrorEl.textContent = "";
  }
}

async function pollTranscriptionStatus(videoId) {
  const response = await fetch(`/api/videos/${videoId}/transcription/status`);
  if (!response.ok) {
    throw new Error("Unable to check transcription status.");
  }
  const body = await response.json();

  if (body.status === "done") {
    transcribeStatusEl.textContent = "Transcription complete.";
    showTranscript(videoId);
    transcribeButton.disabled = false;
    return;
  }
  if (body.status === "error") {
    setTranscribeError(body.error || "Transcription failed.");
    transcribeStatusEl.textContent = "";
    transcribeButton.disabled = false;
    return;
  }

  transcribeStatusEl.textContent = `Status: ${body.status}...`;
  setTimeout(() => pollTranscriptionStatus(videoId), STATUS_POLL_INTERVAL_MS);
}

async function showTranscript(videoId) {
  const response = await fetch(`/api/videos/${videoId}/transcript`);
  if (!response.ok) {
    setTranscribeError("Unable to load transcript.");
    return;
  }
  const body = await response.json();
  transcriptDisplayEl.textContent = body.text;
  transcriptDisplayEl.classList.remove("hidden");

  summarizeSection.classList.remove("hidden");
  summarizeSection.dataset.videoId = videoId;
}

function setSummarizeError(message) {
  if (message) {
    summarizeErrorEl.textContent = message;
    summarizeErrorEl.classList.remove("hidden");
  } else {
    summarizeErrorEl.classList.add("hidden");
    summarizeErrorEl.textContent = "";
  }
}

async function pollSummarizationStatus(videoId) {
  const response = await fetch(`/api/videos/${videoId}/summarization/status`);
  if (!response.ok) {
    throw new Error("Unable to check summarization status.");
  }
  const body = await response.json();

  if (body.status === "done") {
    summarizeStatusEl.textContent = "Summary complete.";
    showLatestSummary(videoId);
    summarizeButton.disabled = false;
    return;
  }
  if (body.status === "error") {
    setSummarizeError(body.error || "Summarization failed.");
    summarizeStatusEl.textContent = "";
    summarizeButton.disabled = false;
    return;
  }

  summarizeStatusEl.textContent = `Status: ${body.status}...`;
  setTimeout(() => pollSummarizationStatus(videoId), STATUS_POLL_INTERVAL_MS);
}

async function showLatestSummary(videoId) {
  const response = await fetch(`/api/videos/${videoId}/summaries`);
  if (!response.ok) {
    setSummarizeError("Unable to load summary.");
    return;
  }
  const body = await response.json();
  const latest = body.summaries[0];
  if (!latest) return;
  summaryDisplayEl.textContent = latest.content;
  summaryDisplayEl.classList.remove("hidden");
}

async function startSummarization() {
  const videoId = summarizeSection.dataset.videoId;
  const format = document.querySelector('input[name="summary-format"]:checked').value;
  const provider = document.querySelector('input[name="summary-provider"]:checked').value;

  setSummarizeError(null);
  summarizeButton.disabled = true;
  summarizeStatusEl.textContent = "Starting summarization...";
  summaryDisplayEl.classList.add("hidden");

  try {
    const response = await fetch(`/api/videos/${videoId}/summarize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ format, provider }),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || "Summarization request failed.");
    }

    pollSummarizationStatus(videoId);
  } catch (err) {
    setSummarizeError(err.message);
    summarizeStatusEl.textContent = "";
    summarizeButton.disabled = false;
  }
}

async function startTranscription() {
  const videoId = transcribeSection.dataset.videoId;
  const method = document.querySelector('input[name="transcription-method"]:checked').value;

  setTranscribeError(null);
  transcribeButton.disabled = true;
  transcribeStatusEl.textContent = "Starting transcription...";
  transcriptDisplayEl.classList.add("hidden");

  try {
    const response = await fetch(`/api/videos/${videoId}/transcribe`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ method }),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || "Transcription request failed.");
    }

    pollTranscriptionStatus(videoId);
  } catch (err) {
    setTranscribeError(err.message);
    transcribeStatusEl.textContent = "";
    transcribeButton.disabled = false;
  }
}

function formatDate(isoString) {
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return isoString;
  return date.toLocaleDateString();
}

function showNewSummaryView() {
  newSummaryView.classList.remove("hidden");
  libraryView.classList.add("hidden");
  navNewSummaryButton.classList.add(...ACTIVE_NAV_CLASSES);
  navNewSummaryButton.classList.remove(...INACTIVE_NAV_CLASSES);
  navLibraryButton.classList.add(...INACTIVE_NAV_CLASSES);
  navLibraryButton.classList.remove(...ACTIVE_NAV_CLASSES);
}

function showLibraryView() {
  libraryView.classList.remove("hidden");
  newSummaryView.classList.add("hidden");
  navLibraryButton.classList.add(...ACTIVE_NAV_CLASSES);
  navLibraryButton.classList.remove(...INACTIVE_NAV_CLASSES);
  navNewSummaryButton.classList.add(...INACTIVE_NAV_CLASSES);
  navNewSummaryButton.classList.remove(...ACTIVE_NAV_CLASSES);
  fetchVideos();
}

function setLibraryError(message) {
  if (message) {
    libraryErrorEl.textContent = message;
    libraryErrorEl.classList.remove("hidden");
  } else {
    libraryErrorEl.classList.add("hidden");
    libraryErrorEl.textContent = "";
  }
}

async function fetchVideos() {
  setLibraryError(null);
  const params = new URLSearchParams();
  const search = librarySearchInput.value.trim();
  const dateFrom = libraryDateFromInput.value;
  const dateTo = libraryDateToInput.value;
  if (search) params.set("search", search);
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);

  try {
    const response = await fetch(`/api/videos?${params.toString()}`);
    if (!response.ok) {
      throw new Error("Unable to load videos.");
    }
    const body = await response.json();
    renderLibraryResults(body.videos);
  } catch (err) {
    setLibraryError(err.message);
  }
}

function renderLibraryResults(videos) {
  libraryResultsEl.innerHTML = "";

  if (videos.length === 0) {
    const empty = document.createElement("li");
    empty.className = "py-3 text-sm text-warm-gray";
    empty.textContent = "No videos found.";
    libraryResultsEl.appendChild(empty);
    return;
  }

  for (const video of videos) {
    const item = document.createElement("li");
    item.className = "py-3";

    const button = document.createElement("button");
    button.className = "w-full text-left hover:text-terracotta";
    button.innerHTML = `
      <span class="font-medium">${video.title}</span>
      <span class="block text-sm text-warm-gray">${video.channel} - ${formatDate(video.date_added)}</span>
    `;
    button.addEventListener("click", () => selectLibraryVideo(video.video_id));

    item.appendChild(button);
    libraryResultsEl.appendChild(item);
  }
}

async function selectLibraryVideo(videoId) {
  setLibraryError(null);
  currentLibraryVideoId = videoId;

  try {
    const metaResponse = await fetch(`/api/videos/${videoId}`);
    if (videoId !== currentLibraryVideoId) return;
    if (!metaResponse.ok) {
      throw new Error("Unable to load video.");
    }
    const meta = await metaResponse.json();
    if (videoId !== currentLibraryVideoId) return;

    libraryDetailSection.classList.remove("hidden");
    libraryDetailSection.dataset.videoId = videoId;
    libraryDetailTitleEl.textContent = meta.title;
    libraryDetailMetaEl.textContent = `${meta.channel} - ${formatDate(meta.date_added)}`;

    const transcriptResponse = await fetch(`/api/videos/${videoId}/transcript`);
    if (videoId !== currentLibraryVideoId) return;
    if (transcriptResponse.ok) {
      const transcript = await transcriptResponse.json();
      if (videoId !== currentLibraryVideoId) return;
      libraryTranscriptDisplayEl.textContent = transcript.text;
    } else {
      libraryTranscriptDisplayEl.textContent = "No transcript yet for this video.";
    }

    await showLibrarySummaries(videoId);
  } catch (err) {
    if (videoId === currentLibraryVideoId) setLibraryError(err.message);
  }
}

async function showLibrarySummaries(videoId) {
  const response = await fetch(`/api/videos/${videoId}/summaries`);
  if (videoId !== currentLibraryVideoId) return;
  librarySummariesEl.innerHTML = "";
  if (!response.ok) return;

  const body = await response.json();
  if (videoId !== currentLibraryVideoId) return;
  if (body.summaries.length === 0) {
    const empty = document.createElement("p");
    empty.className = "text-sm text-warm-gray";
    empty.textContent = "No summaries yet.";
    librarySummariesEl.appendChild(empty);
    return;
  }

  for (const summary of body.summaries) {
    const wrapper = document.createElement("div");
    wrapper.className = "rounded bg-cream p-4 dark:bg-espresso/40";
    const heading = document.createElement("p");
    heading.className = "mb-2 text-sm font-medium text-terracotta";
    heading.textContent = `${summary.format} - ${summary.created_at}`;
    const content = document.createElement("pre");
    content.className = "whitespace-pre-wrap text-sm";
    content.textContent = summary.content;
    wrapper.appendChild(heading);
    wrapper.appendChild(content);
    librarySummariesEl.appendChild(wrapper);
  }
}

function setLibrarySummarizeError(message) {
  if (message) {
    librarySummarizeErrorEl.textContent = message;
    librarySummarizeErrorEl.classList.remove("hidden");
  } else {
    librarySummarizeErrorEl.classList.add("hidden");
    librarySummarizeErrorEl.textContent = "";
  }
}

async function pollLibrarySummarizationStatus(videoId) {
  const response = await fetch(`/api/videos/${videoId}/summarization/status`);
  if (videoId !== currentLibraryVideoId) return;
  if (!response.ok) {
    throw new Error("Unable to check summarization status.");
  }
  const body = await response.json();
  if (videoId !== currentLibraryVideoId) return;

  if (body.status === "done") {
    librarySummarizeStatusEl.textContent = "Summary complete.";
    await showLibrarySummaries(videoId);
    librarySummarizeButton.disabled = false;
    return;
  }
  if (body.status === "error") {
    setLibrarySummarizeError(body.error || "Summarization failed.");
    librarySummarizeStatusEl.textContent = "";
    librarySummarizeButton.disabled = false;
    return;
  }

  librarySummarizeStatusEl.textContent = `Status: ${body.status}...`;
  setTimeout(() => pollLibrarySummarizationStatus(videoId), STATUS_POLL_INTERVAL_MS);
}

async function startLibrarySummarization() {
  const videoId = libraryDetailSection.dataset.videoId;
  const format = document.querySelector('input[name="library-summary-format"]:checked').value;
  const provider = document.querySelector('input[name="library-summary-provider"]:checked').value;

  setLibrarySummarizeError(null);
  librarySummarizeButton.disabled = true;
  librarySummarizeStatusEl.textContent = "Starting summarization...";

  try {
    const response = await fetch(`/api/videos/${videoId}/summarize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ format, provider }),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || "Summarization request failed.");
    }

    pollLibrarySummarizationStatus(videoId);
  } catch (err) {
    setLibrarySummarizeError(err.message);
    librarySummarizeStatusEl.textContent = "";
    librarySummarizeButton.disabled = false;
  }
}

navNewSummaryButton.addEventListener("click", showNewSummaryView);
navLibraryButton.addEventListener("click", showLibraryView);
libraryFilterButton.addEventListener("click", fetchVideos);
librarySummarizeButton.addEventListener("click", startLibrarySummarization);
for (const input of [librarySearchInput, libraryDateFromInput, libraryDateToInput]) {
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") fetchVideos();
  });
}

downloadButton.addEventListener("click", startDownload);
previewButton.addEventListener("click", previewSelection);
trimButton.addEventListener("click", trimSelection);
playPauseButton.addEventListener("click", togglePlayPause);
skipBackButton.addEventListener("click", skipBack);
skipForwardButton.addEventListener("click", skipForward);
transcribeButton.addEventListener("click", startTranscription);
summarizeButton.addEventListener("click", startSummarization);
