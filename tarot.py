import pygame
import random
import sys
import math
import textwrap
from datetime import datetime
from pathlib import Path

pygame.init()

WIDTH, HEIGHT = 1280, 820
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tarot Mystic Ultra")

clock = pygame.time.Clock()
FPS = 60

BLACK = (10, 8, 18)
DARK = (25, 14, 44)
PURPLE = (80, 36, 130)
VIOLET = (115, 58, 180)
GOLD = (235, 190, 85)
WHITE = (245, 235, 215)
GRAY = (120, 115, 130)
RED = (190, 55, 75)
BLUE = (65, 95, 180)
GREEN = (70, 150, 105)
ORANGE = (235, 130, 50)

title_font = pygame.font.SysFont("georgia", 54, bold=True)
big_font = pygame.font.SysFont("georgia", 32, bold=True)
font = pygame.font.SysFont("georgia", 23)
small_font = pygame.font.SysFont("georgia", 17)
tiny_font = pygame.font.SysFont("georgia", 14)

CARD_W, CARD_H = 118, 190

MAJOR = [
    ("The Fool", "începuturi, risc, libertate"),
    ("The Magician", "voință, putere, acțiune"),
    ("The High Priestess", "intuiție, secrete, răbdare"),
    ("The Empress", "creativitate, abundență, grijă"),
    ("The Emperor", "ordine, autoritate, stabilitate"),
    ("The Hierophant", "tradiție, învățare, reguli"),
    ("The Lovers", "alegeri, iubire, conexiune"),
    ("The Chariot", "victorie, control, ambiție"),
    ("Strength", "curaj, autocontrol, blândețe"),
    ("The Hermit", "reflecție, singurătate, adevăr"),
    ("Wheel of Fortune", "destin, schimbare, noroc"),
    ("Justice", "adevăr, echilibru, consecințe"),
    ("The Hanged Man", "pauză, sacrificiu, perspectivă"),
    ("Death", "transformare, final, renaștere"),
    ("Temperance", "echilibru, vindecare, răbdare"),
    ("The Devil", "atașamente, tentații, frică"),
    ("The Tower", "ruptură, șoc, revelație"),
    ("The Star", "speranță, inspirație, liniște"),
    ("The Moon", "confuzie, vise, subconștient"),
    ("The Sun", "claritate, bucurie, succes"),
    ("Judgement", "trezire, decizie, renaștere"),
    ("The World", "împlinire, finalizare, succes")
]

SUITS = {
    "Cups": "emoții, relații, iubire",
    "Wands": "energie, dorință, inițiativă",
    "Swords": "gânduri, conflicte, decizii",
    "Pentacles": "bani, muncă, stabilitate"
}

RANKS = [
    ("Ace", "început puternic"),
    ("Two", "alegere sau echilibru"),
    ("Three", "creștere și colaborare"),
    ("Four", "stabilitate sau blocaj"),
    ("Five", "tensiune și schimbare"),
    ("Six", "armonie și progres"),
    ("Seven", "test, răbdare, strategie"),
    ("Eight", "mișcare, muncă, evoluție"),
    ("Nine", "rezultat aproape complet"),
    ("Ten", "final de ciclu"),
    ("Page", "mesaj, curiozitate, început"),
    ("Knight", "acțiune, impuls, mișcare"),
    ("Queen", "maturitate, grijă, intuiție"),
    ("King", "control, experiență, autoritate")
]

ORACLE = [
    ("Cosmic Gate", "o ușă nouă se deschide"),
    ("Silent Mirror", "adevărul se vede în liniște"),
    ("Golden Path", "drumul potrivit se clarifică"),
    ("Hidden Flame", "dorință ascunsă, energie interioară"),
    ("Silver Moon", "intuiție, vise, sensibilitate"),
    ("Ancient Star", "protecție, speranță, ghidare"),
    ("Broken Crown", "renunțare la ego sau control"),
    ("Crystal Heart", "vindecare emoțională"),
    ("Shadow Key", "ceva ascuns trebuie înțeles"),
    ("Phoenix Soul", "renaștere după o etapă grea"),
    ("Ocean Voice", "emoțiile cer ascultare"),
    ("Mystic Wind", "schimbare rapidă, mesaj neașteptat")
]

