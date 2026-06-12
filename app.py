import os
import random
import string
import time
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

hockey_rooms = {}
hockey_sid_to_room = {}
hockey_lock = Lock()
HOCKEY_W = 960
HOCKEY_H = 520
PADDLE_W = 18
PADDLE_H = 96
PUCK_R = 13
WIN_SCORE = 7
HOCKEY_TICK = 1 / 60


def make_room_code():
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choice(alphabet) for _ in range(5))
        if code not in rooms and code not in hockey_rooms:
            return code


class HockeyGame:
    def __init__(self):
        self.players = {"left": None, "right": None}
        self.spectators = set()
        self.score = {"left": 0, "right": 0}
        self.paddles = {
            "left": {"x": 42, "y": HOCKEY_H / 2 - PADDLE_H / 2, "target": HOCKEY_H / 2},
            "right": {"x": HOCKEY_W - 42 - PADDLE_W, "y": HOCKEY_H / 2 - PADDLE_H / 2, "target": HOCKEY_H / 2},
        }
        self.puck = {"x": HOCKEY_W / 2, "y": HOCKEY_H / 2, "vx": 0, "vy": 0}
        self.winner = None
        self.message = "Waiting for players"
        self.reset_puck(random.choice([-1, 1]))

    def reset_match(self):
        self.score = {"left": 0, "right": 0}
        self.winner = None
        self.message = "First to 7 wins"
        self.paddles["left"]["target"] = HOCKEY_H / 2
        self.paddles["right"]["target"] = HOCKEY_H / 2
        self.reset_puck(random.choice([-1, 1]))

    def reset_puck(self, direction):
        angle = random.uniform(-0.45, 0.45)
        speed = 420
        self.puck = {
            "x": HOCKEY_W / 2,
            "y": HOCKEY_H / 2,
            "vx": speed * direction,
            "vy": speed * angle,
        }

    def set_paddle_target(self, side, y):
        if side not in self.paddles:
            return
        try:
            y = float(y)
        except (TypeError, ValueError):
            return
        self.paddles[side]["target"] = max(PADDLE_H / 2, min(HOCKEY_H - PADDLE_H / 2, y))

    def update(self, dt):
        if self.winner or not self.players["left"] or not self.players["right"]:
            self.message = "Waiting for players" if not self.winner else f"{self.winner.title()} wins"
            return

        for paddle in self.paddles.values():
            desired_y = paddle["target"] - PADDLE_H / 2
            paddle["y"] += (desired_y - paddle["y"]) * min(1, 18 * dt)
            paddle["y"] = max(0, min(HOCKEY_H - PADDLE_H, paddle["y"]))

        puck = self.puck
        puck["x"] += puck["vx"] * dt
        puck["y"] += puck["vy"] * dt

        if puck["y"] <= PUCK_R:
            puck["y"] = PUCK_R
            puck["vy"] = abs(puck["vy"])
        elif puck["y"] >= HOCKEY_H - PUCK_R:
            puck["y"] = HOCKEY_H - PUCK_R
            puck["vy"] = -abs(puck["vy"])

        self.hit_paddle("left")
        self.hit_paddle("right")

        if puck["x"] < -PUCK_R:
            self.score_point("right")
        elif puck["x"] > HOCKEY_W + PUCK_R:
            self.score_point("left")

    def hit_paddle(self, side):
        puck = self.puck
        paddle = self.paddles[side]
        nearest_x = max(paddle["x"], min(puck["x"], paddle["x"] + PADDLE_W))
        nearest_y = max(paddle["y"], min(puck["y"], paddle["y"] + PADDLE_H))
        dx = puck["x"] - nearest_x
        dy = puck["y"] - nearest_y
        if dx * dx + dy * dy > PUCK_R * PUCK_R:
            return

        relative = (puck["y"] - (paddle["y"] + PADDLE_H / 2)) / (PADDLE_H / 2)
        speed = min(760, (abs(puck["vx"]) + 38) * 1.04)
        if side == "left" and puck["vx"] < 0:
            puck["x"] = paddle["x"] + PADDLE_W + PUCK_R
            puck["vx"] = speed
            puck["vy"] = relative * 360
        elif side == "right" and puck["vx"] > 0:
            puck["x"] = paddle["x"] - PUCK_R
            puck["vx"] = -speed
            puck["vy"] = relative * 360

    def score_point(self, side):
        self.score[side] += 1
        if self.score[side] >= WIN_SCORE:
            self.winner = side
            self.puck["vx"] = 0
            self.puck["vy"] = 0
            self.puck["x"] = HOCKEY_W / 2
            self.puck["y"] = HOCKEY_H / 2
            self.message = f"{side.title()} wins"
        else:
            self.message = f"{side.title()} scores"
            self.reset_puck(-1 if side == "left" else 1)

    def public_state(self, room_code):
        return {
            "roomCode": room_code,
            "width": HOCKEY_W,
            "height": HOCKEY_H,
            "paddles": {
                side: {"x": p["x"], "y": p["y"], "w": PADDLE_W, "h": PADDLE_H}
                for side, p in self.paddles.items()
            },
            "puck": {"x": self.puck["x"], "y": self.puck["y"], "r": PUCK_R},
            "score": self.score,
            "winner": self.winner,
            "message": self.message,
            "players": {side: bool(sid) for side, sid in self.players.items()},
            "spectators": len(self.spectators),
        }


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


