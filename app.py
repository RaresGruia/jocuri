import os
import random
import string
from threading import Lock

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

from chess import ChessGame


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

rooms = {}
sid_to_room = {}
rooms_lock = Lock()


def make_room_code():
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choice(alphabet) for _ in range(5))
        if code not in rooms:
            return code


def public_room(room_code):
    room = rooms[room_code]
    return {
        "roomCode": room_code,
        "players": {
            "white": bool(room["players"].get("white")),
            "black": bool(room["players"].get("black")),
        },
        "game": room["game"].serialize(),
    }


def emit_room_state(room_code):
    socketio.emit("room_state", public_room(room_code), room=room_code)


def cleanup_player(sid):
    with rooms_lock:
        room_code = sid_to_room.pop(sid, None)
        if not room_code or room_code not in rooms:
            return None, None
        room = rooms[room_code]
        lost_color = None
        for color, player_sid in list(room["players"].items()):
            if player_sid == sid:
                room["players"][color] = None
                lost_color = color
        empty = not room["players"]["white"] and not room["players"]["black"]
        if empty:
            del rooms[room_code]
            return room_code, lost_color
        return room_code, lost_color


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("create_room")
def create_room():
    with rooms_lock:
        room_code = make_room_code()
        rooms[room_code] = {
            "game": ChessGame(),
            "players": {"white": request.sid, "black": None},
        }
        sid_to_room[request.sid] = room_code
    join_room(room_code)
    emit("joined", {"roomCode": room_code, "color": "white"})
    emit_room_state(room_code)


@socketio.on("join_room_code")
def join_room_code(data):
    room_code = str(data.get("roomCode", "")).strip().upper()
    with rooms_lock:
        room = rooms.get(room_code)
        if not room:
            emit("error_message", {"message": "Room not found"})
            return
        if room["players"]["black"] and room["players"]["black"] != request.sid:
            emit("error_message", {"message": "Room already has two players"})
            return
        room["players"]["black"] = request.sid
        sid_to_room[request.sid] = room_code
    join_room(room_code)
    emit("joined", {"roomCode": room_code, "color": "black"})
    emit_room_state(room_code)


@socketio.on("legal_moves")
def legal_moves(data):
    room_code = sid_to_room.get(request.sid)
    if not room_code:
        emit("legal_moves_result", {"moves": []})
        return
    square = data.get("square")
    with rooms_lock:
        room = rooms.get(room_code)
        if not room:
            emit("legal_moves_result", {"moves": []})
            return
        color = "white" if room["players"]["white"] == request.sid else "black"
        moves = room["game"].legal_moves_payload(square, color)
    emit("legal_moves_result", {"square": square, "moves": moves})


@socketio.on("make_move")
def make_move(data):
    room_code = sid_to_room.get(request.sid)
    if not room_code:
        emit("error_message", {"message": "You are not in a room"})
        return

    with rooms_lock:
        room = rooms.get(room_code)
        if not room:
            emit("error_message", {"message": "Room no longer exists"})
            return
        player_color = "white" if room["players"]["white"] == request.sid else "black"
        ok, message = room["game"].apply_payload(data, player_color)
        if not ok:
            emit("error_message", {"message": message})
            return

    emit_room_state(room_code)


@socketio.on("restart_game")
def restart_game():
    room_code = sid_to_room.get(request.sid)
    if not room_code:
        return
    with rooms_lock:
        room = rooms.get(room_code)
        if not room:
            return
        room["game"].reset()
    emit_room_state(room_code)


@socketio.on("leave_current_room")
def leave_current_room():
    room_code, lost_color = cleanup_player(request.sid)
    if room_code:
        leave_room(room_code)
        socketio.emit("player_left", {"color": lost_color}, room=room_code)
        if room_code in rooms:
            emit_room_state(room_code)


@socketio.on("disconnect")
def disconnect():
    room_code, lost_color = cleanup_player(request.sid)
    if room_code and room_code in rooms:
        socketio.emit("player_left", {"color": lost_color}, room=room_code)
        emit_room_state(room_code)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        debug=False,
        allow_unsafe_werkzeug=True
    )
