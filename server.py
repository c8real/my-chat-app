from flask import Flask, send_file
from flask_socketio import SocketIO, emit
import random

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

username_colors = {}


def random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))


def get_color(username):
    if username not in username_colors:
        username_colors[username] = random_color()

    return username_colors[username]


@app.route("/")
def home():
    return send_file("chat.html")


@socketio.on("send_message")
def handle_message(data):
    username = data.get("username", "").strip()
    message = data.get("message", "").strip()

    if not username or not message:
        return

    color = get_color(username)

    emit(
        "new_message",
        {
            "username": username,
            "message": message,
            "color": color
        },
        broadcast=True
    )


if __name__ == "__main__":
    print("================================")
    print("       CHAT SERVER RUNNING")
    print("================================")
    print("Open: http://127.0.0.1:5000")
    print("")

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    print("CHAT SERVER RUNNING")
    print(f"Port: {port}")

socketio.run(
    app,
    host="0.0.0.0",
    port=port,
    allow_unsafe_werkzeug=True
)
