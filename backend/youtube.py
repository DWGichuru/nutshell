import subprocess
from pathlib import Path
from typing import Any

import yt_dlp


class YouTubeError(Exception):
    """Raised when yt-dlp or ffmpeg can't fetch, download, or convert a video."""


PLAYLIST_ERROR_MESSAGE = "This looks like a playlist. Paste a link to a single video instead."


def fetch_metadata(url: str) -> dict[str, Any]:
    ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        raise YouTubeError(str(exc)) from exc

    if info.get("_type") == "playlist":
        raise YouTubeError(PLAYLIST_ERROR_MESSAGE)
    return info


def download_audio(url: str, dest_dir: Path) -> Path:
    # A bare playlist URL isn't rejected here: yt-dlp would already have started
    # downloading its first entry by the time `_type` is known, so callers must
    # reject playlists via fetch_metadata() first (every route does).
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio/best",
        "outtmpl": str(dest_dir / "audio.%(ext)s"),
        "noplaylist": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return Path(ydl.prepare_filename(info))
    except yt_dlp.utils.DownloadError as exc:
        raise YouTubeError(str(exc)) from exc


def trim_audio(src_path: Path, start_seconds: float, end_seconds: float) -> Path:
    dest_path = src_path.with_name(f"{src_path.stem}.trimmed{src_path.suffix}")
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(src_path),
                "-ss",
                str(start_seconds),
                "-to",
                str(end_seconds),
                str(dest_path),
            ],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode(errors="ignore") if exc.stderr else ""
        raise YouTubeError(f"ffmpeg trim failed: {stderr}") from exc

    dest_path.replace(src_path)
    return src_path


def convert_to_mp3(src_path: Path) -> Path:
    if src_path.suffix == ".mp3":
        return src_path

    dest_path = src_path.with_suffix(".mp3")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(src_path), str(dest_path)],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode(errors="ignore") if exc.stderr else ""
        raise YouTubeError(f"ffmpeg conversion failed: {stderr}") from exc

    src_path.unlink()
    return dest_path