SPREADS = {
    "1 Carte": ["Mesaj principal"],
    "3 Cărți": ["Trecut", "Prezent", "Viitor"],
    "5 Cărți": ["Situație", "Provocare", "Sfat", "Influență ascunsă", "Rezultat posibil"],
    "7 Cărți": ["Tu", "Ce simți", "Ce gândești", "Obstacol", "Ajutor", "Avertisment", "Rezultat"],
    "10 Cărți": ["Tu", "Problema", "Trecut apropiat", "Prezent", "Viitor apropiat", "Frica", "Speranța", "Mediul", "Sfatul", "Rezultat final"]
}


def zodiac_from_date(date_text):
    try:
        day, month, year = map(int, date_text.split("."))
    except:
        return ""

    signs = [
        ("Capricorn", (1, 1), (1, 19)),
        ("Vărsător", (1, 20), (2, 18)),
        ("Pești", (2, 19), (3, 20)),
        ("Berbec", (3, 21), (4, 19)),
        ("Taur", (4, 20), (5, 20)),
        ("Gemeni", (5, 21), (6, 20)),
        ("Rac", (6, 21), (7, 22)),
        ("Leu", (7, 23), (8, 22)),
        ("Fecioară", (8, 23), (9, 22)),
        ("Balanță", (9, 23), (10, 22)),
        ("Scorpion", (10, 23), (11, 21)),
        ("Săgetător", (11, 22), (12, 21)),
        ("Capricorn", (12, 22), (12, 31))
    ]

    for sign, start, end in signs:
        sm, sd = start
        em, ed = end
        if (month == sm and day >= sd) or (month == em and day <= ed):
            return sign

    return ""


def build_deck():
    deck = []

    for name, meaning in MAJOR:
        deck.append({
            "name": name,
            "type": "Arcana Majoră",
            "meaning": meaning
        })

    for suit, suit_meaning in SUITS.items():
        for rank, rank_meaning in RANKS:
            deck.append({
                "name": f"{rank} of {suit}",
                "type": suit,
                "meaning": f"{rank_meaning}; {suit_meaning}"
            })

    for name, meaning in ORACLE:
        deck.append({
            "name": name,
            "type": "Oracle Bonus",
            "meaning": meaning
        })

    return deck


DECK = build_deck()


class Button:
    def __init__(self, text, rect):
        self.text = text
        self.rect = pygame.Rect(rect)

    def draw(self, mouse, selected=False):
        hover = self.rect.collidepoint(mouse)
        color = GOLD if hover else PURPLE
        if selected:
            color = VIOLET

        pygame.draw.rect(screen, color, self.rect, border_radius=14)
        pygame.draw.rect(screen, GOLD if selected else WHITE, self.rect, 2, border_radius=14)

        txt = font.render(self.text, True, BLACK if hover else WHITE)
        screen.blit(txt, txt.get_rect(center=self.rect.center))

    def clicked(self, pos):
        return self.rect.collidepoint(pos)


class InputBox:
    def __init__(self, label, rect, placeholder):
        self.label = label
        self.rect = pygame.Rect(rect)
        self.placeholder = placeholder
        self.text = ""
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False
            elif len(self.text) < 120:
                self.text += event.unicode

    def draw(self):
        lbl = small_font.render(self.label, True, GOLD)
        screen.blit(lbl, (self.rect.x, self.rect.y - 24))

        pygame.draw.rect(screen, DARK, self.rect, border_radius=12)
        pygame.draw.rect(screen, GOLD if self.active else WHITE, self.rect, 2, border_radius=12)

        shown = self.text if self.text else self.placeholder
        color = WHITE if self.text else GRAY

        txt = small_font.render(shown, True, color)
        screen.blit(txt, (self.rect.x + 12, self.rect.y + 14))