@app.route("/hockey")
def hockey():
    return render_template("hockey.html")


def hockey_room_name(room_code):
    return f"hockey-{room_code}"


def emit_hockey_state(room_code):
    game = hockey_rooms.get(room_code)
    if game:
        socketio.emit("hockey_state", game.public_state(room_code), room=hockey_room_name(room_code))


def cleanup_hockey_player(sid):
    with hockey_lock:
        room_code = hockey_sid_to_room.pop(sid, None)
        if not room_code or room_code not in hockey_rooms:
            return None, None
        game = hockey_rooms[room_code]
        lost_side = None
        for side, player_sid in list(game.players.items()):
            if player_sid == sid:
                game.players[side] = None
                lost_side = side
        game.spectators.discard(sid)
        if not game.players["left"] and not game.players["right"] and not game.spectators:
            del hockey_rooms[room_code]
            return room_code, lost_side
        if lost_side:
            game.message = f"{lost_side.title()} disconnected"
        return room_code, lost_side


@socketio.on("hockey_create_room")
def hockey_create_room():
    with hockey_lock:
        room_code = make_room_code()
        game = HockeyGame()
        game.players["left"] = request.sid
        game.message = "Waiting for Player 2"
        hockey_rooms[room_code] = game
        hockey_sid_to_room[request.sid] = room_code
    join_room(hockey_room_name(room_code))
    emit("hockey_joined", {"roomCode": room_code, "side": "left", "spectator": False})
    emit_hockey_state(room_code)


@socketio.on("hockey_join_room")
def hockey_join_room(data):
    room_code = str(data.get("roomCode", "")).strip().upper()
    with hockey_lock:
        game = hockey_rooms.get(room_code)
        if not game:
            emit("hockey_error", {"message": "Room not found"})
            return

        side = None
        spectator = False
        if not game.players["right"]:
            side = "right"
            game.players["right"] = request.sid
            game.message = "First to 7 wins"
        elif not game.players["left"]:
            side = "left"
            game.players["left"] = request.sid
            game.message = "First to 7 wins"
        else:
            side = "spectator"
            spectator = True
            game.spectators.add(request.sid)

        hockey_sid_to_room[request.sid] = room_code
    join_room(hockey_room_name(room_code))
    emit("hockey_joined", {"roomCode": room_code, "side": side, "spectator": spectator})
    emit_hockey_state(room_code)


@socketio.on("hockey_paddle")
def hockey_paddle(data):
    room_code = hockey_sid_to_room.get(request.sid)
    if not room_code:
        return
    with hockey_lock:
        game = hockey_rooms.get(room_code)
        if not game:
            return
        side = None
        for paddle_side, player_sid in game.players.items():
            if player_sid == request.sid:
                side = paddle_side
                break
        if side:
            game.set_paddle_target(side, data.get("y"))


@socketio.on("hockey_restart")
def hockey_restart():
    room_code = hockey_sid_to_room.get(request.sid)
    if not room_code:
        return
    with hockey_lock:
        game = hockey_rooms.get(room_code)
        if not game or request.sid not in game.players.values():
            return
        game.reset_match()
    emit_hockey_state(room_code)


@socketio.on("hockey_leave")
def hockey_leave():
    room_code, lost_side = cleanup_hockey_player(request.sid)
    if room_code:
        leave_room(hockey_room_name(room_code))
        socketio.emit("hockey_player_left", {"side": lost_side}, room=hockey_room_name(room_code))
        emit_hockey_state(room_code)


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
    hockey_room_code, lost_side = cleanup_hockey_player(request.sid)
    if hockey_room_code and hockey_room_code in hockey_rooms:
        socketio.emit("hockey_player_left", {"side": lost_side}, room=hockey_room_name(hockey_room_code))
        emit_hockey_state(hockey_room_code)


def hockey_loop():
    last = time.time()
    while True:
        socketio.sleep(HOCKEY_TICK)
        now = time.time()
        dt = min(0.05, now - last)
        last = now
        with hockey_lock:
            room_codes = list(hockey_rooms.keys())
            for room_code in room_codes:
                game = hockey_rooms.get(room_code)
                if game:
                    game.update(dt)
                    state = game.public_state(room_code)
                    socketio.emit("hockey_state", state, room=hockey_room_name(room_code))


socketio.start_background_task(hockey_loop)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        debug=False,
        allow_unsafe_werkzeug=True
    )
