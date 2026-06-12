import random
import sys
import time

import pygame


pygame.init()

WIDTH, HEIGHT = 1180, 820
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Klondike Solitaire")
clock = pygame.time.Clock()

CARD_W, CARD_H = 92, 132
GAP = 24
TOP_Y = 92
TABLEAU_Y = 260
TABLEAU_STEP_FACE_DOWN = 18
TABLEAU_STEP_FACE_UP = 32

STOCK_POS = (56, TOP_Y)
WASTE_POS = (172, TOP_Y)
FOUNDATION_X = 648
NEW_GAME_RECT = pygame.Rect(WIDTH - 178, 24, 138, 42)

GREEN = (28, 111, 73)
DARK_GREEN = (20, 82, 55)
FELT = (36, 132, 87)
CARD = (250, 247, 238)
CARD_EDGE = (222, 213, 190)
CARD_SHADOW = (16, 45, 34)
RED = (178, 39, 46)
BLACK = (26, 27, 31)
GOLD = (234, 190, 83)
BLUE = (39, 82, 145)
MUTED = (190, 206, 190)
WHITE = (246, 248, 242)
WIN_OVERLAY = (8, 38, 26, 190)

title_font = pygame.font.SysFont("georgia", 36, bold=True)
card_font = pygame.font.SysFont("georgia", 24, bold=True)
small_card_font = pygame.font.SysFont("georgia", 18, bold=True)
ui_font = pygame.font.SysFont("segoeui", 18, bold=True)
small_font = pygame.font.SysFont("segoeui", 14)

SUITS = ["spades", "hearts", "diamonds", "clubs"]
SUIT_SYMBOLS = {
    "spades": "♠",
    "hearts": "♥",
    "diamonds": "♦",
    "clubs": "♣",
}
RANK_LABELS = {
    1: "A",
    11: "J",
    12: "Q",
    13: "K",
}


class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.face_up = False
        self.rect = pygame.Rect(0, 0, CARD_W, CARD_H)

    @property
    def color(self):
        return RED if self.suit in ("hearts", "diamonds") else BLACK

    @property
    def label(self):
        return RANK_LABELS.get(self.rank, str(self.rank))


class DragState:
    def __init__(self, cards, source_type, source_index, grab_offset, start_pos):
        self.cards = cards
        self.source_type = source_type
        self.source_index = source_index
        self.grab_offset = grab_offset
        self.start_pos = start_pos
        self.x = start_pos[0]
        self.y = start_pos[1]


def card_is_red(card):
    return card.suit in ("hearts", "diamonds")


def tableau_x(index):
    return 56 + index * (CARD_W + GAP)


def foundation_pos(index):
    return (FOUNDATION_X + index * (CARD_W + GAP), TOP_Y)


def new_deck():
    deck = [Card(suit, rank) for suit in SUITS for rank in range(1, 14)]
    random.shuffle(deck)
    return deck


def new_game():
    deck = new_deck()
    tableau = [[] for _ in range(7)]

    for col in range(7):
        for row in range(col + 1):
            card = deck.pop()
            card.face_up = row == col
            tableau[col].append(card)

    return {
        "stock": deck,
        "waste": [],
        "tableau": tableau,
        "foundations": [[] for _ in range(4)],
        "drag": None,
        "message": "",
        "message_until": 0,
        "last_click_card": None,
        "last_click_time": 0,
        "won": False,
        "moves": 0,
    }


def set_message(state, text, seconds=1.8):
    state["message"] = text
    state["message_until"] = time.time() + seconds


