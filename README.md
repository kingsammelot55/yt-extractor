# YT Extractor (GitHub Pages + yt-dlp)

A small web interface for downloading videos as MP4 or audio as MP3 using `yt-dlp`.

**Architecture:** GitHub Pages hosts the static frontend. A separate Python backend runs `yt-dlp` and FFmpeg. GitHub Pages cannot run Python or `yt-dlp` itself.

Use this only for videos you own, have permission to download, or that are otherwise legally available for downloading. Respect the platform's terms and copyright. This project does not bypass DRM, paywalls, or access controls.

## 1. Deploy the backend

1. Create a GitHub repository and upload the contents of this folder.
2. Deploy the `backend` directory as a Docker web service on a host that supports Docker (for example, Render).
3. Set these environment variables on the backend:
   - `API_KEY`: a long, random secret. Do not commit it to GitHub.
   - `FRONTEND_ORIGIN`: your exact GitHub Pages origin, for example `https://YOUR_USERNAME.github.io`.
4. The backend listens on the host-provided `PORT` (defaults to `8000`).
5. Copy the backend's public HTTPS URL.

The backend is protected by `API_KEY`. Enter that key in the website when using it. Do not publish the key or hard-code it into the frontend.

## 2. Deploy the frontend with GitHub Pages

1. Push this repository to GitHub.
2. In the repository, open **Settings → Pages**.
3. Under **Build and deployment**, choose **Deploy from a branch**.
4. Choose your branch (usually `main`) and the `/frontend` folder, then save.
5. Open the GitHub Pages URL.

If your Pages settings do not offer `/frontend` as a folder, copy the contents of `frontend/` into a `docs/` folder and select `/docs`.

## 3. Use it

1. Paste the backend HTTPS URL into **Backend URL**.
2. Enter the API key you configured on the backend.
3. Paste a supported video URL and choose MP4 or MP3.
4. Press **Get video info** or **Download**.

## Local backend development

From the `backend` folder:

```bash
pip install -r requirements.txt
# Install FFmpeg separately and make sure `ffmpeg` is on PATH.
# Set API_KEY to a private value before starting.
uvicorn app:app --host 0.0.0.0 --port 8000
```

Then open `frontend/index.html` in a browser and enter `http://localhost:8000` as the backend URL. For local testing, set `FRONTEND_ORIGIN` to `null` only if your browser sends that origin; otherwise use a local static server origin.

## Notes

- MP3 conversion requires FFmpeg.
- Downloads are processed by the backend, so the backend host's storage, bandwidth, and usage limits apply.
- Do not run an unrestricted public instance. Keep the API key private and use a host with appropriate usage limits.
