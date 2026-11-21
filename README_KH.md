# Kuaishou Video Downloader (direct video files only)

## Render deployment
1. Upload all files to a GitHub repository.
2. Render > New > Web Service > connect repository.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
5. Deploy. Check `/health` for `{"status":"ok"}`.

This tool supports direct public HTTPS video file URLs, not Kuaishou share/page links. Use Kuaishou's built-in Save option for authorized downloads. The server enforces a 250 MB limit. Download only content you own or are authorized to save.
