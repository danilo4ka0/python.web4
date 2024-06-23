import http.server
import socketserver
import threading
import os
import urllib.parse
from datetime import datetime
import json
import socket

# Порт для HTTP сервера
PORT = 3000

# Порт для Socket сервера
SOCKET_PORT = 5000

# Шляхи до файлів
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
STORAGE_DIR = os.path.join(os.path.dirname(__file__), 'storage')
DATA_FILE = os.path.join(STORAGE_DIR, 'data.json')

# Клас для обробки HTTP запитів
class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        # Визначаємо шлях запиту
        path = self.path

        # Розбираємо запит для отримання шляху без параметрів
        parsed_path = urllib.parse.urlparse(path)
        clean_path = parsed_path.path

        # Відповідь на запити статичних ресурсів
        if clean_path == '/':
            clean_path = '/index.html'

        if clean_path.endswith('.html'):
            self.send_html(clean_path)
        elif clean_path.endswith('.css'):
            self.send_css(clean_path)
        elif clean_path.endswith('.png'):
            self.send_static_file(clean_path, 'image/png')
        else:
            self.send_error(404, "File not found")

    def do_POST(self):
        # Обробка POST запитів, наприклад, з форми
        if self.path == '/submit_message':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            self.process_form_data(post_data)

            # Перенаправлення користувача після обробки форми
            self.send_response(303)
            self.send_header('Location', '/index.html')
            self.end_headers()
        else:
            self.send_error(404, "File not found")

    def send_html(self, path):
        try:
            with open(os.path.join(TEMPLATE_DIR, path), 'rb') as file:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_error(404, "File not found")

    def send_css(self, path):
        try:
            with open(os.path.join(TEMPLATE_DIR, path), 'rb') as file:
                self.send_response(200)
                self.send_header('Content-type', 'text/css')
                self.end_headers()
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_error(404, "File not found")

    def send_static_file(self, path, content_type):
        try:
            with open(os.path.join(STATIC_DIR, os.path.basename(path)), 'rb') as file:
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.end_headers()
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_error(404, "File not found")

    def process_form_data(self, data):
        # Розбираємо дані форми
        parsed_data = urllib.parse.parse_qs(data)
        username = parsed_data.get('username', [''])[0]
        message = parsed_data.get('message', [''])[0]

        # Створюємо словник для збереження в JSON
        message_data = {
            'username': username,
            'message': message
        }

        # Отримуємо поточний час
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

        # Записуємо дані у файл data.json
        with open(DATA_FILE, 'r+') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {}

            data[current_time] = message_data
            file.seek(0)
            json.dump(data, file, indent=4)

# Функція для запуску HTTP сервера
def run_http_server():
    handler = MyHttpRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"HTTP server is running at http://localhost:{PORT}")
        httpd.serve_forever()

# Функція для обробки UDP запитів
def handle_udp_requests():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind(('', SOCKET_PORT))
        print(f"Socket server is running on UDP port {SOCKET_PORT}")

        while True:
            data, address = server_socket.recvfrom(1024)
            try:
                decoded_data = data.decode('utf-8')
                # Передача отриманих даних для обробки
                handle_socket_data(decoded_data)
            except UnicodeDecodeError:
                print("Error decoding UDP data")

# Функція для обробки отриманих даних через UDP
def handle_socket_data(data):
    # В цьому прикладі ми просто виводимо отримані дані
    print(f"Received UDP data: {data}")

# Запуск HTTP сервера та Socket сервера в окремих потоках
if __name__ == "__main__":
    # Створення папок, якщо вони ще не існують
    os.makedirs(TEMPLATE_DIR, exist_ok=True)
    os.makedirs(STATIC_DIR, exist_ok=True)
    os.makedirs(STORAGE_DIR, exist_ok=True)

    # Запуск HTTP сервера у окремому потоці
    http_server_thread = threading.Thread(target=run_http_server)
    http_server_thread.start()

    # Запуск Socket сервера у окремому потоці
    socket_server_thread = threading.Thread(target=handle_udp_requests)
    socket_server_thread.start()

    # Очікуємо завершення обох потоків
    http_server_thread.join()
    socket_server_thread.join()