def draw_background():
    screen.fill(GREEN)
    pygame.draw.rect(screen, DARK_GREEN, (0, 0, WIDTH, HEIGHT))

    for i in range(0, WIDTH, 44):
        pygame.draw.line(screen, (23, 95, 65), (i, 0), (i - 240, HEIGHT), 1)
    for i in range(-HEIGHT, WIDTH, 64):
        pygame.draw.line(screen, (42, 145, 98), (i, 0), (i + 270, HEIGHT), 1)

    pygame.draw.rect(screen, FELT, (26, 20, WIDTH - 52, HEIGHT - 44), border_radius=26)
    pygame.draw.rect(screen, (70, 164, 112), (26, 20, WIDTH - 52, HEIGHT - 44), 2, border_radius=26)

    title = title_font.render("Klondike Solitaire", True, WHITE)
    screen.blit(title, (52, 26))


def draw_button(rect, text, mouse):
    hover = rect.collidepoint(mouse)
    color = GOLD if hover else (238, 217, 151)
    pygame.draw.rect(screen, CARD_SHADOW, rect.move(0, 3), border_radius=10)
    pygame.draw.rect(screen, color, rect, border_radius=10)
    pygame.draw.rect(screen, WHITE, rect, 2, border_radius=10)
    label = ui_font.render(text, True, BLACK)
    screen.blit(label, label.get_rect(center=rect.center))


def draw_slot(rect, label, accent=GOLD):
    pygame.draw.rect(screen, (24, 92, 62), rect, border_radius=12)
    pygame.draw.rect(screen, (102, 173, 126), rect, 2, border_radius=12)
    pygame.draw.rect(screen, (20, 76, 52), rect.inflate(-12, -12), 1, border_radius=10)
    text = small_font.render(label, True, accent)
    screen.blit(text, text.get_rect(center=rect.center))


def draw_card_back(rect):
    pygame.draw.rect(screen, CARD_SHADOW, rect.move(0, 4), border_radius=12)
    pygame.draw.rect(screen, BLUE, rect, border_radius=12)
    pygame.draw.rect(screen, CARD_EDGE, rect, 2, border_radius=12)

    inner = rect.inflate(-14, -14)
    pygame.draw.rect(screen, (28, 58, 112), inner, border_radius=8)
    pygame.draw.rect(screen, GOLD, inner, 2, border_radius=8)

    cx, cy = rect.center
    pygame.draw.circle(screen, GOLD, (cx, cy), 30, 2)
    pygame.draw.circle(screen, WHITE, (cx, cy), 16, 1)
    pygame.draw.line(screen, GOLD, (cx - 28, cy), (cx + 28, cy), 2)
    pygame.draw.line(screen, GOLD, (cx, cy - 28), (cx, cy + 28), 2)


def draw_card_front(card, rect, lifted=False):
    shadow = rect.move(0, 7 if lifted else 4)
    pygame.draw.rect(screen, CARD_SHADOW, shadow, border_radius=12)
    pygame.draw.rect(screen, CARD, rect, border_radius=12)
    pygame.draw.rect(screen, CARD_EDGE, rect, 2, border_radius=12)

    color = card.color
    label = card.label
    symbol = SUIT_SYMBOLS[card.suit]

    corner = small_card_font.render(label, True, color)
    suit = small_card_font.render(symbol, True, color)
    screen.blit(corner, (rect.x + 9, rect.y + 8))
    screen.blit(suit, (rect.x + 11, rect.y + 29))

    big_symbol = card_font.render(symbol, True, color)
    screen.blit(big_symbol, big_symbol.get_rect(center=(rect.centerx, rect.centery - 4)))

    bottom_label = small_card_font.render(label, True, color)
    bottom_suit = small_card_font.render(symbol, True, color)
    rotated_label = pygame.transform.rotate(bottom_label, 180)
    rotated_suit = pygame.transform.rotate(bottom_suit, 180)
    screen.blit(rotated_suit, (rect.right - 26, rect.bottom - 48))
    screen.blit(rotated_label, (rect.right - 29, rect.bottom - 27))


def draw_card(card, rect, lifted=False):
    card.rect = pygame.Rect(rect)
    if card.face_up:
        draw_card_front(card, card.rect, lifted)
    else:
        draw_card_back(card.rect)


