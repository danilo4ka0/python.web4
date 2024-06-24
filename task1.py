import http.server
import socketserver
import threading
import socket
import os
import json
from datetime import datetime
from urllib.parse import parse_qs

# Constants
HOST_NAME = 'localhost'
HTTP_PORT = 3001  # Змінили з 3000 на 3001
UDP_PORT = 5001  # Змінили з 5000 на 5001

class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/message':
            self.path = '/message.html'
        elif self.path.startswith('/static/'):
            self.path = self.path
        elif self.path == '/favicon.ico':
            self.path = '/static/logo.png'
        else:
            self.path = '/error.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == '/send_message':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            post_data = parse_qs(post_data)

            username = post_data['username'][0]
            message = post_data['message'][0]
            data = {
                "username": username,
                "message": message
            }
            send_to_socket_server(data)
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()

def send_to_socket_server(data):
    UDP_IP = "127.0.0.1"
    MESSAGE = json.dumps(data).encode('utf-8')

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))

def run_http_server():
    web_dir = '/mnt/data/front-init'
    os.chdir(web_dir)
    print(f"Working directory changed to: {os.getcwd()}")
    print(f"Files in directory: {os.listdir(web_dir)}")
    with socketserver.TCPServer((HOST_NAME, HTTP_PORT), SimpleHTTPRequestHandler) as httpd:
        print(f"Serving HTTP on {HOST_NAME}:{HTTP_PORT}")
        httpd.serve_forever()

def run_udp_server():
    UDP_IP = "127.0.0.1"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    if not os.path.exists('storage'):
        os.makedirs('storage')
    data_file = os.path.join('storage', 'data.json')

    while True:
        data, addr = sock.recvfrom(1024)
        message = json.loads(data.decode('utf-8'))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        if os.path.exists(data_file):
            with open(data_file, 'r') as file:
                file_data = json.load(file)
        else:
            file_data = {}

        file_data[timestamp] = message

        with open(data_file, 'w') as file:
            json.dump(file_data, file, indent=4)

if __name__ == "__main__":
    http_thread = threading.Thread(target=run_http_server)
    udp_thread = threading.Thread(target=run_udp_server)

    http_thread.start()
    udp_thread.start()

    http_thread.join()
    udp_thread.join()
