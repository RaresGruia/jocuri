import pygame
import random
import sys
import math
import os

pygame.init()

WIDTH, HEIGHT = 1000, 700
CELL = 24
FPS = 60
MOVE_DELAY_START = 120

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Deluxe")
clock = pygame.time.Clock()

BLACK = (10, 14, 24)
WHITE = (240, 240, 240)
GRAY = (130, 135, 145)
GOLD = (240, 190, 70)
PURPLE = (90, 60, 150)
RED = (220, 35, 45)
DARK_RED = (120, 10, 20)
GREEN = (70, 180, 90)
ORANGE = (255, 140, 35)
DARK_ORANGE = (220, 95, 20)
LIGHT_ORANGE = (255, 180, 80)

title_font = pygame.font.SysFont("georgia", 64, bold=True)
big_font = pygame.font.SysFont("georgia", 38, bold=True)
font = pygame.font.SysFont("georgia", 25)
small_font = pygame.font.SysFont("georgia", 18)

HIGH_SCORE_FILE = "snake_highscore.txt"


def load_high_score():
    if os.path.exists(HIGH_SCORE_FILE):
        try:
            with open(HIGH_SCORE_FILE, "r") as f:
                return int(f.read())
        except:
            return 0
    return 0


def save_high_score(score):
    with open(HIGH_SCORE_FILE, "w") as f:
        f.write(str(score))


