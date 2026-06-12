const socket = io();

const lobby = document.getElementById("lobby");
const gameView = document.getElementById("game");
const roomCodeInput = document.getElementById("roomCodeInput");
const lobbyMessage = document.getElementById("lobbyMessage");
const gameMessage = document.getElementById("gameMessage");
const roomCodeLabel = document.getElementById("roomCode");
const sideLabel = document.getElementById("sideLabel");
const leftScore = document.getElementById("leftScore");
const rightScore = document.getElementById("rightScore");
const connectionStatus = document.getElementById("connectionStatus");
const canvas = document.getElementById("rink");
const ctx = canvas.getContext("2d");

let state = null;
let side = null;
let roomCode = null;
let keys = new Set();
let pointerActive = false;
let lastSentY = null;
let lastSendAt = 0;

document.getElementById("createRoom").addEventListener("click", () => {
  lobbyMessage.textContent = "Creating room...";
  socket.emit("hockey_create_room");
});

document.getElementById("joinRoom").addEventListener("click", joinRoom);
roomCodeInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") joinRoom();
});

document.getElementById("restartMatch").addEventListener("click", () => {
  socket.emit("hockey_restart");
});

document.getElementById("leaveRoom").addEventListener("click", () => {
  socket.emit("hockey_leave");
  showLobby();
});

window.addEventListener("keydown", (event) => {
  keys.add(event.key);
});

window.addEventListener("keyup", (event) => {
  keys.delete(event.key);
});

canvas.addEventListener("pointerdown", (event) => {
  pointerActive = true;
  sendPointerY(event);
});

canvas.addEventListener("pointermove", (event) => {
  if (pointerActive) sendPointerY(event);
});

window.addEventListener("pointerup", () => {
  pointerActive = false;
});

function joinRoom() {
  const code = roomCodeInput.value.trim().toUpperCase();
  if (!code) {
    lobbyMessage.textContent = "Enter a room code.";
    return;
  }
  lobbyMessage.textContent = "Joining room...";
  socket.emit("hockey_join_room", { roomCode: code });
}

socket.on("hockey_joined", (data) => {
  side = data.side;
  roomCode = data.roomCode;
  roomCodeLabel.textContent = roomCode;
  sideLabel.textContent = data.spectator ? "Spectating" : `You are Player ${side === "left" ? "1" : "2"} (${side})`;
  lobby.classList.add("hidden");
  gameView.classList.remove("hidden");
  gameMessage.textContent = data.spectator ? "Room is full. Watching as spectator." : "Connected.";
});

socket.on("hockey_state", (nextState) => {
  state = nextState;
  roomCodeLabel.textContent = state.roomCode;
  leftScore.textContent = state.score.left;
  rightScore.textContent = state.score.right;
  connectionStatus.textContent = statusText();
  if (state.winner) {
    gameMessage.textContent = `${capitalize(state.winner)} side wins.`;
  } else {
    gameMessage.textContent = state.message || "";
  }
});

socket.on("hockey_error", (data) => {
  const message = data.message || "Something went wrong.";
  if (gameView.classList.contains("hidden")) lobbyMessage.textContent = message;
  else gameMessage.textContent = message;
});

socket.on("hockey_player_left", (data) => {
  gameMessage.textContent = data.side ? `${capitalize(data.side)} player disconnected.` : "A spectator left.";
});

socket.on("disconnect", () => {
  connectionStatus.textContent = "Disconnected from server";
});

function showLobby() {
  state = null;
  side = null;
  roomCode = null;
  roomCodeInput.value = "";
  lobbyMessage.textContent = "";
  lobby.classList.remove("hidden");
  gameView.classList.add("hidden");
}

function statusText() {
  if (!state) return "Connecting...";
  const p1 = state.players.left ? "P1 online" : "P1 missing";
  const p2 = state.players.right ? "P2 online" : "P2 missing";
  const watching = state.spectators ? ` · ${state.spectators} watching` : "";
  return `${p1} · ${p2}${watching}`;
}

function sendPointerY(event) {
  if (!canControl()) return;
  const rect = canvas.getBoundingClientRect();
  const y = ((event.clientY - rect.top) / rect.height) * state.height;
  sendPaddle(y);
}

