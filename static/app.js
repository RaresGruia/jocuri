const socket = io();

const pieces = {
  white: { K: "♔", Q: "♕", R: "♖", B: "♗", N: "♘", P: "♙" },
  black: { K: "♚", Q: "♛", R: "♜", B: "♝", N: "♞", P: "♟" },
};

let myColor = null;
let roomCode = null;
let gameState = null;
let selected = null;
let legalMoves = [];
let pendingPromotion = null;

const lobby = document.getElementById("lobby");
const game = document.getElementById("game");
const board = document.getElementById("board");
const lobbyMessage = document.getElementById("lobbyMessage");
const gameMessage = document.getElementById("gameMessage");
const roomCodeInput = document.getElementById("roomCodeInput");
const roomCodeLabel = document.getElementById("roomCode");
const playerLabel = document.getElementById("playerLabel");
const gameStatus = document.getElementById("gameStatus");
const turnDot = document.getElementById("turnDot");
const history = document.getElementById("history");
const capturedWhite = document.getElementById("capturedWhite");
const capturedBlack = document.getElementById("capturedBlack");
const promotion = document.getElementById("promotion");

document.getElementById("createRoom").addEventListener("click", () => {
  lobbyMessage.textContent = "Creating room...";
  socket.emit("create_room");
});

document.getElementById("joinRoom").addEventListener("click", joinRoom);
roomCodeInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") joinRoom();
});

document.getElementById("restartGame").addEventListener("click", () => {
  socket.emit("restart_game");
});

document.getElementById("leaveRoom").addEventListener("click", () => {
  socket.emit("leave_current_room");
  showLobby();
});

document.querySelectorAll("[data-piece]").forEach((button) => {
  button.addEventListener("click", () => {
    if (!pendingPromotion) return;
    socket.emit("make_move", { ...pendingPromotion, promotion: button.dataset.piece });
    pendingPromotion = null;
    promotion.classList.add("hidden");
  });
});

function joinRoom() {
  const code = roomCodeInput.value.trim().toUpperCase();
  if (!code) {
    lobbyMessage.textContent = "Enter a room code.";
    return;
  }
  lobbyMessage.textContent = "Joining room...";
  socket.emit("join_room_code", { roomCode: code });
}

socket.on("joined", (data) => {
  myColor = data.color;
  roomCode = data.roomCode;
  lobby.classList.add("hidden");
  game.classList.remove("hidden");
  roomCodeLabel.textContent = roomCode;
  playerLabel.textContent = `You are ${capitalize(myColor)}`;
  gameMessage.textContent = myColor === "white" ? "Share this room code with Black." : "Connected as Black.";
});

socket.on("room_state", (data) => {
  roomCode = data.roomCode;
  gameState = data.game;
  selected = null;
  legalMoves = [];
  pendingPromotion = null;
  promotion.classList.add("hidden");
  roomCodeLabel.textContent = roomCode;
  render();
});

socket.on("legal_moves_result", (data) => {
  if (!selected || sameSquare(selected, data.square) === false) return;
  legalMoves = data.moves || [];
  renderBoard();
});

socket.on("error_message", (data) => {
  const message = data.message || "Something went wrong.";
  if (game.classList.contains("hidden")) {
    lobbyMessage.textContent = message;
  } else {
    gameMessage.textContent = message;
  }
});

socket.on("player_left", (data) => {
  gameMessage.textContent = `${capitalize(data.color || "A player")} disconnected.`;
});

function showLobby() {
  myColor = null;
  roomCode = null;
  gameState = null;
  selected = null;
  legalMoves = [];
  roomCodeInput.value = "";
  game.classList.add("hidden");
  lobby.classList.remove("hidden");
  lobbyMessage.textContent = "";
}

function render() {
  if (!gameState) return;
  renderBoard();
  gameStatus.textContent = gameState.status;
  turnDot.classList.toggle("black", gameState.turn === "black");
  gameMessage.textContent = gameState.turn === myColor && !gameState.gameOver
    ? "Your move."
    : gameState.gameOver
      ? "Game finished."
      : "Waiting for opponent.";
  renderCaptured();
  renderHistory();
}

function renderBoard() {
  board.innerHTML = "";
  const legalMap = new Map(legalMoves.map((move) => [move.end.join(","), move]));

  for (let r = 0; r < 8; r += 1) {
    for (let c = 0; c < 8; c += 1) {
      const square = document.createElement("button");
      square.className = `square ${(r + c) % 2 === 0 ? "light" : "dark"}`;
      square.type = "button";
      square.dataset.row = r;
      square.dataset.col = c;

      if (selected && selected[0] === r && selected[1] === c) {
        square.classList.add("selected");
      }

      const legal = legalMap.get(`${r},${c}`);
      if (legal) {
        const pieceOnTarget = gameState.board[r][c];
        square.classList.add(pieceOnTarget || legal.enPassant ? "capture" : "legal");
      }

      const piece = gameState.board[r][c];
      if (piece) {
        const span = document.createElement("span");
        span.className = `piece ${piece.color}`;
        span.textContent = pieces[piece.color][piece.kind];
        square.appendChild(span);
      }

      square.addEventListener("click", () => handleSquareClick(r, c));
      board.appendChild(square);
    }
  }
}

function handleSquareClick(r, c) {
  if (!gameState || gameState.gameOver) return;
  if (gameState.turn !== myColor) {
    gameMessage.textContent = "It is not your turn.";
    return;
  }

  const targetMove = legalMoves.find((move) => sameSquare(move.end, [r, c]));
  if (selected && targetMove) {
    const piece = gameState.board[selected[0]][selected[1]];
    const promotes = piece && piece.kind === "P" && (r === 0 || r === 7);
    const payload = { start: selected, end: [r, c] };
    if (promotes) {
      pendingPromotion = payload;
      promotion.classList.remove("hidden");
    } else {
      socket.emit("make_move", payload);
    }
    selected = null;
    legalMoves = [];
    renderBoard();
    return;
  }

  const piece = gameState.board[r][c];
  if (piece && piece.color === myColor) {
    selected = [r, c];
    legalMoves = [];
    socket.emit("legal_moves", { square: selected });
  } else {
    selected = null;
    legalMoves = [];
    renderBoard();
  }
}

function renderCaptured() {
  capturedWhite.textContent = (gameState.captured.white || []).map((piece) => pieces[piece.color][piece.kind]).join(" ");
  capturedBlack.textContent = (gameState.captured.black || []).map((piece) => pieces[piece.color][piece.kind]).join(" ");
}

function renderHistory() {
  history.innerHTML = "";
  gameState.history.slice(-30).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    history.appendChild(li);
  });
}

function sameSquare(a, b) {
  return Boolean(a && b && a[0] === b[0] && a[1] === b[1]);
}

function capitalize(value) {
  if (!value) return "";
  return value.charAt(0).toUpperCase() + value.slice(1);
}
