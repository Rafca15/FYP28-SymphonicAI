# server.py
import threading, socket, uuid, json
from http.server import HTTPServer, BaseHTTPRequestHandler

_server_instance = None

def start_server(midi_queue, host, port):
    global _server_instance
    if _server_instance:
        return _server_instance  # Return existing instance if already started

    class Handler(BaseHTTPRequestHandler):
        def _cors(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')

        def do_OPTIONS(self):
            self.send_response(200)
            self._cors()
            self.end_headers()

        def do_POST(self):
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length))
            midi_queue.put({
                "id": data.get("id", str(uuid.uuid4())),
                "blob": data["blob"]
            })
            self.send_response(200)
            self._cors()
            self.end_headers()

    # Bind to check port availability before launching server
    with socket.socket() as sock:
        sock.bind((host, port))

    server = HTTPServer((host, port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    _server_instance = server  # Save singleton instance
    return server


def stop_server():
    
    global _server_instance
    if _server_instance is None:
        return  # Nothing to stop

    _server_instance.shutdown()
    _server_instance.server_close()
    _server_instance = None