function updateKeyboardControl() {
  if (!canControl() || pointerActive) return;
  const paddle = state.paddles[side];
  let y = paddle.y + paddle.h / 2;
  const speed = 11;
  if (side === "left") {
    if (keys.has("w") || keys.has("W")) y -= speed;
    if (keys.has("s") || keys.has("S")) y += speed;
  } else if (side === "right") {
    if (keys.has("ArrowUp")) y -= speed;
    if (keys.has("ArrowDown")) y += speed;
  }
  if (y !== paddle.y + paddle.h / 2) sendPaddle(y);
}

function sendPaddle(y) {
  const now = performance.now();
  if (lastSentY !== null && Math.abs(lastSentY - y) < 1 && now - lastSendAt < 70) return;
  lastSentY = y;
  lastSendAt = now;
  socket.emit("hockey_paddle", { y });
}

function canControl() {
  return state && (side === "left" || side === "right") && !state.winner;
}

function draw() {
  requestAnimationFrame(draw);
  updateKeyboardControl();
  drawTable();
}

function drawTable() {
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  const gradient = ctx.createLinearGradient(0, 0, w, h);
  gradient.addColorStop(0, "#082232");
  gradient.addColorStop(0.5, "#0b3346");
  gradient.addColorStop(1, "#071b29");
  ctx.fillStyle = gradient;
  roundRect(0, 0, w, h, 22);
  ctx.fill();

  ctx.strokeStyle = "rgba(126,232,255,.75)";
  ctx.lineWidth = 4;
  roundRect(12, 12, w - 24, h - 24, 18);
  ctx.stroke();

  ctx.setLineDash([14, 12]);
  ctx.strokeStyle = "rgba(238,248,255,.36)";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(w / 2, 28);
  ctx.lineTo(w / 2, h - 28);
  ctx.stroke();
  ctx.setLineDash([]);

  ctx.strokeStyle = "rgba(238,248,255,.34)";
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.arc(w / 2, h / 2, 86, 0, Math.PI * 2);
  ctx.stroke();

  ctx.fillStyle = "rgba(255,92,154,.28)";
  ctx.fillRect(0, h / 2 - 90, 10, 180);
  ctx.fillStyle = "rgba(82,217,255,.28)";
  ctx.fillRect(w - 10, h / 2 - 90, 10, 180);

  if (!state) {
    ctx.fillStyle = "#eef8ff";
    ctx.font = "700 32px Segoe UI";
    ctx.textAlign = "center";
    ctx.fillText("Waiting for match", w / 2, h / 2);
    return;
  }

  drawPaddle(state.paddles.left, "#ff5c9a");
  drawPaddle(state.paddles.right, "#52d9ff");
  drawPuck(state.puck);

  if (state.winner) {
    ctx.fillStyle = "rgba(0,0,0,.46)";
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = "#ffd166";
    ctx.font = "800 48px Segoe UI";
    ctx.textAlign = "center";
    ctx.fillText(`${capitalize(state.winner)} wins`, w / 2, h / 2);
  }
}

function drawPaddle(paddle, color) {
  ctx.shadowBlur = 22;
  ctx.shadowColor = color;
  ctx.fillStyle = color;
  roundRect(paddle.x, paddle.y, paddle.w, paddle.h, 10);
  ctx.fill();
  ctx.shadowBlur = 0;
  ctx.fillStyle = "rgba(255,255,255,.45)";
  roundRect(paddle.x + 4, paddle.y + 8, 4, paddle.h - 16, 4);
  ctx.fill();
}

function drawPuck(puck) {
  ctx.shadowBlur = 26;
  ctx.shadowColor = "#ffffff";
  ctx.fillStyle = "#f8fbff";
  ctx.beginPath();
  ctx.arc(puck.x, puck.y, puck.r, 0, Math.PI * 2);
  ctx.fill();
  ctx.shadowBlur = 0;
  ctx.strokeStyle = "#52d9ff";
  ctx.lineWidth = 3;
  ctx.stroke();
}

function roundRect(x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function capitalize(value) {
  if (!value) return "";
  return value.charAt(0).toUpperCase() + value.slice(1);
}

draw();
