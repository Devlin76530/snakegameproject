import pygame
import random
from collections import deque
import heapq

pygame.init()

# =========================================================
# GAME SETTINGS
# =========================================================

WIDTH = 600
HEIGHT = 400
CELL = 20

COLS = WIDTH // CELL
ROWS = HEIGHT // CELL
TOTAL_CELLS = COLS * ROWS

MAX_SCORE = TOTAL_CELLS - 3

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake AI - Smart & Safe Pathfinder")

clock = pygame.time.Clock()

# =========================================================
# COLORS & FONTS
# =========================================================

BG = (30, 30, 30)
GRID = (45, 45, 45)
WHITE = (255, 255, 255)
GRAY = (160, 160, 160)
GREEN = (0, 180, 0)
DARK_GREEN = (0, 120, 0)
BLUE = (0, 110, 190)
RED = (190, 0, 0)

title_font = pygame.font.Font(None, 65)
button_font = pygame.font.Font(None, 30)
score_font = pygame.font.Font(None, 28)
small_font = pygame.font.Font(None, 22)

# =========================================================
# GET NEIGHBORS
# =========================================================

def get_neighbors(position, game_mode):
    x, y = position
    neighbors = [
        (x + CELL, y),
        (x - CELL, y),
        (x, y + CELL),
        (x, y - CELL)
    ]
    result = []
    for nx, ny in neighbors:
        if game_mode == "NORMAL":
            nx %= WIDTH
            ny %= HEIGHT
            result.append((nx, ny))
        else:
            if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                result.append((nx, ny))
    return result

# =========================================================
# CREATE FOOD (Safe Spawning)
# =========================================================

def create_food(snake, game_mode="NORMAL"):
    """
    Sinh mồi trong tầm kiểm soát: mồi phải nằm trên ô mà đầu rắn 
    có thể tới được và không nằm ở hốc cụt.
    """
    empty_cells = []
    blocked = set(snake)
    head = snake[0]

    # Lấy các ô rỗng mà từ đầu rắn có thể tìm tới
    queue = deque([head])
    reachable = set([head])

    while queue:
        curr = queue.popleft()
        for nxt in get_neighbors(curr, game_mode):
            if nxt not in blocked and nxt not in reachable:
                reachable.add(nxt)
                queue.append(nxt)

    reachable.discard(head)
    
    # Lọc những ô có ít nhất 2 ô trống xung quanh để rắn dễ thoát
    for cell in reachable:
        free_neighbors = sum(
            1 for nxt in get_neighbors(cell, game_mode) if nxt not in blocked
        )
        if free_neighbors >= 1:
            empty_cells.append(cell)

    if not empty_cells:
        # Fallback nếu đường đi bị hạn chế
        all_empty = [
            (x, y) for x in range(0, WIDTH, CELL) 
            for y in range(0, HEIGHT, CELL) if (x, y) not in snake
        ]
        return random.choice(all_empty) if all_empty else None

    return random.choice(empty_cells)

# =========================================================
# RESET GAME
# =========================================================

recent_positions = deque(maxlen=35)

def reset_game():
    global snake, direction, food, score, game_over, win, recent_positions
    snake = [
        (300, 200),
        (280, 200),
        (260, 200)
    ]
    direction = (CELL, 0)
    score = 0
    game_over = False
    win = False
    food = create_food(snake, game_mode)
    recent_positions.clear()
    return snake, direction, food, score

# =========================================================
# PATHFINDING: A* ALGORITHM (Shortest Path)
# =========================================================

def heuristic(a, b):
    # Manhattan distance
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def find_path_astar(snake, target, blocked=None, game_mode="NORMAL"):
    if target is None:
        return None

    if blocked is None:
        blocked = set(snake[:-1])  # Đuôi sẽ di chuyển
    else:
        blocked = set(blocked)

    start = snake[0]
    blocked.discard(start)

    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, target)}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == target:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        for nxt in get_neighbors(current, game_mode):
            if nxt in blocked:
                continue

            tentative_g = g_score[current] + 1

            if nxt not in g_score or tentative_g < g_score[nxt]:
                came_from[nxt] = current
                g_score[nxt] = tentative_g
                f_score[nxt] = tentative_g + heuristic(nxt, target)
                heapq.heappush(open_set, (f_score[nxt], nxt))

    return None

