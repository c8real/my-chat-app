from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
import random

app = Flask(__name__)
app.config["SECRET_KEY"] = "c8real-secret"

socketio = SocketIO(
    app,
    cors_allowed_origins="*"
)


@app.route("/")
def index():
    return render_template("chat.html")


@socketio.on("join_server")
def handle_join(data):

    username = data.get("username", "").strip()
    code = data.get("code", "").strip()

    if username == "" or code == "":
        return

    join_room(code)

    print(
        username,
        "joined server",
        code
    )


@socketio.on("leave_server")
def handle_leave(data):

    code = data.get("code", "").strip()

    if code == "":
        return

    leave_room(code)


@socketio.on("send_message")
def handle_message(data):

    username = data.get("username", "").strip()
    message = data.get("message", "").strip()
    code = data.get("code", "").strip()

    if username == "":
        return

    if message == "":
        return

    if code == "":
        return

    color = (
        "hsl("
        + str(random.randint(0, 360))
        + ", 80%, 65%)"
    )

    emit(
        "new_message",
        {
            "username": username,
            "message": message,
            "color": color,
            "code": code
        },
        room=code
    )


if __name__ == "__main__":

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000
    )