def assign_static_positions(state):
    stock_rect = pygame.Rect(*STOCK_POS, CARD_W, CARD_H)
    for card in state["stock"]:
        card.rect = stock_rect

    waste_rect = pygame.Rect(*WASTE_POS, CARD_W, CARD_H)
    for card in state["waste"]:
        card.rect = waste_rect

    for i, pile in enumerate(state["foundations"]):
        rect = pygame.Rect(*foundation_pos(i), CARD_W, CARD_H)
        for card in pile:
            card.rect = rect

    for col, pile in enumerate(state["tableau"]):
        y = TABLEAU_Y
        x = tableau_x(col)
        for card in pile:
            card.rect = pygame.Rect(x, y, CARD_W, CARD_H)
            y += TABLEAU_STEP_FACE_UP if card.face_up else TABLEAU_STEP_FACE_DOWN


def draw_piles(state):
    stock_rect = pygame.Rect(*STOCK_POS, CARD_W, CARD_H)
    waste_rect = pygame.Rect(*WASTE_POS, CARD_W, CARD_H)

    draw_slot(stock_rect, "STOCK")
    draw_slot(waste_rect, "WASTE")
    for i, suit in enumerate(["♠", "♥", "♦", "♣"]):
        color = RED if suit in ("♥", "♦") else BLACK
        draw_slot(pygame.Rect(*foundation_pos(i), CARD_W, CARD_H), suit, color)

    if state["stock"]:
        draw_card_back(stock_rect)
    if state["waste"]:
        draw_card(state["waste"][-1], waste_rect)

    for i, pile in enumerate(state["foundations"]):
        if pile:
            draw_card(pile[-1], pygame.Rect(*foundation_pos(i), CARD_W, CARD_H))

    for col, pile in enumerate(state["tableau"]):
        x = tableau_x(col)
        empty_rect = pygame.Rect(x, TABLEAU_Y, CARD_W, CARD_H)
        if not pile:
            draw_slot(empty_rect, "K")
            continue

        y = TABLEAU_Y
        for card in pile:
            if state["drag"] and card in state["drag"].cards:
                y += TABLEAU_STEP_FACE_UP if card.face_up else TABLEAU_STEP_FACE_DOWN
                continue
            draw_card(card, pygame.Rect(x, y, CARD_W, CARD_H))
            y += TABLEAU_STEP_FACE_UP if card.face_up else TABLEAU_STEP_FACE_DOWN


def draw_dragged_cards(drag):
    if not drag:
        return

    for i, card in enumerate(drag.cards):
        draw_card(card, pygame.Rect(drag.x, drag.y + i * TABLEAU_STEP_FACE_UP, CARD_W, CARD_H), True)


def can_place_on_tableau(cards, target_pile):
    moving = cards[0]
    if not target_pile:
        return moving.rank == 13

    target = target_pile[-1]
    return target.face_up and moving.rank == target.rank - 1 and card_is_red(moving) != card_is_red(target)


def can_place_on_foundation(card, foundation):
    if not foundation:
        return card.rank == 1
    top = foundation[-1]
    return card.suit == top.suit and card.rank == top.rank + 1


def flip_exposed_tableau_card(state, source_index):
    if source_index is None:
        return

    pile = state["tableau"][source_index]
    if pile and not pile[-1].face_up:
        pile[-1].face_up = True


def remove_from_source(state, drag):
    if drag.source_type == "waste":
        state["waste"].pop()
    elif drag.source_type == "foundation":
        state["foundations"][drag.source_index].pop()
    elif drag.source_type == "tableau":
        pile = state["tableau"][drag.source_index]
        del pile[-len(drag.cards):]


def return_drag_to_source(state, drag):
    if drag.source_type == "waste":
        state["waste"].append(drag.cards[0])
    elif drag.source_type == "foundation":
        state["foundations"][drag.source_index].extend(drag.cards)
    elif drag.source_type == "tableau":
        state["tableau"][drag.source_index].extend(drag.cards)


