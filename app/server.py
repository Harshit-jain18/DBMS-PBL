"""Presentation-facing HTTP server (standard library only).  Run:  python server.py   then open http://localhost:8000"""
import json, os, sys, logging, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import api, tests_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get('AIRLINE_DB', os.path.join(HERE, 'airline.db'))
LOCK = threading.Lock()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

def init_db(reset=False):
    if reset and os.path.exists(DB): os.remove(DB)
    if not os.path.exists(DB):
        c = api.connect(DB); api.build_database(c); c.close()
        logging.info('database created at %s', DB)

class Handler(BaseHTTPRequestHandler):
    server_version = 'AirlineDBMS/1.0'
    def log_message(self, fmt, *a): logging.info('%s %s', self.address_string(), fmt % a)
    def _send(self, status, payload, ctype='application/json'):
        data = payload if isinstance(payload, bytes) else json.dumps(payload, default=str).encode()
        self.send_response(status); self.send_header('Content-Type', ctype + ('; charset=utf-8' if 'json' in ctype or 'html' in ctype else ''))
        self.send_header('Content-Length', str(len(data))); self.send_header('X-Content-Type-Options', 'nosniff'); self.end_headers()
        self.wfile.write(data)
    def _body(self):
        n = int(self.headers.get('Content-Length') or 0)
        if n > 100_000: raise ValueError('body too large')
        raw = self.rfile.read(n) if n else b''
        if not raw: return {}
        return json.loads(raw.decode('utf-8'))
    def _route(self, method):
        u = urlparse(self.path); q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if method == 'GET' and not u.path.startswith('/api'):
            f = os.path.join(HERE, 'static', 'index.html')
            return self._send(200, open(f, 'rb').read(), 'text/html')
        try: body = self._body() if method in ('POST', 'PUT', 'DELETE') else {}
        except (ValueError, UnicodeDecodeError): return self._send(400, {'error': 'Request body must be valid JSON (max 100 KB)'})
        if u.path == '/api/tests/run' and method == 'POST':
            res = tests_matrix.run_matrix(); return self._send(200, res)
        if u.path == '/api/reset' and method == 'POST':
            with LOCK: init_db(reset=True)
            return self._send(200, {'reset': True})
        with LOCK:
            conn = api.connect(DB)
            try: status, payload = api.handle(conn, method, u.path, q, body, DB)
            finally: conn.close()
        self._send(status, payload)
    def do_GET(self): self._route('GET')
    def do_POST(self): self._route('POST')
    def do_PUT(self): self._route('PUT')
    def do_DELETE(self): self._route('DELETE')

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    init_db()
    print('Airline DBMS prototype running at http://localhost:%d  (Ctrl+C to stop)' % port)
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
