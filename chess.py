from dataclasses import dataclass
import copy


FILES = "abcdefgh"
PROMOTION_CHOICES = {"Q", "R", "B", "N"}


@dataclass
class Piece:
    color: str
    kind: str
    moved: bool = False


@dataclass
class Move:
    start: tuple
    end: tuple
    promotion: str = None
    castle: bool = False
    en_passant: bool = False


def other(color):
    return "black" if color == "white" else "white"


def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def square_name(square):
    r, c = square
    return FILES[c] + str(8 - r)


def initial_board():
    board = [[None for _ in range(8)] for _ in range(8)]
    back = ["R", "N", "B", "Q", "K", "B", "N", "R"]
    for c, kind in enumerate(back):
        board[0][c] = Piece("black", kind)
        board[1][c] = Piece("black", "P")
        board[6][c] = Piece("white", "P")
        board[7][c] = Piece("white", kind)
    return board


class ChessGame:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board = initial_board()
        self.turn = "white"
        self.history = []
        self.captured = {"white": [], "black": []}
        self.en_passant_target = None
        self.status = "White to move"
        self.game_over = False
        self.winner = None

    def clone(self):
        new = ChessGame.__new__(ChessGame)
        new.board = copy.deepcopy(self.board)
        new.turn = self.turn
        new.history = self.history[:]
        new.captured = {"white": self.captured["white"][:], "black": self.captured["black"][:]}
        new.en_passant_target = self.en_passant_target
        new.status = self.status
        new.game_over = self.game_over
        new.winner = self.winner
        return new

    def piece_at(self, square):
        r, c = square
        return self.board[r][c]

    def find_king(self, color):
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece.color == color and piece.kind == "K":
                    return r, c
        return None

    def square_attacked(self, square, by_color):
        r, c = square
        pawn_dir = -1 if by_color == "white" else 1
        for dc in (-1, 1):
            pr, pc = r - pawn_dir, c + dc
            if in_bounds(pr, pc):
                piece = self.board[pr][pc]
                if piece and piece.color == by_color and piece.kind == "P":
                    return True

        for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc):
                piece = self.board[nr][nc]
                if piece and piece.color == by_color and piece.kind == "N":
                    return True

        rays = [
            (-1, 0, ("R", "Q")), (1, 0, ("R", "Q")), (0, -1, ("R", "Q")), (0, 1, ("R", "Q")),
            (-1, -1, ("B", "Q")), (-1, 1, ("B", "Q")), (1, -1, ("B", "Q")), (1, 1, ("B", "Q")),
        ]
        for dr, dc, attackers in rays:
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc):
                piece = self.board[nr][nc]
                if piece:
                    if piece.color == by_color and piece.kind in attackers:
                        return True
                    break
                nr += dr
                nc += dc

        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc):
                    piece = self.board[nr][nc]
                    if piece and piece.color == by_color and piece.kind == "K":
                        return True
        return False

    def in_check(self, color):
        king = self.find_king(color)
        return bool(king and self.square_attacked(king, other(color)))

    def pseudo_moves(self, square, include_castling=True):
        piece = self.piece_at(square)
        if not piece:
            return []

        r, c = square
        moves = []

        if piece.kind == "P":
            direction = -1 if piece.color == "white" else 1
            start_row = 6 if piece.color == "white" else 1
            one = (r + direction, c)
            if in_bounds(*one) and self.piece_at(one) is None:
                moves.append(Move(square, one))
                two = (r + 2 * direction, c)
                if r == start_row and in_bounds(*two) and self.piece_at(two) is None:
                    moves.append(Move(square, two))
            for dc in (-1, 1):
                target = (r + direction, c + dc)
                if not in_bounds(*target):
                    continue
                victim = self.piece_at(target)
                if victim and victim.color != piece.color:
                    moves.append(Move(square, target))
                elif target == self.en_passant_target:
                    moves.append(Move(square, target, en_passant=True))

        elif piece.kind == "N":
            for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
                target = (r + dr, c + dc)
                if in_bounds(*target):
                    victim = self.piece_at(target)
                    if victim is None or victim.color != piece.color:
                        moves.append(Move(square, target))

        elif piece.kind in ("B", "R", "Q"):
            dirs = []
            if piece.kind in ("B", "Q"):
                dirs += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            if piece.kind in ("R", "Q"):
                dirs += [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                while in_bounds(nr, nc):
                    victim = self.board[nr][nc]
                    if victim is None:
                        moves.append(Move(square, (nr, nc)))
                    else:
                        if victim.color != piece.color:
                            moves.append(Move(square, (nr, nc)))
                        break
                    nr += dr
                    nc += dc

        elif piece.kind == "K":
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    target = (r + dr, c + dc)
                    if in_bounds(*target):
                        victim = self.piece_at(target)
                        if victim is None or victim.color != piece.color:
                            moves.append(Move(square, target))
            if include_castling and not piece.moved and not self.in_check(piece.color):
                moves += self.castling_moves(square)

        return moves

    def castling_moves(self, square):
        r, _ = square
        piece = self.piece_at(square)
        moves = []
        if not piece or piece.kind != "K" or piece.moved:
            return moves

        for rook_col, king_target_col, empty_cols, safe_cols in [
            (7, 6, [5, 6], [5, 6]),
            (0, 2, [1, 2, 3], [3, 2]),
        ]:
            rook = self.board[r][rook_col]
            if not rook or rook.color != piece.color or rook.kind != "R" or rook.moved:
                continue
            if any(self.board[r][col] is not None for col in empty_cols):
                continue
            if any(self.square_attacked((r, col), other(piece.color)) for col in safe_cols):
                continue
            moves.append(Move(square, (r, king_target_col), castle=True))
        return moves

    def legal_moves_for(self, square, color=None):
        piece = self.piece_at(square)
        active_color = color or self.turn
        if not piece or piece.color != active_color:
            return []

        legal = []
        for move in self.pseudo_moves(square):
            test = self.clone()
            test.apply_move(move, switch_turn=False, record=False)
            if not test.in_check(piece.color):
                legal.append(move)
        return legal

    def all_legal_moves(self, color):
        moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece.color == color:
                    moves.extend(self.legal_moves_for((r, c), color))
        return moves

    def move_from_payload(self, payload):
        start = tuple(payload.get("start", ()))
        end = tuple(payload.get("end", ()))
        if len(start) != 2 or len(end) != 2 or not in_bounds(*start) or not in_bounds(*end):
            return None
        promotion = payload.get("promotion")
        if promotion:
            promotion = promotion.upper()
            if promotion not in PROMOTION_CHOICES:
                return None
        for move in self.legal_moves_for(start):
            if move.end == end:
                move.promotion = promotion
                return move
        return None

    def apply_payload(self, payload, player_color):
        if self.game_over:
            return False, "Game is over"
        if player_color != self.turn:
            return False, "It is not your turn"
        piece = self.piece_at(tuple(payload.get("start", ())))
        if not piece or piece.color != player_color:
            return False, "Select one of your pieces"
        move = self.move_from_payload(payload)
        if not move:
            return False, "Illegal move"
        if piece.kind == "P" and move.end[0] in (0, 7) and not move.promotion:
            return False, "Promotion choice required"
        self.apply_move(move, promotion_kind=move.promotion)
        return True, "Move played"

    def apply_move(self, move, switch_turn=True, record=True, promotion_kind=None):
        sr, sc = move.start
        er, ec = move.end
        piece = self.board[sr][sc]
        captured = None

        if move.en_passant:
            captured = self.board[sr][ec]
            self.board[sr][ec] = None
        else:
            captured = self.board[er][ec]

        self.board[er][ec] = piece
        self.board[sr][sc] = None
        piece.moved = True

        if move.castle:
            if ec == 6:
                rook = self.board[er][7]
                self.board[er][5] = rook
                self.board[er][7] = None
            else:
                rook = self.board[er][0]
                self.board[er][3] = rook
                self.board[er][0] = None
            rook.moved = True

        promoted_to = None
        if piece.kind == "P" and er in (0, 7):
            promoted_to = promotion_kind or move.promotion or "Q"
            piece.kind = promoted_to

        self.en_passant_target = None
        if piece.kind == "P" and abs(er - sr) == 2:
            self.en_passant_target = ((sr + er) // 2, sc)

        if captured and record:
            self.captured[piece.color].append(captured)

        if record:
            self.history.append(self.notation(move, piece, captured, promoted_to))

        if switch_turn:
            self.turn = other(self.turn)
            self.update_status()

    def notation(self, move, piece, captured, promoted_to):
        if move.castle:
            text = "O-O" if move.end[1] == 6 else "O-O-O"
        else:
            cap = "x" if captured or move.en_passant else "-"
            text = f"{piece.kind}{square_name(move.start)}{cap}{square_name(move.end)}"
            if promoted_to:
                text += f"={promoted_to}"
            if move.en_passant:
                text += " e.p."
        if self.in_check(other(piece.color)):
            text += "+"
        return f"{len(self.history) + 1}. {text}" if piece.color == "white" else text

    def update_status(self):
        self.game_over = False
        self.winner = None
        if self.in_check(self.turn):
            if not self.all_legal_moves(self.turn):
                self.status = f"Checkmate! {other(self.turn).title()} wins"
                self.game_over = True
                self.winner = other(self.turn)
            else:
                self.status = f"{self.turn.title()} is in check"
        else:
            if not self.all_legal_moves(self.turn):
                self.status = "Stalemate"
                self.game_over = True
            else:
                self.status = f"{self.turn.title()} to move"

    def legal_moves_payload(self, square, color):
        if color != self.turn:
            return []
        return [
            {
                "start": list(move.start),
                "end": list(move.end),
                "promotion": move.promotion,
                "castle": move.castle,
                "enPassant": move.en_passant,
            }
            for move in self.legal_moves_for(tuple(square), color)
        ]

    def serialize(self):
        board = []
        for row in self.board:
            out_row = []
            for piece in row:
                out_row.append(None if piece is None else {"color": piece.color, "kind": piece.kind})
            board.append(out_row)
        return {
            "board": board,
            "turn": self.turn,
            "status": self.status,
            "gameOver": self.game_over,
            "winner": self.winner,
            "history": self.history,
            "captured": {
                color: [{"color": p.color, "kind": p.kind} for p in pieces]
                for color, pieces in self.captured.items()
            },
            "check": self.in_check(self.turn),
        }