def complete_move(state, drag, target_type, target_index):
    moved = False

    if target_type == "tableau":
        state["tableau"][target_index].extend(drag.cards)
        moved = True
    elif target_type == "foundation":
        state["foundations"][target_index].append(drag.cards[0])
        moved = True

    if moved:
        flip_exposed_tableau_card(state, drag.source_index if drag.source_type == "tableau" else None)
        state["moves"] += 1

    return moved


def find_tableau_drop(state, drag):
    mouse_rect = pygame.Rect(drag.x, drag.y, CARD_W, CARD_H)
    best_index = None
    best_overlap = 0

    for i, pile in enumerate(state["tableau"]):
        if not can_place_on_tableau(drag.cards, pile):
            continue

        if pile:
            target_rect = pile[-1].rect
        else:
            target_rect = pygame.Rect(tableau_x(i), TABLEAU_Y, CARD_W, CARD_H)

        overlap = mouse_rect.clip(target_rect).w * mouse_rect.clip(target_rect).h
        if overlap > best_overlap or target_rect.collidepoint(mouse_rect.center):
            best_overlap = overlap
            best_index = i

    return best_index


def find_foundation_drop(state, drag):
    if len(drag.cards) != 1:
        return None
    if drag.source_type == "foundation":
        return None

    card = drag.cards[0]
    for i, foundation in enumerate(state["foundations"]):
        rect = pygame.Rect(*foundation_pos(i), CARD_W, CARD_H)
        if rect.colliderect(pygame.Rect(drag.x, drag.y, CARD_W, CARD_H)) and can_place_on_foundation(card, foundation):
            return i

    return None


def end_drag(state):
    drag = state["drag"]
    if not drag:
        return

    target_foundation = find_foundation_drop(state, drag)
    if target_foundation is not None:
        complete_move(state, drag, "foundation", target_foundation)
    else:
        target_tableau = find_tableau_drop(state, drag)
        if target_tableau is not None:
            complete_move(state, drag, "tableau", target_tableau)
        else:
            return_drag_to_source(state, drag)
            set_message(state, "Illegal move")

    state["drag"] = None
    assign_static_positions(state)
    check_win(state)


def top_card_under_mouse(state, pos):
    if state["waste"] and state["waste"][-1].rect.collidepoint(pos):
        return {
            "cards": [state["waste"][-1]],
            "source_type": "waste",
            "source_index": None,
            "card": state["waste"][-1],
        }

    for i, pile in enumerate(state["foundations"]):
        if pile and pile[-1].rect.collidepoint(pos):
            return {
                "cards": [pile[-1]],
                "source_type": "foundation",
                "source_index": i,
                "card": pile[-1],
            }

    for col in range(6, -1, -1):
        pile = state["tableau"][col]
        for idx in range(len(pile) - 1, -1, -1):
            card = pile[idx]
            if card.face_up and card.rect.collidepoint(pos):
                return {
                    "cards": pile[idx:],
                    "source_type": "tableau",
                    "source_index": col,
                    "card": card,
                }

    return None


def start_drag(state, hit, pos):
    cards = hit["cards"]
    drag = DragState(cards[:], hit["source_type"], hit["source_index"], (pos[0] - cards[0].rect.x, pos[1] - cards[0].rect.y), cards[0].rect.topleft)
    remove_from_source(state, drag)
    drag.x = pos[0] - drag.grab_offset[0]
    drag.y = pos[1] - drag.grab_offset[1]
    state["drag"] = drag


def draw_from_stock(state):
    if state["stock"]:
        card = state["stock"].pop()
        card.face_up = True
        state["waste"].append(card)
        state["moves"] += 1
        return

    if state["waste"]:
        while state["waste"]:
            card = state["waste"].pop()
            card.face_up = False
            state["stock"].append(card)
        state["moves"] += 1