# =========================================================
# HELPER FUNCTIONS FOR SAFETY
# =========================================================

def count_free_space(head, snake, game_mode):
    blocked = set(snake)
    blocked.discard(head)
    queue = deque([head])
    visited = {head}

    while queue:
        current = queue.popleft()
        for nxt in get_neighbors(current, game_mode):
            if nxt not in blocked and nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)

    return len(visited)

def simulate_move(snake, direction, food, game_mode):
    head_x = snake[0][0] + direction[0]
    head_y = snake[0][1] + direction[1]

    if game_mode == "HARD":
        if head_x < 0 or head_x >= WIDTH or head_y < 0 or head_y >= HEIGHT:
            return None
    else:
        head_x %= WIDTH
        head_y %= HEIGHT

    new_head = (head_x, head_y)
    will_eat = (new_head == food)

    if will_eat:
        if new_head in snake:
            return None
    else:
        if new_head in snake[:-1]:
            return None

    new_snake = snake.copy()
    new_snake.insert(0, new_head)
    if not will_eat:
        new_snake.pop()

    return new_snake

def can_reach_tail(snake, game_mode):
    if len(snake) <= 2:
        return True
    head = snake[0]
    tail = snake[-1]
    path = find_path_astar(snake, tail, set(snake[:-1]), game_mode)
    return path is not None

# =========================================================
# ADVANCED AI BRAIN (Săn mồi ngắn nhất & Gỡ rối)
# =========================================================

def get_smart_ai_direction(snake, food, current_direction, game_mode):
    head = snake[0]
    
    # 1. Thử tìm đường ngắn nhất tới mồi qua A*
    path_to_food = find_path_astar(snake, food, set(snake[:-1]), game_mode)

    if path_to_food:
        # Giả lập ăn mồi theo đường đi ngắn nhất
        virtual_snake = snake.copy()
        for step in path_to_food:
            virtual_snake.insert(0, step)
            if step != food:
                virtual_snake.pop()

        # Kiểm tra an toàn: Sau khi ăn xong rắn có bị kẹt (phải vẫn chạm được đuôi)
        if can_reach_tail(virtual_snake, game_mode):
            first_step = path_to_food[0]
            dx = first_step[0] - head[0]
            dy = first_step[1] - head[1]
            
            # Xử lý wrap-around map Normal
            if game_mode == "NORMAL":
                if dx > CELL: dx = -CELL
                elif dx < -CELL: dx = CELL
                if dy > CELL: dy = -CELL
                elif dy < -CELL: dy = CELL
                
            return (dx, dy)

    # 2. GỠ RỐI / HOÃN SĂN MỒI: Nếu không thể ăn an toàn, đi theo đuôi để xả vị trí
    tail_path = find_path_astar(snake, snake[-1], set(snake[:-1]), game_mode)
    if tail_path:
        first_step = tail_path[0]
        dx = first_step[0] - head[0]
        dy = first_step[1] - head[1]
        
        if game_mode == "NORMAL":
            if dx > CELL: dx = -CELL
            elif dx < -CELL: dx = CELL
            if dy > CELL: dy = -CELL
            elif dy < -CELL: dy = CELL
            
        return (dx, dy)

    # 3. NƯỚC ĐI TỐI THƯỢNG (Survival Mode): Chọn hướng có không gian rộng nhất (Flood Fill)
    possible_directions = [(CELL, 0), (-CELL, 0), (0, CELL), (0, -CELL)]
    best_dir = current_direction
    max_space = -1

    for move in possible_directions:
        if move[0] == -current_direction[0] and move[1] == -current_direction[1]:
            continue

        simulated = simulate_move(snake, move, food, game_mode)
        if simulated is not None:
            space = count_free_space(simulated[0], simulated[1:], game_mode)
            if space > max_space:
                max_space = space
                best_dir = move

    return best_dir

