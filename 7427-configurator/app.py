"""Run the local 7427 browser configurator."""
import argparse
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import webbrowser
from threading import Timer

from configurator import CURVE, CURVE_COUNT, build, bundle, json_bytes, load_stock

STATIC = Path(__file__).resolve().parent / 'static'
ASSETS = {'/': ('index.html', 'text/html'), '/app.css': ('app.css', 'text/css'),
          '/app.js': ('app.js', 'text/javascript')}


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, content_type, body, filename=None):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        if filename:
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path not in ASSETS:
            return self.send_error(404)
        filename, content_type = ASSETS[self.path]
        self.reply(200, content_type + '; charset=utf-8', (STATIC/filename).read_bytes())

    def do_POST(self):
        if self.path not in ('/api/identify', '/api/preview', '/api/build'):
            return self.send_error(404)
        try:
            if self.headers.get_content_type() != 'application/json':
                raise ValueError('Expected a JSON request.')
            length = int(self.headers.get('Content-Length', '0'))
            if not 1 <= length <= 600000:
                raise ValueError('Request size is outside the supported limit.')
            request = json.loads(self.rfile.read(length))
            if not isinstance(request, dict) or not isinstance(request.get('rom'), str):
                raise ValueError('A stock ROM is required.')
            image = load_stock(base64.b64decode(request['rom'], validate=True))
            if self.path == '/api/identify':
                self.reply(200, 'application/json', json_bytes({'curve': list(image[CURVE:CURVE+CURVE_COUNT])}))
                return
            report, files = build(image, request.get('project'))
            if self.path == '/api/preview':
                self.reply(200, 'application/json', json_bytes(report))
            else:
                self.reply(200, 'application/zip', bundle(files), '7427-build.zip')
        except (ValueError, TypeError, RecursionError) as exc:
            self.reply(400, 'application/json', json_bytes({'error': str(exc)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8742)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    with ThreadingHTTPServer(('127.0.0.1', args.port), Handler) as server:
        url = f'http://127.0.0.1:{server.server_port}/'
        print(f'7427 Configurator · {url}', flush=True)
        if not args.no_browser:
            Timer(0.2, webbrowser.open, (url,)).start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
