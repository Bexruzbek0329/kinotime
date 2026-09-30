"""Video downloader service supporting yt-dlp and direct HTTP streams."""
import asyncio
import os
import tempfile
import uuid
import shutil
from typing import Optional
import httpx
import structlog

log = structlog.get_logger()

# Telegram Bot API standard upload limit is 50 MB
MAX_FILE_SIZE = 50 * 1024 * 1024


def _download_with_ytdlp(url: str, dest_dir: str) -> Optional[dict]:
    """Download video using yt-dlp in a sync worker thread."""
    try:
        import yt_dlp

        out_template = os.path.join(dest_dir, f"{uuid.uuid4().hex}_%(id)s.%(ext)s")

        has_ffmpeg = shutil.which("ffmpeg") is not None
        if has_ffmpeg:
            format_str = (
                "best[filesize<48M]/"
                "best[filesize_approx<48M]/"
                "bestvideo[filesize<40M]+bestaudio[filesize<8M]/"
                "bestvideo[filesize_approx<40M]+bestaudio[filesize_approx<8M]/"
                "best[ext=mp4][height<=720]/"
                "best[ext=mp4][height<=480]/"
                "best[height<=480]/"
                "best[ext=mp4][height<=360]/"
                "worst[ext=mp4]/"
                "worst/"
                "best"
            )
        else:
            format_str = (
                "best[filesize<48M]/"
                "best[filesize_approx<48M]/"
                "best[ext=mp4][height<=720]/"
                "best[ext=mp4][height<=480]/"
                "best[height<=480]/"
                "best[ext=mp4][height<=360]/"
                "worst[ext=mp4]/"
                "worst/"
                "best"
            )

        ydl_opts = {
            "format": format_str,
            "outtmpl": out_template,
            "max_filesize": MAX_FILE_SIZE,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "extract_flat": False,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-us,en;q=0.5",
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return None

            filename = ydl.prepare_filename(info)
            if not os.path.exists(filename):
                base = os.path.splitext(filename)[0]
                for ext in (".mp4", ".mkv", ".webm", ".mov"):
                    if os.path.exists(base + ext):
                        filename = base + ext
                        break

            if not os.path.exists(filename):
                return None

            size = os.path.getsize(filename)
            if size > MAX_FILE_SIZE:
                try:
                    os.remove(filename)
                except Exception:
                    pass
                return {"error": "size_limit", "size": size}

            return {
                "file_path": filename,
                "title": info.get("title", "Video"),
                "duration": int(info.get("duration") or 0),
                "width": info.get("width"),
                "height": info.get("height"),
                "size_mb": round(size / 1024 / 1024, 2),
            }
    except Exception as e:
        err_str = str(e)
        if "larger than max-filesize" in err_str or "File is larger than" in err_str:
            return {"error": "size_limit", "size": MAX_FILE_SIZE + 1}
        log.warning("ytdlp_download_failed", error=err_str, url=url)
        return None


async def _download_direct_http(url: str, dest_dir: str) -> Optional[dict]:
    """Download direct video file over HTTP/HTTPS with stream size check."""
    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            head = await client.head(url)
            content_length = head.headers.get("content-length")
            if content_length and int(content_length) > MAX_FILE_SIZE:
                return {"error": "size_limit", "size": int(content_length)}

            dest_path = os.path.join(dest_dir, f"{uuid.uuid4().hex}.mp4")
            total = 0
            async with client.stream("GET", url) as response:
                if response.status_code != 200:
                    return None
                with open(dest_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        total += len(chunk)
                        if total > MAX_FILE_SIZE:
                            f.close()
                            if os.path.exists(dest_path):
                                os.remove(dest_path)
                            return {"error": "size_limit", "size": total}
                        f.write(chunk)

            if total == 0:
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                return None

            filename = url.split("/")[-1].split("?")[0] or "Video"
            return {
                "file_path": dest_path,
                "title": filename,
                "duration": 0,
                "width": None,
                "height": None,
                "size_mb": round(total / 1024 / 1024, 2),
            }
    except Exception as e:
        log.warning("direct_http_download_failed", error=str(e), url=url)
        return None


async def download_video(url: str) -> Optional[dict]:
    """Download video from any web page or direct URL."""
    dest_dir = tempfile.gettempdir()

    # 1. Try yt-dlp (handles YouTube, Instagram, TikTok, Facebook, Twitter, and hundreds of sites)
    res = await asyncio.to_thread(_download_with_ytdlp, url, dest_dir)
    if res:
        return res

    # 2. Try direct streaming download for video files
    lower_url = url.lower()
    if any(ext in lower_url for ext in (".mp4", ".mov", ".webm", ".mkv", ".avi", "video")):
        res_http = await _download_direct_http(url, dest_dir)
        if res_http:
            return res_http

    return None