# =========================================================
# DRAW FUNCTIONS
# =========================================================

def draw_game(snake, food, score, auto_mode, game_mode, game_speed):
    screen.fill(BG)

    for x in range(0, WIDTH, CELL):
        pygame.draw.line(screen, GRID, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, CELL):
        pygame.draw.line(screen, GRID, (0, y), (WIDTH, y))

    for index, part in enumerate(snake):
        color = GREEN if index == 0 else DARK_GREEN
        pygame.draw.rect(screen, color, (part[0], part[1], CELL, CELL))

    if food is not None:
        pygame.draw.rect(screen, RED, (food[0], food[1], CELL, CELL))

    score_text = score_font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 8))

    speed_mult = game_speed / 10
    info_text = small_font.render(
        f"{game_mode} | {'AUTO' if auto_mode else 'MANUAL'} | Speed: x{speed_mult:.1f}",
        True, WHITE
    )
    screen.blit(info_text, (10, 34))

    mode_button = pygame.Rect(WIDTH - 215, 10, 100, 35)
    mode_color = BLUE if auto_mode else GREEN
    mode_label = "AUTO" if auto_mode else "MANUAL"
    pygame.draw.rect(screen, mode_color, mode_button)
    text = button_font.render(mode_label, True, WHITE)
    screen.blit(text, text.get_rect(center=mode_button.center))

    menu_button = pygame.Rect(WIDTH - 105, 10, 95, 35)
    pygame.draw.rect(screen, BLUE, menu_button)
    text = button_font.render("MENU", True, WHITE)
    screen.blit(text, text.get_rect(center=menu_button.center))

    return mode_button, menu_button

def draw_end_screen(title_text, title_color):
    screen.fill(BG)
    title = title_font.render(title_text, True, title_color)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 100)))

    play_again_button = pygame.Rect(200, 170, 200, 45)
    pygame.draw.rect(screen, GREEN, play_again_button)
    text = button_font.render("PLAY AGAIN", True, WHITE)
    screen.blit(text, text.get_rect(center=play_again_button.center))

    main_menu_button = pygame.Rect(200, 230, 200, 45)
    pygame.draw.rect(screen, BLUE, main_menu_button)
    text = button_font.render("MAIN MENU", True, WHITE)
    screen.blit(text, text.get_rect(center=main_menu_button.center))

    quit_button = pygame.Rect(200, 290, 200, 45)
    pygame.draw.rect(screen, RED, quit_button)
    text = button_font.render("QUIT", True, WHITE)
    screen.blit(text, text.get_rect(center=quit_button.center))

    return play_again_button, main_menu_button, quit_button

# =========================================================
# MAIN LOOP
# =========================================================

game_mode = "NORMAL"
snake, direction, food, score = reset_game()

running = True
menu = True
paused = False
game_over = False
win = False
auto_mode = False

game_speed = 10
target_score = 10
input_text = "10"