def draw_background():
    screen.fill(BLACK)

    for y in range(0, HEIGHT, CELL):
        for x in range(0, WIDTH, CELL):
            color = (16, 24, 38) if (x // CELL + y // CELL) % 2 == 0 else (13, 20, 32)
            pygame.draw.rect(screen, color, (x, y, CELL, CELL))

    for i in range(70):
        x = (i * 137 + pygame.time.get_ticks() // 25) % WIDTH
        y = (i * 71) % HEIGHT
        pygame.draw.circle(screen, (45, 70, 110), (x, y), 1)

    pygame.draw.rect(screen, (8, 10, 18), (0, 0, WIDTH, 55))
    pygame.draw.line(screen, GOLD, (0, 55), (WIDTH, 55), 3)


def draw_button(text, rect, mouse):
    hover = rect.collidepoint(mouse)
    color = GOLD if hover else PURPLE
    text_color = BLACK if hover else WHITE

    pygame.draw.rect(screen, color, rect, border_radius=16)
    pygame.draw.rect(screen, WHITE, rect, 2, border_radius=16)

    txt = font.render(text, True, text_color)
    screen.blit(txt, txt.get_rect(center=rect.center))


def random_grid_position(excluded):
    while True:
        x = random.randrange(1, WIDTH // CELL - 1) * CELL
        y = random.randrange(3, HEIGHT // CELL - 1) * CELL
        pos = (x, y)

        if pos not in excluded:
            return pos


def draw_apple(pos, pulse):
    x, y = pos
    cx = x + CELL // 2
    cy = y + CELL // 2

    glow = pygame.Surface((CELL * 3, CELL * 3), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 40, 60, 55), (CELL * 3 // 2, CELL * 3 // 2), CELL)
    screen.blit(glow, (x - CELL, y - CELL))

    r = CELL // 2 - 3 + int(math.sin(pulse) * 2)

    pygame.draw.circle(screen, DARK_RED, (cx + 2, cy + 2), r)
    pygame.draw.circle(screen, RED, (cx, cy), r)
    pygame.draw.circle(screen, (255, 130, 140), (cx - 5, cy - 5), 4)

    pygame.draw.line(screen, (100, 60, 25), (cx, cy - 10), (cx + 4, cy - 18), 4)
    pygame.draw.ellipse(screen, GREEN, (cx + 3, cy - 21, 14, 8))


def draw_obstacle(pos):
    x, y = pos
    rect = pygame.Rect(x + 2, y + 2, CELL - 4, CELL - 4)

    pygame.draw.rect(screen, (75, 80, 92), rect, border_radius=6)
    pygame.draw.rect(screen, (145, 150, 165), rect, 2, border_radius=6)
    pygame.draw.line(screen, (45, 50, 60), (x + 6, y + 6), (x + CELL - 6, y + CELL - 6), 2)
    pygame.draw.line(screen, (45, 50, 60), (x + CELL - 6, y + 6), (x + 6, y + CELL - 6), 2)


def interpolate(a, b, t):
    return a + (b - a) * t


def draw_snake(snake, old_snake, progress, direction):
    for i in range(len(snake) - 1, -1, -1):
        current = snake[i]
        old = old_snake[i] if i < len(old_snake) else current

        x = interpolate(old[0], current[0], progress)
        y = interpolate(old[1], current[1], progress)

        if i == 0:
            color = ORANGE
            size = CELL
        else:
            color = (
                max(140, DARK_ORANGE[0] - i * 2),
                max(70, DARK_ORANGE[1] - i),
                20
            )
            size = CELL - 2

        rect = pygame.Rect(x + 1, y + 1, size - 2, size - 2)
        pygame.draw.rect(screen, color, rect, border_radius=10)

        pygame.draw.circle(
            screen,
            LIGHT_ORANGE,
            (int(x + CELL // 2), int(y + CELL // 2)),
            max(3, CELL // 5),
            1
        )

    hx, hy = snake[0]
    old_hx, old_hy = old_snake[0]

    hx = interpolate(old_hx, hx, progress)
    hy = interpolate(old_hy, hy, progress)

    cx = int(hx + CELL // 2)
    cy = int(hy + CELL // 2)

    eye_dx = 0
    eye_dy = 0

    if direction == (CELL, 0):
        eye_dx = 5
    elif direction == (-CELL, 0):
        eye_dx = -5
    elif direction == (0, CELL):
        eye_dy = 5
    elif direction == (0, -CELL):
        eye_dy = -5

    pygame.draw.circle(screen, WHITE, (cx - 5 + eye_dx, cy - 5 + eye_dy), 4)
    pygame.draw.circle(screen, WHITE, (cx + 5 + eye_dx, cy - 5 + eye_dy), 4)
    pygame.draw.circle(screen, BLACK, (cx - 5 + eye_dx, cy - 5 + eye_dy), 2)
    pygame.draw.circle(screen, BLACK, (cx + 5 + eye_dx, cy - 5 + eye_dy), 2)


def add_eat_particles(particles, pos):
    x, y = pos
    cx = x + CELL // 2
    cy = y + CELL // 2

    for _ in range(25):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1.5, 4)

        particles.append({
            "x": cx,
            "y": cy,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "r": random.randint(2, 5),
            "life": random.randint(25, 45),
            "color": random.choice([RED, GOLD, ORANGE, GREEN])
        })


def update_particles(particles):
    for p in particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["life"] -= 1
        p["r"] = max(1, p["r"] - 0.04)

        if p["life"] <= 0:
            particles.remove(p)


def draw_particles(particles):
    for p in particles:
        pygame.draw.circle(screen, p["color"], (int(p["x"]), int(p["y"])), int(p["r"]))


def draw_ui(score, high_score, speed_level):
    score_text = font.render(f"Scor: {score}", True, WHITE)
    screen.blit(score_text, (20, 15))

    high_text = font.render(f"Record: {high_score}", True, GOLD)
    screen.blit(high_text, (175, 15))

    speed_text = font.render(f"Viteză: {speed_level}", True, WHITE)
    screen.blit(speed_text, (390, 15))

    hint = small_font.render("WASD / Săgeți | P = pauză | ESC = meniu", True, GRAY)
    screen.blit(hint, (WIDTH - 385, 19))


def menu():
    high_score = load_high_score()

    start_rect = pygame.Rect(WIDTH // 2 - 150, 330, 300, 65)
    quit_rect = pygame.Rect(WIDTH // 2 - 150, 420, 300, 60)

    while True:
        clock.tick(FPS)
        mouse = pygame.mouse.get_pos()

        draw_background()

        title = title_font.render("Snake Deluxe", True, GOLD)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 170)))

        subtitle = font.render("Șarpe portocaliu, mere, obstacole și mișcare fluidă.", True, WHITE)
        screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 240)))

        record = font.render(f"Record: {high_score}", True, GOLD)
        screen.blit(record, record.get_rect(center=(WIDTH // 2, 285)))

        draw_button("Începe jocul", start_rect, mouse)
        draw_button("Ieșire", quit_rect, mouse)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_rect.collidepoint(event.pos):
                    game()
                if quit_rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

        pygame.display.flip()


def pause_screen():
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(190)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    text = big_font.render("Pauză", True, GOLD)
    screen.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))

    hint = font.render("Apasă P ca să continui", True, WHITE)
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 25)))

    pygame.display.flip()


def game_over_screen(score, high_score):
    restart_rect = pygame.Rect(WIDTH // 2 - 160, 390, 320, 60)
    menu_rect = pygame.Rect(WIDTH // 2 - 160, 470, 320, 60)

    while True:
        clock.tick(FPS)
        mouse = pygame.mouse.get_pos()

        draw_background()

        title = title_font.render("Game Over", True, RED)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 200)))

        score_text = font.render(f"Scor final: {score}", True, WHITE)
        screen.blit(score_text, score_text.get_rect(center=(WIDTH // 2, 285)))

        high_text = font.render(f"Record: {high_score}", True, GOLD)
        screen.blit(high_text, high_text.get_rect(center=(WIDTH // 2, 325)))

        draw_button("Restart", restart_rect, mouse)
        draw_button("Meniu principal", menu_rect, mouse)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if restart_rect.collidepoint(event.pos):
                    game()
                if menu_rect.collidepoint(event.pos):
                    menu()

        pygame.display.flip()


def game():
    high_score = load_high_score()

    start_x = (WIDTH // 2 // CELL) * CELL
    start_y = (HEIGHT // 2 // CELL) * CELL

    snake = [
        (start_x, start_y),
        (start_x - CELL, start_y),
        (start_x - CELL * 2, start_y)
    ]

    old_snake = snake.copy()

    direction = (CELL, 0)
    next_direction = direction

    obstacles = []

    for _ in range(12):
        obstacles.append(random_grid_position(set(snake + obstacles)))

    apple = random_grid_position(set(snake + obstacles))

    score = 0
    speed_level = 1
    move_delay = MOVE_DELAY_START
    move_timer = 0
    progress = 1

    particles = []
    paused = False

    while True:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    menu()

                if event.key == pygame.K_p:
                    paused = not paused

                if event.key in [pygame.K_UP, pygame.K_w] and direction != (0, CELL):
                    next_direction = (0, -CELL)

                elif event.key in [pygame.K_DOWN, pygame.K_s] and direction != (0, -CELL):
                    next_direction = (0, CELL)

                elif event.key in [pygame.K_LEFT, pygame.K_a] and direction != (CELL, 0):
                    next_direction = (-CELL, 0)

                elif event.key in [pygame.K_RIGHT, pygame.K_d] and direction != (-CELL, 0):
                    next_direction = (CELL, 0)

        if paused:
            pause_screen()
            continue

        move_timer += dt
        progress = min(1, move_timer / move_delay)

        if move_timer >= move_delay:
            move_timer = 0
            progress = 0

            old_snake = snake.copy()
            direction = next_direction

            head_x, head_y = snake[0]
            new_head = (head_x + direction[0], head_y + direction[1])

            hit_wall = (
                new_head[0] < 0 or
                new_head[0] >= WIDTH or
                new_head[1] < 55 or
                new_head[1] >= HEIGHT
            )

            hit_self = new_head in snake
            hit_obstacle = new_head in obstacles

            if hit_wall or hit_self or hit_obstacle:
                if score > high_score:
                    high_score = score
                    save_high_score(high_score)

                game_over_screen(score, high_score)

            snake.insert(0, new_head)

            if new_head == apple:
                score += 1
                add_eat_particles(particles, apple)

                speed_level = 1 + score // 4
                move_delay = max(55, MOVE_DELAY_START - score * 4)

                if score % 4 == 0 and len(obstacles) < 28:
                    obstacles.append(random_grid_position(set(snake + obstacles + [apple])))

                apple = random_grid_position(set(snake + obstacles))
            else:
                snake.pop()

        update_particles(particles)

        draw_background()

        for obstacle in obstacles:
            draw_obstacle(obstacle)

        draw_apple(apple, pygame.time.get_ticks() / 180)

        draw_snake(snake, old_snake, progress, direction)

        draw_particles(particles)
        draw_ui(score, high_score, speed_level)

        pygame.display.flip()


menu()