def auto_move_to_foundation(state, hit):
    if len(hit["cards"]) != 1:
        return False
    if hit["source_type"] == "foundation":
        return False

    card = hit["cards"][0]
    for i, foundation in enumerate(state["foundations"]):
        if can_place_on_foundation(card, foundation):
            drag = DragState([card], hit["source_type"], hit["source_index"], (0, 0), card.rect.topleft)
            remove_from_source(state, drag)
            complete_move(state, drag, "foundation", i)
            assign_static_positions(state)
            check_win(state)
            return True

    set_message(state, "No foundation move")
    return False


def check_win(state):
    state["won"] = all(len(pile) == 13 for pile in state["foundations"])
    if state["won"]:
        set_message(state, "You won!", 999)


def draw_status(state):
    moves = small_font.render(f"Moves: {state['moves']}", True, WHITE)
    screen.blit(moves, (WIDTH - 178, 76))

    if state["message"] and time.time() < state["message_until"]:
        msg = ui_font.render(state["message"], True, GOLD)
        screen.blit(msg, msg.get_rect(center=(WIDTH // 2, 52)))


def draw_win_overlay(state, mouse):
    if not state["won"]:
        return

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill(WIN_OVERLAY)
    screen.blit(overlay, (0, 0))

    box = pygame.Rect(WIDTH // 2 - 210, HEIGHT // 2 - 110, 420, 220)
    pygame.draw.rect(screen, (245, 235, 190), box, border_radius=18)
    pygame.draw.rect(screen, GOLD, box, 4, border_radius=18)
    title = title_font.render("You won!", True, BLACK)
    screen.blit(title, title.get_rect(center=(box.centerx, box.y + 70)))
    subtitle = ui_font.render(f"Completed in {state['moves']} moves", True, BLACK)
    screen.blit(subtitle, subtitle.get_rect(center=(box.centerx, box.y + 114)))
    draw_button(pygame.Rect(box.centerx - 72, box.y + 150, 144, 42), "New Game", mouse)


def handle_mouse_down(state, event):
    pos = event.pos

    if NEW_GAME_RECT.collidepoint(pos):
        return new_game()

    if state["won"]:
        win_new_rect = pygame.Rect(WIDTH // 2 - 72, HEIGHT // 2 + 40, 144, 42)
        if win_new_rect.collidepoint(pos):
            return new_game()
        return state

    assign_static_positions(state)

    stock_rect = pygame.Rect(*STOCK_POS, CARD_W, CARD_H)
    if stock_rect.collidepoint(pos):
        draw_from_stock(state)
        assign_static_positions(state)
        return state

    hit = top_card_under_mouse(state, pos)
    if not hit:
        return state

    now = time.time()
    is_double_click = hit["card"] is state["last_click_card"] and now - state["last_click_time"] <= 0.35
    state["last_click_card"] = hit["card"]
    state["last_click_time"] = now

    if is_double_click:
        auto_move_to_foundation(state, hit)
    else:
        start_drag(state, hit, pos)

    return state


def draw_game(state):
    mouse = pygame.mouse.get_pos()
    draw_background()
    draw_button(NEW_GAME_RECT, "New Game", mouse)
    assign_static_positions(state)
    draw_piles(state)
    draw_dragged_cards(state["drag"])
    draw_status(state)
    draw_win_overlay(state, mouse)
    pygame.display.flip()


def main():
    state = new_game()

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_n:
                    state = new_game()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                state = handle_mouse_down(state, event)

            if event.type == pygame.MOUSEMOTION and state["drag"]:
                state["drag"].x = event.pos[0] - state["drag"].grab_offset[0]
                state["drag"].y = event.pos[1] - state["drag"].grab_offset[1]

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                end_drag(state)

        draw_game(state)


if __name__ == "__main__":
    main()