while running:
    # -----------------------------------------------------
    # MAIN MENU
    # -----------------------------------------------------
    if menu:
        screen.fill(BG)
        title = title_font.render("SNAKE AI", True, GREEN)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 35)))

        target_text = score_font.render(f"Target Score: {input_text}", True, WHITE)
        screen.blit(target_text, target_text.get_rect(center=(WIDTH // 2, 78)))

        max_text = small_font.render(f"Enter 1 - {MAX_SCORE}", True, GRAY)
        screen.blit(max_text, max_text.get_rect(center=(WIDTH // 2, 102)))

        play_button = pygame.Rect(200, 120, 200, 42)
        pygame.draw.rect(screen, GREEN, play_button)
        text = button_font.render("PLAY", True, WHITE)
        screen.blit(text, text.get_rect(center=play_button.center))

        auto_button = pygame.Rect(200, 168, 200, 42)
        pygame.draw.rect(screen, BLUE, auto_button)
        text = button_font.render("AUTO PLAY", True, WHITE)
        screen.blit(text, text.get_rect(center=auto_button.center))

        normal_button = pygame.Rect(100, 218, 180, 42)
        pygame.draw.rect(screen, GREEN if game_mode == "NORMAL" else (70, 70, 70), normal_button)
        text = button_font.render("NORMAL", True, WHITE)
        screen.blit(text, text.get_rect(center=normal_button.center))

        hard_button = pygame.Rect(320, 218, 180, 42)
        pygame.draw.rect(screen, RED if game_mode == "HARD" else (70, 70, 70), hard_button)
        text = button_font.render("HARD", True, WHITE)
        screen.blit(text, text.get_rect(center=hard_button.center))

        quit_button = pygame.Rect(200, 272, 200, 42)
        pygame.draw.rect(screen, RED, quit_button)
        text = button_font.render("QUIT", True, WHITE)
        screen.blit(text, text.get_rect(center=quit_button.center))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.key == pygame.K_RETURN:
                    if input_text.isdigit() and 1 <= int(input_text) <= MAX_SCORE:
                        target_score = int(input_text)
                elif event.unicode.isdigit() and len(input_text) < 3:
                    input_text += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if play_button.collidepoint(pos) and input_text.isdigit():
                    target_score = int(input_text)
                    snake, direction, food, score = reset_game()
                    menu = False; auto_mode = False
                elif auto_button.collidepoint(pos) and input_text.isdigit():
                    target_score = int(input_text)
                    snake, direction, food, score = reset_game()
                    menu = False; auto_mode = True
                elif normal_button.collidepoint(pos):
                    game_mode = "NORMAL"
                elif hard_button.collidepoint(pos):
                    game_mode = "HARD"
                elif quit_button.collidepoint(pos):
                    running = False

        pygame.display.flip()
        clock.tick(30)
        continue

    # -----------------------------------------------------
    # GAME OVER / WIN
    # -----------------------------------------------------
    if game_over or win:
        title_str = "YOU WIN!" if win else "GAME OVER"
        title_clr = GREEN if win else RED
        p_btn, m_btn, q_btn = draw_end_screen(title_str, title_clr)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if p_btn.collidepoint(event.pos):
                    snake, direction, food, score = reset_game()
                    game_over = False; win = False
                elif m_btn.collidepoint(event.pos):
                    snake, direction, food, score = reset_game()
                    menu = True; game_over = False; win = False
                elif q_btn.collidepoint(event.pos):
                    running = False

        pygame.display.flip()
        clock.tick(30)
        continue

    # -----------------------------------------------------
    # ACTIVE GAMEPLAY
    # -----------------------------------------------------
    mode_btn, menu_btn = draw_game(snake, food, score, auto_mode, game_mode, game_speed)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                game_speed = 5 if game_speed >= 200 else game_speed * 2
            elif event.key == pygame.K_f:
                game_speed = max(game_speed // 2, 5)

            new_dir = None
            if event.key in (pygame.K_w, pygame.K_UP): new_dir = (0, -CELL)
            elif event.key in (pygame.K_s, pygame.K_DOWN): new_dir = (0, CELL)
            elif event.key in (pygame.K_a, pygame.K_LEFT): new_dir = (-CELL, 0)
            elif event.key in (pygame.K_d, pygame.K_RIGHT): new_dir = (CELL, 0)

            if new_dir:
                auto_mode = False
                if not (new_dir[0] == -direction[0] and new_dir[1] == -direction[1]):
                    direction = new_dir

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if mode_btn.collidepoint(event.pos):
                auto_mode = not auto_mode
            elif menu_btn.collidepoint(event.pos):
                menu = True

    # Call AI Direction Update
    if auto_mode and not paused:
        direction = get_smart_ai_direction(snake, food, direction, game_mode)

    # Move logic
    if not paused:
        new_snake = simulate_move(snake, direction, food, game_mode)
        if new_snake is None:
            game_over = True
        else:
            snake = new_snake
            if snake[0] == food:
                score += 1
                food = create_food(snake, game_mode)
                if score >= target_score or food is None:
                    win = True

    pygame.display.flip()
    clock.tick(game_speed)

pygame.quit()