class TarotCard:
    def __init__(self, data, x, y):
        self.data = data
        self.x = x
        self.y = y
        self.reversed = random.choice([False, False, True])
        self.target = False
        self.revealed = False
        self.flip = 0
        self.float_offset = random.random() * 6

    def rect(self):
        return pygame.Rect(self.x, self.y, CARD_W, CARD_H)

    def update(self):
        if self.target and self.flip < 1:
            self.flip += 0.055
            if self.flip >= 1:
                self.flip = 1
                self.revealed = True

    def draw_back(self, x, y, w):
        pygame.draw.rect(screen, DARK, (x, y, w, CARD_H), border_radius=16)
        pygame.draw.rect(screen, GOLD, (x, y, w, CARD_H), 3, border_radius=16)

        cx = x + w // 2
        cy = y + CARD_H // 2

        pygame.draw.circle(screen, GOLD, (cx, cy), max(4, w // 4), 2)
        pygame.draw.circle(screen, VIOLET, (cx, cy), max(3, w // 6), 2)
        pygame.draw.line(screen, GOLD, (cx, y + 25), (cx, y + CARD_H - 25), 2)
        pygame.draw.line(screen, GOLD, (x + 15, cy), (x + w - 15, cy), 2)

        for i in range(8):
            angle = i * math.pi / 4
            px = cx + int(math.cos(angle) * max(5, w // 3))
            py = cy + int(math.sin(angle) * 45)
            pygame.draw.circle(screen, GOLD, (px, py), 2)

        txt = tiny_font.render("MYSTIC", True, GOLD)
        screen.blit(txt, txt.get_rect(center=(cx, y + CARD_H - 22)))

    def draw_front(self, x, y, w):
        pygame.draw.rect(screen, WHITE, (x, y, w, CARD_H), border_radius=16)
        pygame.draw.rect(screen, GOLD, (x, y, w, CARD_H), 3, border_radius=16)

        cx = x + w // 2
        cy = y + CARD_H // 2 + 8

        name = self.data["name"]
        if self.reversed:
            name += " Rx"

        lines = textwrap.wrap(name, width=14)
        yy = y + 16
        for line in lines[:2]:
            txt = tiny_font.render(line, True, BLACK)
            screen.blit(txt, txt.get_rect(center=(cx, yy)))
            yy += 16

        self.draw_symbol(cx, cy)

        arc = tiny_font.render(self.data["type"], True, BLACK)
        screen.blit(arc, arc.get_rect(center=(cx, y + CARD_H - 18)))

    def draw_symbol(self, cx, cy):
        value = sum(ord(c) for c in self.data["name"]) % 8

        if value == 0:
            pygame.draw.circle(screen, ORANGE, (cx, cy), 30)
            pygame.draw.circle(screen, GOLD, (cx, cy), 43, 3)
        elif value == 1:
            pygame.draw.polygon(screen, BLUE, [(cx, cy - 42), (cx - 34, cy + 32), (cx + 34, cy + 32)])
            pygame.draw.circle(screen, GOLD, (cx, cy), 13)
        elif value == 2:
            pygame.draw.circle(screen, BLUE, (cx - 13, cy), 28)
            pygame.draw.circle(screen, WHITE, (cx - 1, cy - 3), 28)
            pygame.draw.circle(screen, GOLD, (cx + 32, cy - 33), 5)
        elif value == 3:
            pygame.draw.rect(screen, GREEN, (cx - 32, cy - 32, 64, 64), border_radius=10)
            pygame.draw.circle(screen, GOLD, (cx, cy), 18)
        elif value == 4:
            pygame.draw.polygon(screen, RED, [(cx, cy - 42), (cx - 35, cy + 35), (cx + 35, cy + 35)])
            pygame.draw.line(screen, GOLD, (cx, cy - 42), (cx, cy + 35), 3)
        elif value == 5:
            pygame.draw.circle(screen, PURPLE, (cx, cy), 36)
            pygame.draw.circle(screen, GOLD, (cx, cy), 23, 3)
            pygame.draw.circle(screen, WHITE, (cx, cy), 7)
        elif value == 6:
            pygame.draw.polygon(screen, GOLD, [
                (cx, cy - 42), (cx + 12, cy - 10), (cx + 44, cy - 10),
                (cx + 18, cy + 8), (cx + 28, cy + 40),
                (cx, cy + 20), (cx - 28, cy + 40),
                (cx - 18, cy + 8), (cx - 44, cy - 10),
                (cx - 12, cy - 10)
            ])
        else:
            pygame.draw.arc(screen, PURPLE, (cx - 38, cy - 38, 76, 76), 0, math.pi * 1.6, 5)
            pygame.draw.circle(screen, GOLD, (cx, cy), 18)

        if self.reversed:
            txt = tiny_font.render("inversată", True, RED)
            screen.blit(txt, txt.get_rect(center=(cx, cy + 60)))

    def draw(self):
        y = self.y + int(math.sin(pygame.time.get_ticks() / 500 + self.float_offset) * 2)
        scale = abs(math.cos(self.flip * math.pi))
        w = max(6, int(CARD_W * scale))
        x = self.x + (CARD_W - w) // 2

        if self.flip < 0.5:
            self.draw_back(x, y, w)
        else:
            self.draw_front(x, y, w)


def draw_background():
    screen.fill(BLACK)

    t = pygame.time.get_ticks() / 1000

    for i in range(150):
        x = (i * 97 + int(t * 10)) % WIDTH
        y = (i * 53) % HEIGHT
        r = 1 if i % 4 else 2
        pygame.draw.circle(screen, (105, 82, 150), (x, y), r)

    pygame.draw.circle(screen, DARK, (WIDTH // 2, HEIGHT // 2), 410, 2)
    pygame.draw.circle(screen, PURPLE, (WIDTH // 2, HEIGHT // 2), 310, 2)
    pygame.draw.circle(screen, VIOLET, (WIDTH // 2, HEIGHT // 2), 210, 1)


def draw_panel(rect):
    pygame.draw.rect(screen, (20, 12, 35), rect, border_radius=18)
    pygame.draw.rect(screen, GOLD, rect, 2, border_radius=18)


def make_wrapped_lines(text, max_width, font_obj):
    words = text.split()
    lines = []
    line = ""

    for word in words:
        test = line + word + " "
        if font_obj.size(test)[0] <= max_width:
            line = test
        else:
            lines.append(line)
            line = word + " "

    if line:
        lines.append(line)

    return lines


def zodiac_energy(sign):
    data = {
        "Berbec": "energie directă, curaj și impuls",
        "Taur": "stabilitate, răbdare și nevoie de siguranță",
        "Gemeni": "comunicare, curiozitate și schimbare",
        "Rac": "emoție, familie și protecție",
        "Leu": "încredere, expresivitate și dorință de recunoaștere",
        "Fecioară": "analiză, ordine și perfecționare",
        "Balanță": "echilibru, relații și decizii",
        "Scorpion": "intensitate, transformare și adevăr ascuns",
        "Săgetător": "libertate, direcție și expansiune",
        "Capricorn": "ambiție, disciplină și construcție pe termen lung",
        "Vărsător": "originalitate, independență și idei noi",
        "Pești": "intuiție, sensibilitate și imaginație"
    }
    return data.get(sign, "energie personală greu de definit")


def interpretation(card, position, profile):
    name = profile["name"] if profile["name"] else "tu"
    question = profile["question"] if profile["question"] else "situația ta"
    sign = profile["zodiac"] if profile["zodiac"] else "zodie necunoscută"

    reverse_text = (
        "Fiind inversată, cartea arată blocaj, întârziere, teamă sau o energie folosită greșit."
        if card.reversed else
        "Fiind dreaptă, cartea arată o energie clară, activă și mai ușor de folosit."
    )

    extra = random.choice([
        "Mesajul ei sugerează să nu te grăbești și să observi semnele din jur.",
        "Citirea indică o schimbare importantă dacă alegi să acționezi conștient.",
        "Cartea te împinge să fii sincer cu tine și să nu ignori intuiția.",
        "Energia acestei poziții arată că răspunsul vine prin claritate și răbdare."
    ])

    return (
        f"{position}: Pentru {name}, în legătură cu «{question}», cartea {card.data['name']} "
        f"aduce tema: {card.data['meaning']}. {reverse_text} "
        f"Zodia {sign} adaugă în citire: {zodiac_energy(sign)}. {extra}"
    )


def save_reading(profile, spread_name, positions, cards, interpretations):
    folder = Path(__file__).resolve().parent / "saved_readings"
    folder.mkdir(exist_ok=True)

    raw_name = profile["name"].strip() if profile["name"] else "reading"
    safe_name = "".join(ch if ch.isalnum() else "_" for ch in raw_name).strip("_") or "reading"
    safe_name = safe_name[:28]
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}.txt"
    path = folder / filename

    lines = [
        "Tarot Mystic Ultra",
        f"Salvat: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        f"Etalare: {spread_name}",
        f"Nume: {profile['name'] or 'Fără nume'}",
        f"Data nașterii: {profile['date'] or 'dată necunoscută'}",
        f"Zodie: {profile['zodiac'] or 'zodie necunoscută'}",
        f"Întrebare: {profile['question'] or 'citire generală'}",
        "",
    ]

    for i, card in enumerate(cards):
        orientation = "inversată" if card.reversed else "dreaptă"
        lines.append(f"{i + 1}. {positions[i]} - {card.data['name']} ({orientation})")
        lines.append(interpretations[i])
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def start_screen():
    name_box = InputBox("Nume", (120, 245, 330, 50), "ex: Rareș")
    date_box = InputBox("Data nașterii", (475, 245, 330, 50), "ex: 20.10.2006")
    zodiac_box = InputBox("Zodie", (830, 245, 330, 50), "se completează automat sau scrii tu")
    question_box = InputBox("Subiect / întrebare", (120, 345, 1040, 55), "ex: Ce urmează în dragoste / facultate / bani?")

    spread_buttons = []
    x = 120
    y = 455
    for name in SPREADS:
        spread_buttons.append(Button(name, (x, y, 190, 52)))
        x += 205

    selected_spread = "5 Cărți"

    start_button = Button("Începe citirea", (420, 575, 250, 58))
    quit_button = Button("Ieșire", (700, 575, 180, 58))

    while True:
        clock.tick(FPS)
        mouse = pygame.mouse.get_pos()
        draw_background()

        title = title_font.render("Tarot Mystic Ultra", True, GOLD)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 95)))

        subtitle = font.render("Introdu profilul, întrebarea și alege etalarea.", True, WHITE)
        screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 155)))

        draw_panel((80, 205, 1120, 500))

        for box in [name_box, date_box, zodiac_box, question_box]:
            box.draw()

        auto_sign = zodiac_from_date(date_box.text)
        if auto_sign and not zodiac_box.text:
            hint = small_font.render(f"Zodie detectată: {auto_sign}", True, GOLD)
            screen.blit(hint, (830, 305))

        spread_label = small_font.render("Alege etalarea:", True, GOLD)
        screen.blit(spread_label, (120, 425))

        for btn in spread_buttons:
            btn.draw(mouse, btn.text == selected_spread)

        start_button.draw(mouse)
        quit_button.draw(mouse)

        info = small_font.render("Pachet: 78 cărți Tarot + 12 cărți Oracle bonus = 90 de cărți.", True, WHITE)
        screen.blit(info, info.get_rect(center=(WIDTH // 2, 745)))

        for event in pygame.event.get():
            for box in [name_box, date_box, zodiac_box, question_box]:
                box.handle_event(event)

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                for btn in spread_buttons:
                    if btn.clicked(event.pos):
                        selected_spread = btn.text

                if start_button.clicked(event.pos):
                    final_zodiac = zodiac_box.text.strip()
                    if not final_zodiac:
                        final_zodiac = zodiac_from_date(date_box.text)

                    profile = {
                        "name": name_box.text.strip(),
                        "date": date_box.text.strip(),
                        "zodiac": final_zodiac,
                        "question": question_box.text.strip()
                    }

                    reading_screen(profile, selected_spread)

                if quit_button.clicked(event.pos):
                    pygame.quit()
                    sys.exit()

        pygame.display.flip()


def reading_screen_legacy(profile, spread_name):
    positions = SPREADS[spread_name]
    number = len(positions)

    chosen = random.sample(DECK, number)
    cards = []

    if number <= 5:
        total = number * CARD_W + (number - 1) * 38
        start_x = WIDTH // 2 - total // 2
        for i in range(number):
            cards.append(TarotCard(chosen[i], start_x + i * (CARD_W + 38), 190))
    else:
        cols = 5
        start_x = WIDTH // 2 - (cols * CARD_W + 4 * 36) // 2
        start_y = 165
        for i in range(number):
            row = i // cols
            col = i % cols
            cards.append(TarotCard(chosen[i], start_x + col * (CARD_W + 36), start_y + row * 215))

    revealed = 0
    show_results = False
    scroll = 0

    menu_button = Button("Meniu", (790, 745, 150, 45))
    restart_button = Button("Altă citire", (970, 745, 190, 45))

    while True:
        clock.tick(FPS)
        mouse = pygame.mouse.get_pos()
        draw_background()

        title = big_font.render(f"Etalare: {spread_name}", True, GOLD)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 40)))

        profile_text = f"{profile['name'] or 'Fără nume'} | {profile['date'] or 'dată necunoscută'} | {profile['zodiac'] or 'zodie necunoscută'}"
        p = small_font.render(profile_text, True, WHITE)
        screen.blit(p, p.get_rect(center=(WIDTH // 2, 75)))

        q = small_font.render(f"Întrebare: {profile['question'] or 'citire generală'}", True, WHITE)
        screen.blit(q, q.get_rect(center=(WIDTH // 2, 102)))

        instr = tiny_font.render("Click pe fiecare carte pentru a o întoarce. ESC = meniu. Scroll = vezi tot textul.", True, GRAY)
        screen.blit(instr, instr.get_rect(center=(WIDTH // 2, 125)))

        for i, card in enumerate(cards):
            label = tiny_font.render(positions[i], True, GOLD)
            screen.blit(label, label.get_rect(center=(card.x + CARD_W // 2, card.y - 18)))
            card.update()
            card.draw()

        if revealed == number:
            show_results = True

        if show_results:
            panel_rect = pygame.Rect(50, 595, 1180, 205)
            draw_panel(panel_rect)

            content_surface = pygame.Surface((1140, 1000), pygame.SRCALPHA)
            y = 0

            for i, card in enumerate(cards):
                card_title = card.data["name"] + (" inversată" if card.reversed else "")
                head = tiny_font.render(f"{positions[i]} — {card_title}", True, GOLD)
                content_surface.blit(head, (0, y))
                y += 18

                text = interpretation(card, positions[i], profile)
                lines = make_wrapped_lines(text, 1080, tiny_font)

                for line in lines:
                    line_img = tiny_font.render(line, True, WHITE)
                    content_surface.blit(line_img, (0, y))
                    y += 17

                y += 8

            max_scroll = max(0, y - 145)
            scroll = max(0, min(scroll, max_scroll))

            visible_area = pygame.Rect(0, scroll, 1140, 145)
            screen.blit(content_surface, (75, 615), visible_area)

            if max_scroll > 0:
                bar_x = 1210
                bar_y = 615
                bar_h = 145
                pygame.draw.rect(screen, GRAY, (bar_x, bar_y, 6, bar_h), border_radius=3)

                handle_h = max(25, int(bar_h * (145 / y)))
                handle_y = bar_y + int((scroll / max_scroll) * (bar_h - handle_h))
                pygame.draw.rect(screen, GOLD, (bar_x, handle_y, 6, handle_h), border_radius=3)

            hint = tiny_font.render("Folosește rotița mouse-ului ca să vezi toată citirea.", True, GRAY)
            screen.blit(hint, (75, 770))

            menu_button.draw(mouse)
            restart_button.draw(mouse)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEWHEEL and show_results:
                scroll -= event.y * 35

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    start_screen()

                if show_results:
                    if event.key == pygame.K_DOWN:
                        scroll += 35
                    elif event.key == pygame.K_UP:
                        scroll -= 35

            if event.type == pygame.MOUSEBUTTONDOWN:
                for card in cards:
                    if card.rect().collidepoint(event.pos) and not card.target:
                        card.target = True
                        revealed += 1

                if show_results:
                    if menu_button.clicked(event.pos):
                        start_screen()

                    if restart_button.clicked(event.pos):
                        reading_screen(profile, spread_name)

        pygame.display.flip()


def reading_screen(profile, spread_name):
    positions = SPREADS[spread_name]
    number = len(positions)

    chosen = random.sample(DECK, number)
    cards = []

    if number <= 5:
        total = number * CARD_W + (number - 1) * 38
        start_x = WIDTH // 2 - total // 2
        for i in range(number):
            cards.append(TarotCard(chosen[i], start_x + i * (CARD_W + 38), 190))
    else:
        cols = 5
        start_x = WIDTH // 2 - (cols * CARD_W + 4 * 36) // 2
        start_y = 165
        for i in range(number):
            row = i // cols
            col = i % cols
            cards.append(TarotCard(chosen[i], start_x + col * (CARD_W + 36), start_y + row * 215))

    interpretations = [interpretation(cards[i], positions[i], profile) for i in range(number)]
    revealed = 0
    show_results = False
    selected_index = 0
    save_status = ""
    save_status_until = 0

    prev_button = Button("<", (70, 745, 58, 45))
    next_button = Button(">", (142, 745, 58, 45))
    save_button = Button("Salvează", (570, 745, 180, 45))
    menu_button = Button("Meniu", (790, 745, 150, 45))
    restart_button = Button("Altă citire", (970, 745, 190, 45))

    while True:
        clock.tick(FPS)
        mouse = pygame.mouse.get_pos()
        draw_background()

        title = big_font.render(f"Etalare: {spread_name}", True, GOLD)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 40)))

        profile_text = f"{profile['name'] or 'Fără nume'} | {profile['date'] or 'dată necunoscută'} | {profile['zodiac'] or 'zodie necunoscută'}"
        p = small_font.render(profile_text, True, WHITE)
        screen.blit(p, p.get_rect(center=(WIDTH // 2, 75)))

        q = small_font.render(f"Întrebare: {profile['question'] or 'citire generală'}", True, WHITE)
        screen.blit(q, q.get_rect(center=(WIDTH // 2, 102)))

        instr = tiny_font.render("Click pe fiecare carte pentru a o întoarce. Apoi alege o carte pentru interpretare. ESC = meniu.", True, GRAY)
        screen.blit(instr, instr.get_rect(center=(WIDTH // 2, 125)))

        for i, card in enumerate(cards):
            label = tiny_font.render(positions[i], True, GOLD)
            screen.blit(label, label.get_rect(center=(card.x + CARD_W // 2, card.y - 18)))
            card.update()
            card.draw()
            if card.revealed and i == selected_index:
                glow = card.rect().inflate(14, 14)
                pygame.draw.rect(screen, GOLD, glow, 3, border_radius=20)
                pygame.draw.rect(screen, VIOLET, glow.inflate(8, 8), 1, border_radius=24)

        if revealed == number:
            show_results = True

        if show_results:
            panel_rect = pygame.Rect(50, 585, 1180, 220)
            draw_panel(panel_rect)

            selected_card = cards[selected_index]
            orientation = "inversată" if selected_card.reversed else "dreaptă"
            left_x = 82
            top_y = 608

            count_text = tiny_font.render(f"{selected_index + 1}/{number}", True, BLACK)
            pygame.draw.rect(screen, GOLD, (left_x, top_y, 54, 26), border_radius=13)
            screen.blit(count_text, count_text.get_rect(center=(left_x + 27, top_y + 13)))

            heading = small_font.render(f"{positions[selected_index]}  |  {selected_card.data['name']} ({orientation})", True, GOLD)
            screen.blit(heading, (left_x + 70, top_y + 1))

            type_text = tiny_font.render(f"{selected_card.data['type']}  |  {selected_card.data['meaning']}", True, GRAY)
            screen.blit(type_text, (left_x + 70, top_y + 28))

            pygame.draw.line(screen, VIOLET, (left_x, top_y + 58), (1195, top_y + 58), 1)

            lines = make_wrapped_lines(interpretations[selected_index], 1080, tiny_font)
            y = top_y + 76
            for line in lines[:7]:
                line_img = tiny_font.render(line, True, WHITE)
                screen.blit(line_img, (left_x, y))
                y += 18

            for i in range(number):
                dot_x = 250 + i * 28
                color = GOLD if i == selected_index else (70, 55, 95)
                pygame.draw.circle(screen, color, (dot_x, 766), 7)
                if i == selected_index:
                    pygame.draw.circle(screen, WHITE, (dot_x, 766), 7, 1)

            if save_status and pygame.time.get_ticks() < save_status_until:
                saved = tiny_font.render(save_status, True, GREEN)
                screen.blit(saved, saved.get_rect(center=(WIDTH // 2, 724)))

            prev_button.draw(mouse)
            next_button.draw(mouse)
            save_button.draw(mouse)
            menu_button.draw(mouse)
            restart_button.draw(mouse)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    start_screen()

                if show_results:
                    if event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                        selected_index = (selected_index + 1) % number
                    elif event.key in (pygame.K_LEFT, pygame.K_UP):
                        selected_index = (selected_index - 1) % number
                    elif event.key == pygame.K_s:
                        path = save_reading(profile, spread_name, positions, cards, interpretations)
                        save_status = f"Citirea a fost salvată: {path.name}"
                        save_status_until = pygame.time.get_ticks() + 3500

            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, card in enumerate(cards):
                    if card.rect().collidepoint(event.pos) and not card.target:
                        card.target = True
                        revealed += 1
                        selected_index = i
                    elif show_results and card.rect().collidepoint(event.pos) and card.revealed:
                        selected_index = i

                if show_results:
                    if prev_button.clicked(event.pos):
                        selected_index = (selected_index - 1) % number

                    if next_button.clicked(event.pos):
                        selected_index = (selected_index + 1) % number

                    if save_button.clicked(event.pos):
                        path = save_reading(profile, spread_name, positions, cards, interpretations)
                        save_status = f"Citirea a fost salvată: {path.name}"
                        save_status_until = pygame.time.get_ticks() + 3500

                    if menu_button.clicked(event.pos):
                        start_screen()

                    if restart_button.clicked(event.pos):
                        reading_screen(profile, spread_name)

        pygame.display.flip()


start_screen()
