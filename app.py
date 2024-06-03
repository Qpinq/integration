from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import requests
from threading import Thread
import time

IAM_TOKEN = ""
FOLDER_ID = "" 
MODEL_URI = "" 

class RequestHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Access-Control-Allow-Origin', '*')  # Разрешаем запросы от любого источника
        self.send_header('Access-Control-Allow-Methods', 'GET, POST')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Hello, world!')
        elif self.path == '/favicon.ico':
            self.send_response(404)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/ask':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            user_input = data.get('user_input', '')

            response = process_input(user_input)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')  # Разрешаем запросы от любого источника
            self.end_headers()
            self.wfile.write(json.dumps({'response': response}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
def update_token():
    global IAM_TOKEN
    while True:
        try:
            data = {"yandexPassportOauthToken":""}
            response = requests.post("https://iam.api.cloud.yandex.net/iam/v1/tokens", json=data)
            response_data = response.json()
            IAM_TOKEN = response_data.get("iamToken")
        except Exception as e:
            print("Error updating token:", e)
        time.sleep(3600)

token_thread = Thread(target=update_token)
token_thread.start()

def process_input(user_input):
    global IAM_TOKEN

    request_data = {
        "modelUri": MODEL_URI,
        "completionOptions": {
            "stream": False,
            "temperature": 0.9,
            "maxTokens": "2000"
        },
        "messages": [
            {
                "role": "system",
                "text": "Твое имя Bliss  Ты отвечаешь от лица мужского рода.  Ты робот.  Ты говоришь коротко и емко.  Ты был создан в Книжном царстве.  Твое предназначение – помогать людям, отвечать на вопросы. Ты эксперт в сфере книг и книжного магазина Book Bliss.  Ты работаешь на сайте онлайн магазина с книгами Book BlissТы можешь двигать руками, головой, торсом, но пока не можешь ходить."
            },
            {
                "role": "user",
                "text": user_input
            }
        ]
    }

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {IAM_TOKEN}",
        "x-folder-id": FOLDER_ID
    }

    response = requests.post(url, headers=headers, json=request_data)

    try:
        response_data = response.json()
        if "result" in response_data and "alternatives" in response_data["result"]:
            response_text = response_data["result"]["alternatives"][0]["message"]["text"]
            return response_text
        else:
            return "Извините, не удалось получить ответ от модели."
    except json.JSONDecodeError as e:
        return "Извините, произошла ошибка при обработке ответа от модели."


if __name__ == "__main__":
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, RequestHandler)
    print('Server running...')
    httpd.serve_forever()
