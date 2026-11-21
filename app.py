import os, socket, ipaddress
from urllib.parse import urlparse
from flask import Flask, render_template, request, Response, jsonify
import requests

app = Flask(__name__)
MAX_BYTES = 250 * 1024 * 1024

def safe_url(url):
    p = urlparse(url)
    if p.scheme != 'https' or not p.hostname or p.username or p.password or p.port not in (None, 443):
        return False
    try:
        infos = socket.getaddrinfo(p.hostname, 443, type=socket.SOCK_STREAM)
        return bool(infos) and all(ipaddress.ip_address(x[4][0]).is_global for x in infos)
    except (OSError, ValueError):
        return False

@app.get('/')
def home():
    return render_template('index.html')

@app.post('/download')
def download():
    url = (request.form.get('url') or '').strip()
    if not safe_url(url):
        return jsonify(error='Please provide a public HTTPS direct video URL.'), 400
    try:
        # No redirects: prevents redirects to private addresses or non-video pages.
        r = requests.get(url, stream=True, timeout=(8, 25), allow_redirects=False,
                         headers={'User-Agent':'KuaishouPersonalDownloader/1.0'})
        if 300 <= r.status_code < 400:
            r.close()
            return jsonify(error='This link redirects. Please use the final direct video URL.'), 400
        r.raise_for_status()
        typ = r.headers.get('Content-Type', '').split(';')[0].strip().lower()
        if typ not in ('video/mp4','video/webm','video/quicktime','application/octet-stream'):
            r.close()
            return jsonify(error='This is not a direct video file. Kuaishou share/page links are not supported.'), 400
        size = int(r.headers.get('Content-Length','0') or 0)
        if size > MAX_BYTES:
            r.close()
            return jsonify(error='Video exceeds 250 MB limit.'), 413
        def chunks():
            total = 0
            try:
                for chunk in r.iter_content(65536):
                    if not chunk: continue
                    total += len(chunk)
                    if total > MAX_BYTES: break
                    yield chunk
            finally:
                r.close()
        ext = 'webm' if typ == 'video/webm' else 'mov' if typ == 'video/quicktime' else 'mp4'
        return Response(chunks(), mimetype=typ if typ != 'application/octet-stream' else 'video/mp4', headers={
            'Content-Disposition':f'attachment; filename="kuaishou_video.{ext}"',
            'Cache-Control':'no-store', 'X-Content-Type-Options':'nosniff'})
    except requests.RequestException:
        return jsonify(error='Unable to access this video. Try an accessible direct video link.'), 502

@app.get('/health')
def health(): return jsonify(status='ok')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
