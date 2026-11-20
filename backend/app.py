import ipaddress
import os
import socket
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl

API_KEY = os.environ.get("API_KEY", "")
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "*")

if not API_KEY:
    raise RuntimeError("Set the API_KEY environment variable before starting the server.")

app = FastAPI(title="YT Extractor API")

allowed_origins = ["*"] if FRONTEND_ORIGIN == "*" else [FRONTEND_ORIGIN]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

class VideoRequest(BaseModel):
    url: HttpUrl
    format: str = "mp4"

def require_key(x_api_key: str = Header(default="")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key.")

def validate_public_url(url: str):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise HTTPException(status_code=400, detail="Enter a valid HTTP or HTTPS video URL.")
    host = parsed.hostname.lower()
    if host in {"localhost"} or host.endswith((".localhost", ".local")):
        raise HTTPException(status_code=400, detail="Local network URLs are not allowed.")
    try:
        addresses = socket.getaddrinfo(host, None)
        for item in addresses:
            ip = ipaddress.ip_address(item[4][0])
            if not ip.is_global:
                raise HTTPException(status_code=400, detail="Private or local network URLs are not allowed.")
    except socket.gaierror:
        raise HTTPException(status_code=400, detail="The video host could not be resolved.")

def ydl_base():
    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 20,
        "retries": 2,
    }

@app.get("/")
def health():
    return {"status": "ok", "service": "yt-extractor"}

@app.post("/api/info", dependencies=[Depends(require_key)])
def video_info(body: VideoRequest):
    url = str(body.url)
    validate_public_url(url)
    try:
        with yt_dlp.YoutubeDL({**ydl_base(), "skip_download": True}) as ydl:
            info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title") or "Untitled video",
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "extractor": info.get("extractor_key"),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read video information: {str(exc)[:300]}")

@app.post("/api/download", dependencies=[Depends(require_key)])
def download(body: VideoRequest):
    url = str(body.url)
    validate_public_url(url)
    fmt = body.format.lower()
    if fmt not in {"mp4", "mp3"}:
        raise HTTPException(status_code=400, detail="Format must be mp4 or mp3.")

    temp_dir = tempfile.mkdtemp(prefix="yt-extractor-")
    output = str(Path(temp_dir) / "%(title).150B.%(ext)s")
    options = {
        **ydl_base(),
        "outtmpl": output,
        "restrictfilenames": True,
        "max_filesize": 1024 * 1024 * 500,  # 500 MB
    }
    if fmt == "mp4":
        options.update({
            "format": "best[ext=mp4]/bestvideo[ext=mp4]+bestaudio/best",
            "merge_output_format": "mp4",
        })
    else:
        options.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])
        candidates = [p for p in Path(temp_dir).iterdir() if p.is_file()]
        if not candidates:
            raise RuntimeError("The extractor did not produce an output file.")
        result = max(candidates, key=lambda p: p.stat().st_size)
        media_type = "audio/mpeg" if fmt == "mp3" else "video/mp4"

        # FileResponse streams the result. A background task removes the temporary file.
        from starlette.background import BackgroundTask
        def cleanup():
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

        return FileResponse(
            result,
            media_type=media_type,
            filename=result.name,
            background=BackgroundTask(cleanup),
        )
    except Exception as exc:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=f"Download failed: {str(exc)[:300]}")
