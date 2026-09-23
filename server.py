import ipaddress
import os
from flask import Flask, send_from_directory, request, abort
from flask_socketio import SocketIO, join_room, leave_room, emit

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "c8real-chat-secret"
)

# Socket.IO server
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

# Keep track of connected users
users = {}

# ============================================================
# C2k School Network Firewall (Northern Ireland)
# ============================================================

SCHOOL_NETWORK = ipaddress.ip_network('85.31.136.0/21')

@app.before_request
def block_school_network():
    # Render passes the real visitor IP in the 'X-Forwarded-For' header
    x_forwarded = request.headers.get('X-Forwarded-For')
    
    if x_forwarded:
        # Grab the first IP in the chain (the actual visitor) and clean up spaces
        client_ip = x_forwarded.split(',')[0].strip()
    else:
        client_ip = request.remote_addr

    try:
        # Convert string to an IP object and check if it's inside the C2k block
        visitor_ip = ipaddress.ip_address(client_ip)
        if visitor_ip in SCHOOL_NETWORK:
            abort(403)  # Rejects the request instantly
    except ValueError:
        # If the IP string fails parsing for any reason, let it pass safely
        pass


# ============================================================
# Serve chat.html
# ============================================================

@app.route("/")
def index():
    return send_from_directory(".", "chat.html")


# ============================================================
# Health check
# ============================================================

@app.route("/health")
def health():
    return "c8real Chat is online!"


# ============================================================
# Join a server
# ============================================================

@socketio.on("join")
def handle_join(data):
    username = str(data.get("username", "Anonymous")).strip()
    server_code = str(data.get("server_code", "")).strip()

    if not username:
        username = "Anonymous"

    if not server_code:
        emit("error_message", {
            "message": "You need to enter a server code."
        })
        return

    # Remove spaces from the server code
    server_code = server_code.replace(" ", "")

    # Leave previous room if the user was already in one
    if request.sid in users:
        old_room = users[request.sid]["server_code"]

        leave_room(old_room)

        emit(
            "user_left",
            {
                "username": users[request.sid]["username"]
            },
            room=old_room
        )

    # Save user information
    users[request.sid] = {
        "username": username,
        "server_code": server_code
    }

    # Join the new room
    join_room(server_code)

    # Tell everyone in the room that the user joined
    emit(
        "user_joined",
        {
            "username": username
        },
        room=server_code
    )

    # Confirm to the person who joined
    emit(
        "joined",
        {
            "username": username,
            "server_code": server_code
        }
    )


# ============================================================
# Send a message
# ============================================================

@socketio.on("send_message")
def handle_message(data):
    if request.sid not in users:
        emit("error_message", {
            "message": "You are not in a server."
        })
        return

    message = str(data.get("message", "")).strip()

    if not message:
        return

    username = users[request.sid]["username"]
    server_code = users[request.sid]["server_code"]

    # Send message to everyone in the same server
    emit(
        "receive_message",
        {
            "username": username,
            "message": message
        },
        room=server_code
    )


# ============================================================
# Leave server
# ============================================================

@socketio.on("leave")
def handle_leave():
    if request.sid not in users:
        return

    username = users[request.sid]["username"]
    server_code = users[request.sid]["server_code"]

    leave_room(server_code)

    emit(
        "user_left",
        {
            "username": username
        },
        room=server_code
    )

    del users[request.sid]


# ============================================================
# Disconnect
# ============================================================

@socketio.on("disconnect")
def handle_disconnect():
    if request.sid not in users:
        return

    username = users[request.sid]["username"]
    server_code = users[request.sid]["server_code"]

    emit(
        "user_left",
        {
            "username": username
        },
        room=server_code
    )

    del users[request.sid]


# ============================================================
# Local development
#
# Render should NOT use this.
# Render should use:
#
# gunicorn --threads 100 --workers 1 server:app
#
# ============================================================

if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        allow_unsafe_werkzeug=True
    )
