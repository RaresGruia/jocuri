import pygame
import random
import sys
import math
import os

pygame.init()

WIDTH, HEIGHT = 1000, 700
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Deluxe")
clock = pygame.time.Clock()

SKY_TOP = (75, 175, 245)
SKY_BOTTOM = (190, 230, 255)
WHITE = (245, 245, 245)
BLACK = (20, 20, 25)
YELLOW = (255, 215, 65)
ORANGE = (245, 125, 35)
RED = (220, 55, 70)
GREEN = (70, 190, 90)
DARK_GREEN = (35, 135, 60)
GOLD = (240, 190, 70)
PURPLE = (90, 70, 170)
GROUND = (210, 165, 90)
GRASS = (60, 170, 75)
GRAY = (80, 90, 105)

title_font = pygame.font.SysFont("georgia", 64, bold=True)
big_font = pygame.font.SysFont("georgia", 38, bold=True)
font = pygame.font.SysFont("georgia", 25)
small_font = pygame.font.SysFont("georgia", 18)

HIGH_SCORE_FILE = "flappy_highscore.txt"

BIRD_X = 250
BIRD_RADIUS = 22
GRAVITY = 0.45
FLAP_POWER = -8.7

PIPE_W = 90
PIPE_GAP_START = 205
PIPE_SPEED_START = 4
PIPE_INTERVAL = 1450

GROUND_H = 90


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


def draw_gradient_background():
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(SKY_TOP[0] * (1 - ratio) + SKY_BOTTOM[0] * ratio)
        g = int(SKY_TOP[1] * (1 - ratio) + SKY_BOTTOM[1] * ratio)
        b = int(SKY_TOP[2] * (1 - ratio) + SKY_BOTTOM[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))


