import socket
import sys
from io import StringIO

class SimpleWSGIServer:
    def __init__(self, host, port, application):
        self.host = host
        self.port = port
        self.application = application
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(1)
        print(f"🚀 Server listening on http://{host}:{port}")

    def serve_forever(self):
        while True:
            # 1. Wacht op een verbinding
            client_connection, client_address = self.server_socket.accept()
            self.handle_request(client_connection)

    def handle_request(self, client_connection):
        try:
            # 1. Lees tot we de headers hebben (\r\n\r\n)
            request_data = b""
            while b'\r\n\r\n' not in request_data:
                chunk = client_connection.recv(4096)
                if not chunk:
                    return # Verbinding verbroken
                request_data += chunk
                if len(request_data) > 65536: # Protection tegen te grote headers
                    return

            # 2. Splits headers en (deel van) body
            header_bytes, body_bytes = request_data.split(b'\r\n\r\n', 1)
            
            header_str = header_bytes.decode('iso-8859-1')
            request_lines = header_str.splitlines()

            if not request_lines:
                return
                
            print(f"📥 Request: {request_lines[0]}")

            # Parse headers om Content-Length te vinden
            headers = {}
            for line in request_lines[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().upper()] = value.strip()

            content_length = int(headers.get('CONTENT-LENGTH', 0))

            # 3. Lees de rest van de body als dat nodig is
            while len(body_bytes) < content_length:
                chunk = client_connection.recv(4096)
                if not chunk:
                    break
                body_bytes += chunk

            # Simpele parsing: GET /path HTTP/1.1
            try:
                method, path, version = request_lines[0].split()
            except ValueError:
                method, path, version = "GET", "/", "HTTP/1.1"

            # 4. Bouw de WSGI 'environ' dictionary
            from io import BytesIO
            
            environ = {
                'wsgi.version': (1, 0),
                'wsgi.url_scheme': 'http',
                'wsgi.input': BytesIO(body_bytes),
                'wsgi.errors': sys.stderr,
                'wsgi.multithread': False,
                'wsgi.multiprocess': False,
                'wsgi.run_once': False,
                'REQUEST_METHOD': method,
                'PATH_INFO': path,
                'SERVER_NAME': self.host,
                'SERVER_PORT': str(self.port),
            }

            # Headers toevoegen aan environ
            for key, value in headers.items():
                wsgi_key = key.replace('-', '_')
                if wsgi_key in ['CONTENT_TYPE', 'CONTENT_LENGTH']:
                    environ[wsgi_key] = value
                else:
                    environ[f'HTTP_{wsgi_key}'] = value

            # 5. Definieer de start_response functie
            headers_container = {'status': '200 OK', 'headers': []}
            headers_sent = []

            def start_response(status, response_headers, exc_info=None):
                headers_container['status'] = status
                headers_container['headers'] = response_headers
                return write

            def write(data):
                if not headers_sent:
                    status = headers_container['status']
                    response_headers = headers_container['headers']
                    
                    response = f"HTTP/1.1 {status}\r\n"
                    for header in response_headers:
                        response += f"{header[0]}: {header[1]}\r\n"
                    response += "\r\n"
                    
                    client_connection.sendall(response.encode('iso-8859-1'))
                    headers_sent.append(True)
                
                client_connection.sendall(data)

            # 6. Roep de applicatie aan
            result = self.application(environ, start_response)
            
            for data in result:
                write(data)
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            client_connection.close()

# --- De Applicatie (het WSGI deel) ---

from run import app as flask_app

if __name__ == '__main__':
    # Start de server op poort 5100 (de standaard poort van de app)
    # Zorg dat je andere server (Gunicorn) uit staat!
    try:
        server = SimpleWSGIServer('0.0.0.0', 5100, flask_app)
        server.serve_forever()
    except OSError as e:
        if e.errno == 48:
            print("\n❌ Error: Poort 5100 is al in gebruik.")
            print("   Stop de bestaande applicatie eerst (./stop.sh of docker stop).")
            print("   Of verander de poort in het script.")
        else:
            raise
