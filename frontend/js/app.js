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

const STATUS_POLL_INTERVAL_MS = 2000;
const SKIP_SECONDS = 5;

let wavesurfer = null;
let activeRegion = null;

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
  } catch (err) {
    setTrimError(err.message);
    trimStatusEl.textContent = "";
  } finally {
    trimButton.disabled = false;
  }
}

downloadButton.addEventListener("click", startDownload);
previewButton.addEventListener("click", previewSelection);
trimButton.addEventListener("click", trimSelection);
playPauseButton.addEventListener("click", togglePlayPause);
skipBackButton.addEventListener("click", skipBack);
skipForwardButton.addEventListener("click", skipForward);