def draw_sun():
    t = pygame.time.get_ticks() / 700
    cx, cy = WIDTH - 130, 115
    glow = pygame.Surface((220, 220), pygame.SRCALPHA)

    for r in range(90, 20, -12):
        alpha = max(10, 65 - r // 2)
        pygame.draw.circle(glow, (255, 220, 90, alpha), (110, 110), r)

    screen.blit(glow, (cx - 110, cy - 110))
    pygame.draw.circle(screen, (255, 225, 95), (cx, cy), 38)

    for i in range(12):
        angle = i * math.pi / 6 + t * 0.1
        x1 = cx + math.cos(angle) * 50
        y1 = cy + math.sin(angle) * 50
        x2 = cx + math.cos(angle) * 68
        y2 = cy + math.sin(angle) * 68
        pygame.draw.line(screen, (255, 225, 95), (x1, y1), (x2, y2), 3)


def draw_cloud(x, y, scale):
    color = (255, 255, 255)
    shadow = (220, 235, 245)

    pygame.draw.circle(screen, shadow, (int(x + 4), int(y + 5)), int(22 * scale))
    pygame.draw.circle(screen, shadow, (int(x + 29 * scale), int(y - 5 * scale)), int(28 * scale))
    pygame.draw.circle(screen, shadow, (int(x + 59 * scale), int(y + 5)), int(23 * scale))

    pygame.draw.circle(screen, color, (int(x), int(y)), int(22 * scale))
    pygame.draw.circle(screen, color, (int(x + 25 * scale), int(y - 10 * scale)), int(28 * scale))
    pygame.draw.circle(screen, color, (int(x + 55 * scale), int(y)), int(23 * scale))
    pygame.draw.rect(screen, color, (x - 5 * scale, y, 70 * scale, 22 * scale), border_radius=12)


def draw_ground(offset):
    pygame.draw.rect(screen, GROUND, (0, HEIGHT - GROUND_H, WIDTH, GROUND_H))
    pygame.draw.rect(screen, GRASS, (0, HEIGHT - GROUND_H, WIDTH, 18))

    for x in range(-80, WIDTH + 100, 80):
        xx = x - offset % 80
        pygame.draw.polygon(screen, (180, 125, 60), [
            (xx, HEIGHT - 20),
            (xx + 40, HEIGHT - 55),
            (xx + 80, HEIGHT - 20)
        ])

    for x in range(-40, WIDTH + 40, 40):
        xx = x - offset % 40
        pygame.draw.line(screen, (85, 190, 90), (xx, HEIGHT - GROUND_H + 4), (xx + 12, HEIGHT - GROUND_H - 8), 3)


def draw_button(text, rect, mouse):
    hover = rect.collidepoint(mouse)
    color = GOLD if hover else PURPLE
    text_color = BLACK if hover else WHITE

    pygame.draw.rect(screen, color, rect, border_radius=16)
    pygame.draw.rect(screen, WHITE, rect, 2, border_radius=16)

    txt = font.render(text, True, text_color)
    screen.blit(txt, txt.get_rect(center=rect.center))


def draw_bird(x, y, velocity, frame):
    angle = max(-32, min(38, velocity * 4))

    bird_surface = pygame.Surface((90, 78), pygame.SRCALPHA)
    cx, cy = 45, 39

    wing_offset = math.sin(frame / 80) * 8

    pygame.draw.ellipse(bird_surface, ORANGE, (15, 19, 55, 42))
    pygame.draw.ellipse(bird_surface, YELLOW, (22, 13, 47, 39))
    pygame.draw.ellipse(bird_surface, (255, 235, 120), (31, 20, 25, 15))

    pygame.draw.polygon(bird_surface, (255, 185, 40), [
        (30, 43),
        (6, 32 + wing_offset),
        (32, 28)
    ])

    pygame.draw.circle(bird_surface, WHITE, (60, 26), 10)
    pygame.draw.circle(bird_surface, BLACK, (63, 27), 4)
    pygame.draw.circle(bird_surface, WHITE, (64, 25), 1)

    pygame.draw.polygon(bird_surface, RED, [
        (68, 35),
        (86, 41),
        (68, 47)
    ])

    pygame.draw.line(bird_surface, BLACK, (70, 41), (84, 41), 1)

    rotated = pygame.transform.rotate(bird_surface, -angle)
    rect = rotated.get_rect(center=(x, y))
    screen.blit(rotated, rect)


def draw_pipe(pipe):
    x = pipe["x"]
    gap_y = pipe["gap_y"]
    gap = pipe["gap"]

    top_rect = pygame.Rect(x, 0, PIPE_W, gap_y - gap // 2)
    bottom_rect = pygame.Rect(x, gap_y + gap // 2, PIPE_W, HEIGHT - GROUND_H - (gap_y + gap // 2))

    for rect in [top_rect, bottom_rect]:
        pygame.draw.rect(screen, DARK_GREEN, rect, border_radius=10)
        pygame.draw.rect(screen, GREEN, rect.inflate(-14, 0), border_radius=8)

        highlight = pygame.Rect(rect.x + 12, rect.y + 10, 12, max(0, rect.h - 20))
        if highlight.h > 0:
            pygame.draw.rect(screen, (115, 225, 120), highlight, border_radius=6)

    cap_h = 35
    top_cap = pygame.Rect(x - 8, gap_y - gap // 2 - cap_h, PIPE_W + 16, cap_h)
    bottom_cap = pygame.Rect(x - 8, gap_y + gap // 2, PIPE_W + 16, cap_h)

    pygame.draw.rect(screen, DARK_GREEN, top_cap, border_radius=8)
    pygame.draw.rect(screen, DARK_GREEN, bottom_cap, border_radius=8)
    pygame.draw.rect(screen, GREEN, top_cap.inflate(-12, -8), border_radius=8)
    pygame.draw.rect(screen, GREEN, bottom_cap.inflate(-12, -8), border_radius=8)


def create_pipe(score):
    gap = max(150, PIPE_GAP_START - score * 2)
    gap_y = random.randint(170, HEIGHT - GROUND_H - 170)

    return {
        "x": WIDTH + 40,
        "gap_y": gap_y,
        "gap": gap,
        "scored": False
    }


def bird_collision_rect(x, y):
    return pygame.Rect(x - 20, y - 17, 40, 34)


def pipe_collides(pipe, bird_rect):
    x = pipe["x"]
    gap_y = pipe["gap_y"]
    gap = pipe["gap"]

    top = pygame.Rect(x, 0, PIPE_W, gap_y - gap // 2)
    bottom = pygame.Rect(x, gap_y + gap // 2, PIPE_W, HEIGHT - GROUND_H - (gap_y + gap // 2))

    return bird_rect.colliderect(top) or bird_rect.colliderect(bottom)


def add_particles(particles, x, y, color, amount=18):
    for _ in range(amount):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1, 4)

        particles.append({
            "x": x,
            "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "r": random.randint(2, 5),
            "life": random.randint(20, 45),
            "color": color
        })


def update_particles(particles):
    for p in particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.04
        p["life"] -= 1
        p["r"] = max(1, p["r"] - 0.04)

        if p["life"] <= 0:
            particles.remove(p)


def draw_particles(particles):
    for p in particles:
        pygame.draw.circle(screen, p["color"], (int(p["x"]), int(p["y"])), int(p["r"]))


def draw_ui(score, high_score, speed):
    pygame.draw.rect(screen, (20, 35, 70), (0, 0, WIDTH, 58))
    pygame.draw.line(screen, GOLD, (0, 58), (WIDTH, 58), 3)

    s = font.render(f"Scor: {score}", True, WHITE)
    screen.blit(s, (20, 16))

    h = font.render(f"Record: {high_score}", True, GOLD)
    screen.blit(h, (170, 16))

    sp = font.render(f"Viteză: {speed:.1f}", True, WHITE)
    screen.blit(sp, (390, 16))

    hint = small_font.render("SPACE / Click = zboară | P = pauză | ESC = meniu", True, WHITE)
    screen.blit(hint, (WIDTH - 470, 20))


def draw_scene(clouds, ground_offset):
    draw_gradient_background()
    draw_sun()

    for cloud in clouds:
        draw_cloud(cloud["x"], cloud["y"], cloud["scale"])

    draw_ground(ground_offset)


def make_clouds():
    return [
        {"x": 100, "y": 130, "scale": 1.1, "speed": 0.35},
        {"x": 450, "y": 90, "scale": 0.8, "speed": 0.25},
        {"x": 750, "y": 160, "scale": 1.3, "speed": 0.3},
        {"x": 950, "y": 80, "scale": 0.65, "speed": 0.22},
    ]


def update_clouds(clouds):
    for cloud in clouds:
        cloud["x"] -= cloud["speed"]

        if cloud["x"] < -130:
            cloud["x"] = WIDTH + 130
            cloud["y"] = random.randint(75, 190)


def menu():
    high_score = load_high_score()
    clouds = make_clouds()

    start_rect = pygame.Rect(WIDTH // 2 - 160, 350, 320, 65)
    quit_rect = pygame.Rect(WIDTH // 2 - 160, 440, 320, 60)

    ground_offset = 0

    while True:
        clock.tick(FPS)
        mouse = pygame.mouse.get_pos()

        ground_offset += 3
        update_clouds(clouds)
        draw_scene(clouds, ground_offset)

        title = title_font.render("Flappy Deluxe", True, GOLD)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 180)))

        subtitle = font.render("Zboară printre țevi, strânge scor și bate recordul.", True, BLACK)
        screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 250)))

        record = font.render(f"Record: {high_score}", True, BLACK)
        screen.blit(record, record.get_rect(center=(WIDTH // 2, 300)))

        draw_bird(WIDTH // 2, 105 + math.sin(pygame.time.get_ticks() / 300) * 10, 0, pygame.time.get_ticks())

        draw_button("Începe jocul", start_rect, mouse)
        draw_button("Ieșire", quit_rect, mouse)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_rect.collidepoint(event.pos):
                    game()
                if quit_rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

        pygame.display.flip()


def pause_screen():
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(170)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    t = big_font.render("Pauză", True, GOLD)
    screen.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))

    h = font.render("Apasă P ca să continui", True, WHITE)
    screen.blit(h, h.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 25)))

    pygame.display.flip()


def game_over_screen(score, high_score):
    restart_rect = pygame.Rect(WIDTH // 2 - 160, 380, 320, 60)
    menu_rect = pygame.Rect(WIDTH // 2 - 160, 460, 320, 60)

    clouds = make_clouds()
    ground_offset = 0

    while True:
        clock.tick(FPS)
        mouse = pygame.mouse.get_pos()

        ground_offset += 2
        update_clouds(clouds)
        draw_scene(clouds, ground_offset)

        title = title_font.render("Game Over", True, RED)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 200)))

        score_text = font.render(f"Scor final: {score}", True, BLACK)
        screen.blit(score_text, score_text.get_rect(center=(WIDTH // 2, 285)))

        high_text = font.render(f"Record: {high_score}", True, BLACK)
        screen.blit(high_text, high_text.get_rect(center=(WIDTH // 2, 325)))

        draw_button("Restart", restart_rect, mouse)
        draw_button("Meniu principal", menu_rect, mouse)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if restart_rect.collidepoint(event.pos):
                    game()
                if menu_rect.collidepoint(event.pos):
                    menu()

        pygame.display.flip()


def game():
    high_score = load_high_score()

    bird_y = HEIGHT // 2
    velocity = 0

    pipes = []
    particles = []

    score = 0
    speed = PIPE_SPEED_START
    last_pipe_time = pygame.time.get_ticks()

    ground_offset = 0
    paused = False
    started = False

    clouds = make_clouds()

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    menu()

                if event.key == pygame.K_p:
                    paused = not paused

                if event.key == pygame.K_SPACE:
                    velocity = FLAP_POWER
                    started = True
                    add_particles(particles, BIRD_X - 15, bird_y + 10, YELLOW)

            if event.type == pygame.MOUSEBUTTONDOWN:
                velocity = FLAP_POWER
                started = True
                add_particles(particles, BIRD_X - 15, bird_y + 10, YELLOW)

        if paused:
            pause_screen()
            continue

        if started:
            velocity += GRAVITY
            bird_y += velocity
            ground_offset += speed

            now = pygame.time.get_ticks()

            if now - last_pipe_time > PIPE_INTERVAL:
                pipes.append(create_pipe(score))
                last_pipe_time = now

            for pipe in pipes[:]:
                pipe["x"] -= speed

                if pipe["x"] + PIPE_W < 0:
                    pipes.remove(pipe)

                if not pipe["scored"] and pipe["x"] + PIPE_W < BIRD_X:
                    pipe["scored"] = True
                    score += 1
                    speed = PIPE_SPEED_START + score * 0.13
                    add_particles(particles, BIRD_X, bird_y, GOLD, amount=25)

        else:
            bird_y = HEIGHT // 2 + math.sin(pygame.time.get_ticks() / 300) * 12
            ground_offset += 2

        update_clouds(clouds)
        update_particles(particles)

        draw_scene(clouds, ground_offset)

        for pipe in pipes:
            draw_pipe(pipe)

        draw_particles(particles)
        draw_bird(BIRD_X, bird_y, velocity, pygame.time.get_ticks())
        draw_ui(score, high_score, speed)

        if not started:
            txt = big_font.render("Apasă SPACE sau Click ca să începi", True, BLACK)
            screen.blit(txt, txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 110)))

        bird_rect = bird_collision_rect(BIRD_X, bird_y)

        hit_ground = bird_y + BIRD_RADIUS >= HEIGHT - GROUND_H
        hit_ceiling = bird_y - BIRD_RADIUS <= 58
        hit_pipe = any(pipe_collides(pipe, bird_rect) for pipe in pipes)

        if hit_ground or hit_ceiling or hit_pipe:
            add_particles(particles, BIRD_X, bird_y, RED, amount=35)

            if score > high_score:
                high_score = score
                save_high_score(high_score)

            game_over_screen(score, high_score)

        pygame.display.flip()


menu()