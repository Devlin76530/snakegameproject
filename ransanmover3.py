



import pygame
import random
import heapq
from collections import deque

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

# Snake ban đầu dài 3
MAX_SCORE = TOTAL_CELLS - 3

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake AI")

clock = pygame.time.Clock()


# =========================================================
# COLORS
# =========================================================

BG = (30, 30, 30)
GRID = (45, 45, 45)

WHITE = (255, 255, 255)
GRAY = (160, 160, 160)

GREEN = (0, 180, 0)
DARK_GREEN = (0, 120, 0)

BLUE = (0, 110, 190)
RED = (190, 0, 0)

YELLOW = (220, 180, 0)


# =========================================================
# FONTS
# =========================================================

title_font = pygame.font.Font(None, 65)
button_font = pygame.font.Font(None, 30)
score_font = pygame.font.Font(None, 28)
small_font = pygame.font.Font(None, 22)


# =========================================================
# CREATE FOOD
# =========================================================

def create_food(snake):

    empty_cells = []

    for x in range(0, WIDTH, CELL):

        for y in range(0, HEIGHT, CELL):

            position = (x, y)

            if position not in snake:

                empty_cells.append(position)

    if not empty_cells:

        return None

    return random.choice(empty_cells)


# =========================================================
# RESET GAME
# =========================================================
recent_positions = deque(maxlen=35)

def reset_game():
    global snake
    global direction
    global food
    global score
    global game_over
    global game_won
    global recent_positions
    global pattern_started
    global pattern_path
    global spiral_phase
    global spiral_clockwise
    global shortcut_active
    global shortcut_path
    global shortcut_index
    global shortcut_food
    global hard_escape_steps

    hard_escape_steps = 0   

    snake = [
        (300, 200),
        (280, 200),
        (260, 200)
    ]

    direction = (CELL, 0)
    food = create_food(snake)

    score = 0
    game_over = False
    game_won = False
    pattern_started = False
    pattern_path = []



    recent_positions.clear()
    spiral_phase = "IN"
    spiral_clockwise = True


    shortcut_active = False
    shortcut_path = []
    shortcut_index = 0
    shortcut_food = None


    return snake, direction, food, score


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

        # =================================================
        # NORMAL
        # =================================================

        if game_mode == "NORMAL":

            nx %= WIDTH
            ny %= HEIGHT

            result.append((nx, ny))

        # =================================================
        # HARD
        # =================================================

        else:

            if (
                0 <= nx < WIDTH
                and
                0 <= ny < HEIGHT
            ):

                result.append((nx, ny))

    return result


# =========================================================
# FIND PATH - BFS
# =========================================================

def find_path(
    snake,
    target,
    blocked=None,
    game_mode="NORMAL"
):

    if target is None:

        return None

    if blocked is None:

        blocked = set(snake)

    else:

        blocked = set(blocked)

    start = snake[0]

    blocked.discard(start)

    queue = deque([start])

    visited = {start}

    previous = {}

    while queue:

        current = queue.popleft()

        if current == target:

            break

        for next_pos in get_neighbors(
            current,
            game_mode
        ):

            if next_pos in blocked:

                continue

            if next_pos in visited:

                continue

            visited.add(next_pos)

            previous[next_pos] = current

            queue.append(next_pos)

    if target not in visited:

        return None

    path = []

    current = target

    while current != start:

        path.append(current)

        current = previous[current]

    path.reverse()

    return path


# =========================================================
# COUNT FREE SPACE
# =========================================================

def count_free_space(
    head,
    snake,
    game_mode
):

    blocked = set(snake)

    blocked.discard(head)

    queue = deque([head])

    visited = {head}

    while queue:

        current = queue.popleft()

        for next_pos in get_neighbors(
            current,
            game_mode
        ):

            if next_pos in blocked:

                continue

            if next_pos in visited:

                continue

            visited.add(next_pos)

            queue.append(next_pos)

    return len(visited)


# =========================================================
# CAN REACH TAIL
# =========================================================

def can_reach_tail(
    snake,
    game_mode
):

    if len(snake) <= 2:

        return True

    head = snake[0]

    tail = snake[-1]

    # Đuôi sẽ di chuyển
    blocked = set(snake[:-1])

    path = find_path(
        [head],
        tail,
        blocked,
        game_mode
    )

    return path is not None


# =========================================================
# SIMULATE MOVE
# =========================================================

def simulate_move(
    snake,
    direction,
    food,
    game_mode
):

    head_x = snake[0][0] + direction[0]
    head_y = snake[0][1] + direction[1]

    # =====================================================
    # HARD
    # =====================================================

    if game_mode == "HARD":

        if (
            head_x < 0
            or head_x >= WIDTH
            or head_y < 0
            or head_y >= HEIGHT
        ):

            return None

    # =====================================================
    # NORMAL
    # =====================================================

    else:

        head_x %= WIDTH
        head_y %= HEIGHT

    new_head = (head_x, head_y)

    will_eat = new_head == food

    # Nếu ăn food thì đuôi KHÔNG di chuyển
    if will_eat:

        if new_head in snake:

            return None

    # Nếu không ăn thì đuôi di chuyển
    else:

        if new_head in snake[:-1]:

            return None

    new_snake = snake.copy()

    new_snake.insert(
        0,
        new_head
    )

    if not will_eat:

        new_snake.pop()

    return new_snake


# =========================================================
# AI
# =========================================================

def find_best_direction(
    snake,
    food,
    current_direction,
    game_mode,
    recent_positions
):

    possible_directions = [
        (CELL, 0),
        (-CELL, 0),
        (0, CELL),
        (0, -CELL)
    ]

    candidates = []

    # =====================================================
    # TEST ALL DIRECTIONS
    # =====================================================

    for direction in possible_directions:

        # Không quay 180 độ
        if (
            direction[0] == -current_direction[0]
            and
            direction[1] == -current_direction[1]
        ):

            continue

        new_snake = simulate_move(
            snake,
            direction,
            food,
            game_mode
        )

        # Đâm tường / thân
        if new_snake is None:

            continue

        new_head = new_snake[0]

        # =================================================
        # FREE SPACE
        # =================================================

        free_space = count_free_space(
            new_head,
            new_snake[1:],
            game_mode
        )

        # Không gian tối thiểu
        minimum_space = max(
            len(new_snake) + 2,
            8
        )

        if free_space < minimum_space:

            continue

        # =================================================
        # CAN REACH TAIL
        # =================================================

        tail_safe = can_reach_tail(
            new_snake,
            game_mode
        )

        # =================================================
        # PATH TO FOOD
        # =================================================

        food_path = find_path(
            new_snake,
            food,
            new_snake[1:],
            game_mode
        )

        if food_path is None:

            food_distance = 9999

        else:

            food_distance = len(food_path)

        # =================================================
        # ANTI LOOP
        # =================================================

        loop_penalty = 0

        if new_head in recent_positions:

            loop_penalty = 1500

        # =================================================
        # SCORE
        # =================================================

        value = 0

        # Không gian
        value += free_space * 5

        # Có đường về đuôi
        if tail_safe:

            value += 2500

        else:

            value -= 1800

        # Gần food
        if food_path is not None:

            value -= food_distance * 6

        else:

            value -= 300

        # =================================================
        # ĂN FOOD
        # =================================================

        if new_head == food:

            # Ăn food an toàn
            if tail_safe:

                value += 5000

            else:

                value -= 3000

        # =================================================
        # ANTI LOOP
        # =================================================

        value -= loop_penalty

        candidates.append(
            (
                value,
                direction
            )
        )

    # =====================================================
    # CHỌN NƯỚC TỐT NHẤT
    # =====================================================

    if candidates:

        candidates.sort(
            key=lambda item: item[0],
            reverse=True
        )

        return candidates[0][1]

    # =====================================================
    # FALLBACK
    # =====================================================

    fallback = []

    for direction in possible_directions:

        if (
            direction[0] == -current_direction[0]
            and
            direction[1] == -current_direction[1]
        ):

            continue

        new_snake = simulate_move(
            snake,
            direction,
            food,
            game_mode
        )

        if new_snake is None:

            continue

        free_space = count_free_space(
            new_snake[0],
            new_snake[1:],
            game_mode
        )

        fallback.append(
            (
                free_space,
                direction
            )
        )

    if fallback:

        fallback.sort(
            key=lambda x: x[0],
            reverse=True
        )

        return fallback[0][1]

    return current_direction


# =========================================================
# DRAW GAME
# =========================================================
# =========================
# PATTERN AFTER SCORE 100
# =========================

def generate_row_path():
    path = []

    for row in range(ROWS):
        row_cells = [
            (col * CELL, row * CELL)
            for col in range(COLS)
        ]

        if row % 2 == 1:
            row_cells.reverse()

        path.extend(row_cells)

    return path


def generate_spiral_path():
    path = []

    left = 0
    right = COLS - 1
    top = 0
    bottom = ROWS - 1

    while left <= right and top <= bottom:

        # Đi sang phải
        for col in range(left, right + 1):
            path.append((col * CELL, top * CELL))

        top += 1

        # Đi xuống
        for row in range(top, bottom + 1):
            path.append((right * CELL, row * CELL))

        right -= 1

        # Đi sang trái
        if top <= bottom:
            for col in range(right, left - 1, -1):
                path.append((col * CELL, bottom * CELL))

            bottom -= 1

        # Đi lên
        if left <= right:
            for row in range(bottom, top - 1, -1):
                path.append((left * CELL, row * CELL))

            left += 1

    # Tới tâm rồi đổi chiều
    middle = len(path) // 2

    path = path[:middle] + list(reversed(path[middle:]))

    return path


def get_pattern_direction():
    
    global spiral_phase
    global spiral_clockwise

    if direction is None:
        return (CELL, 0)

    head = snake[0]

    col = head[0] // CELL
    row = head[1] // CELL

    # ============================================
    # XÁC ĐỊNH TÂM
    # ============================================

    center_cols = {
        COLS // 2 - 1,
        COLS // 2
    }

    center_rows = {
        ROWS // 2 - 1,
        ROWS // 2
    }

    at_center = (
        col in center_cols
        and row in center_rows
    )

    # ============================================
    # XÁC ĐỊNH RÌA
    # ============================================

    at_edge = (
        col == 0
        or col == COLS - 1
        or row == 0
        or row == ROWS - 1
    )

    # ============================================
    # TÂM -> ĐỔI SANG ĐI RA
    # ============================================

    if spiral_phase == "IN" and at_center:

        spiral_phase = "OUT"

        # Đổi chiều xoắn
        spiral_clockwise = not spiral_clockwise

    # ============================================
    # RÌA -> ĐỔI SANG ĐI VÀO
    # ============================================

    elif spiral_phase == "OUT" and at_edge:

        spiral_phase = "IN"

        # Đổi chiều xoắn
        spiral_clockwise = not spiral_clockwise

    # ============================================
    # TÂM BÀN
    # ============================================

    center_x = (WIDTH - CELL) / 2
    center_y = (HEIGHT - CELL) / 2

    dx = head[0] - center_x
    dy = head[1] - center_y

    distance = max(
        abs(dx),
        abs(dy)
    )

    if distance == 0:

        if spiral_phase == "OUT":

            if spiral_clockwise:
                return (CELL, 0)
            else:
                return (-CELL, 0)

        return direction

    # ============================================
    # VECTOR HƯỚNG VÀO / RA
    # ============================================

    length = (dx * dx + dy * dy) ** 0.5

    if length == 0:
        length = 1

    if spiral_phase == "IN":

        # Hướng vào tâm
        radial_x = -dx / length
        radial_y = -dy / length

    else:

        # Hướng ra ngoài
        radial_x = dx / length
        radial_y = dy / length

    # ============================================
    # VECTOR XOẮN
    # ============================================

    if spiral_clockwise:

        tangent_x = -dy / length
        tangent_y = dx / length

    else:

        tangent_x = dy / length
        tangent_y = -dx / length

    # ============================================
    # KẾT HỢP:
    # XOẮN + VÀO/RA
    # ============================================

    desired_x = (
        tangent_x * 1.8
        + radial_x * 0.7
    )

    desired_y = (
        tangent_y * 1.8
        + radial_y * 0.7
    )

    possible_directions = [
        (CELL, 0),
        (-CELL, 0),
        (0, CELL),
        (0, -CELL)
    ]

    candidates = []

    for move in possible_directions:

        # Không quay đầu 180°
        if (
            move[0] == -direction[0]
            and
            move[1] == -direction[1]
        ):
            continue

        # Kiểm tra đâm tường / thân
        test_snake = simulate_move(
            snake,
            move,
            food,
            game_mode
        )

        if test_snake is None:
            continue

        # Điểm khớp với hướng spiral
        move_x = move[0] / CELL
        move_y = move[1] / CELL

        spiral_score = (
            move_x * desired_x
            + move_y * desired_y
        )

        # Không gian sống
        free_space = count_free_space(
            test_snake[0],
            test_snake[1:],
            game_mode
        )

        value = spiral_score * 100
        value += free_space * 0.5

        # Ưu tiên an toàn với đuôi
        if can_reach_tail(
            test_snake,
            game_mode
        ):
            value += 500

        # Tránh loop
        if test_snake[0] in recent_positions:
            value -= 1000

        # Ăn food thì ưu tiên
        if test_snake[0] == food:
            value += 5000

        candidates.append(
            (
                value,
                move
            )
        )

    # ============================================
    # CHỌN NƯỚC TỐT NHẤT
    # ============================================

    if candidates:

        candidates.sort(
            key=lambda item: item[0],
            reverse=True
        )

        return candidates[0][1]

    # ============================================
    # KHÔNG CÓ NƯỚC -> AI CŨ CỨU
    # ============================================

    return find_best_direction(
        snake,
        food,
        direction,
        game_mode,
        recent_positions
    )    

# =========================================================
# HAMILTONIAN CYCLE + SAFE SHORTCUT
# =========================================================

hamiltonian_path = []
hamiltonian_index = {}

shortcut_active = False
shortcut_path = []
shortcut_index = 0
shortcut_food = None


def generate_hamiltonian_cycle():

    path = []

    # Hàng đầu tiên: trái -> phải
    for x in range(COLS):
        path.append(
            (x * CELL, 0)
        )

    # Các hàng còn lại
    for y in range(1, ROWS):

        if y % 2 == 1:

            for x in range(COLS - 1, 0, -1):
                path.append(
                    (x * CELL, y * CELL)
                )

        else:

            for x in range(1, COLS):
                path.append(
                    (x * CELL, y * CELL)
                )

    # Cột trái cuối
    path.append(
        (0, (ROWS - 1) * CELL)
    )

    for y in range(ROWS - 2, 0, -1):

        path.append(
            (0, y * CELL)
        )

    return path


def setup_hamiltonian():

    global hamiltonian_path
    global hamiltonian_index

    if not hamiltonian_path:

        hamiltonian_path = (
            generate_hamiltonian_cycle()
        )

        hamiltonian_index = {
            pos: i
            for i, pos in enumerate(
                hamiltonian_path
            )
        }


def get_cycle_direction_from_head(head):

    setup_hamiltonian()

    if head not in hamiltonian_index:
        return direction

    head_index = hamiltonian_index[head]

    next_index = (
        head_index + 1
    ) % len(hamiltonian_path)

    target = hamiltonian_path[next_index]

    dx = target[0] - head[0]
    dy = target[1] - head[1]

    if dx > 0:
        return (CELL, 0)

    if dx < 0:
        return (-CELL, 0)

    if dy > 0:
        return (0, CELL)

    if dy < 0:
        return (0, -CELL)

    return direction


def is_opposite_direction(
    move,
    current_direction
):

    return (
        move[0] == -current_direction[0]
        and
        move[1] == -current_direction[1]
    )


def is_snake_aligned_with_cycle(body):

    setup_hamiltonian()

    if not body:
        return False

    head = body[0]

    if head not in hamiltonian_index:
        return False

    head_index = hamiltonian_index[head]

    for i, part in enumerate(body):

        expected_index = (
            head_index - i
        ) % len(hamiltonian_path)

        expected = hamiltonian_path[
            expected_index
        ]

        if part != expected:
            return False

    return True


def get_normal_move_between(
    current,
    target
):

    x, y = current

    possible_moves = [
        (
            (x + CELL) % WIDTH,
            y,
            (CELL, 0)
        ),
        (
            (x - CELL) % WIDTH,
            y,
            (-CELL, 0)
        ),
        (
            x,
            (y + CELL) % HEIGHT,
            (0, CELL)
        ),
        (
            x,
            (y - CELL) % HEIGHT,
            (0, -CELL)
        )
    ]

    for nx, ny, move in possible_moves:

        if (nx, ny) == target:
            return move

    return None


def can_return_to_cycle(body):

    setup_hamiltonian()

    test_snake = body.copy()

    max_steps = min(
        len(test_snake) + 5,
        120
    )

    for _ in range(max_steps):

        if is_snake_aligned_with_cycle(
            test_snake
        ):
            return True

        head = test_snake[0]

        if head not in hamiltonian_index:
            return False

        move = get_cycle_direction_from_head(
            head
        )

        test_snake = simulate_move(
            test_snake,
            move,
            None,
            "NORMAL"
        )

        if test_snake is None:
            return False

    return False


def build_safe_shortcut():

    setup_hamiltonian()

    head = snake[0]

    # Shortcut chỉ bắt đầu khi rắn đang
    # nằm đúng trên Hamiltonian
    if not is_snake_aligned_with_cycle(
        snake
    ):
        return None

    if food is None:
        return None

    if food not in hamiltonian_index:
        return None

    head_index = hamiltonian_index[head]
    food_index = hamiltonian_index[food]

    cycle_length = len(
        hamiltonian_path
    )

    # Food nằm bao xa phía trước trên cycle
    food_cycle_distance = (
        food_index - head_index
    ) % cycle_length

    if food_cycle_distance <= 1:
        return None

    # Số ô trống thực sự còn phía trước
    free_cells = (
        cycle_length - len(snake)
    )

    # Food nằm sau vùng an toàn
    if food_cycle_distance >= free_cells:
        return None

    # =========================================
    # BFS TỚI FOOD
    # =========================================

    path = find_path(
        [head],
        food,
        snake[1:],
        "NORMAL"
    )

    if not path:
        return None

    # Nếu đi cycle còn nhanh gần bằng shortcut
    if len(path) >= food_cycle_distance:
        return None

    # Shortcut quá dài thì bỏ
    if len(path) > 30:
        return None

    # =========================================
    # MỌI Ô TRONG SHORTCUT PHẢI NẰM
    # TRONG ĐOẠN AN TOÀN CỦA CYCLE
    # =========================================

    for pos in path:

        if pos not in hamiltonian_index:
            return None

        pos_index = hamiltonian_index[pos]

        distance_from_head = (
            pos_index - head_index
        ) % cycle_length

        if (
            distance_from_head <= 0
            or
            distance_from_head > food_cycle_distance
        ):
            return None

    # =========================================
    # MÔ PHỎNG TOÀN BỘ SHORTCUT
    # =========================================

    test_snake = snake.copy()

    for i, target in enumerate(path):

        move = get_normal_move_between(
            test_snake[0],
            target
        )

        if move is None:
            return None

        if i == 0:

            if is_opposite_direction(
                move,
                direction
            ):
                return None

        test_snake = simulate_move(
            test_snake,
            move,
            food,
            "NORMAL"
        )

        if test_snake is None:
            return None

    # Phải ăn được food
    if test_snake[0] != food:
        return None

    # =========================================
    # SAU KHI ĂN VẪN PHẢI TỚI ĐƯỢC ĐUÔI
    # =========================================

    if not can_reach_tail(
        test_snake,
        "NORMAL"
    ):
        return None

    # =========================================
    # VÀ PHẢI QUAY LẠI ĐƯỢC CYCLE
    # =========================================

    if not can_return_to_cycle(
        test_snake
    ):
        return None

    return path

# =========================================================
# HARD AI - A* + SURVIVAL + HAMILTONIAN
# =========================================================

HARD_AI_MODE = "HYBRID"


def hard_heuristic(a, b):
    """
    Manhattan distance cho A*
    """
    return (
        abs(a[0] - b[0])
        + abs(a[1] - b[1])
    ) // CELL


def find_path_astar_hard(
    snake,
    target
):
    """
    A* trong HARD.
    Không cho đi xuyên tường.
    """

    if target is None:
        return None

    start = snake[0]

    # Cho phép đi vào ô đuôi hiện tại
    # vì đuôi có thể di chuyển
    blocked = set(snake[:-1])

    blocked.discard(start)

    open_heap = []

    heapq.heappush(
        open_heap,
        (
            hard_heuristic(start, target),
            0,
            start
        )
    )

    previous = {}

    g_score = {
        start: 0
    }

    visited = set()

    while open_heap:

        _, current_cost, current = heapq.heappop(
            open_heap
        )

        if current in visited:
            continue

        visited.add(current)

        # Tới food
        if current == target:

            path = []

            while current != start:

                path.append(current)

                current = previous[current]

            path.reverse()

            return path

        for next_pos in get_neighbors(
            current,
            "HARD"
        ):

            if next_pos in blocked:
                continue

            if next_pos in visited:
                continue

            new_cost = current_cost + 1

            if new_cost < g_score.get(
                next_pos,
                999999
            ):

                g_score[next_pos] = new_cost

                previous[next_pos] = current

                f_score = (
                    new_cost
                    + hard_heuristic(
                        next_pos,
                        target
                    )
                )

                heapq.heappush(
                    open_heap,
                    (
                        f_score,
                        new_cost,
                        next_pos
                    )
                )

    return None


def get_hard_move_between(
    current,
    target
):
    """
    Lấy hướng đi từ current -> target.
    Chỉ dùng cho 2 ô kế nhau.
    """

    dx = target[0] - current[0]
    dy = target[1] - current[1]

    if dx == CELL and dy == 0:
        return (CELL, 0)

    if dx == -CELL and dy == 0:
        return (-CELL, 0)

    if dx == 0 and dy == CELL:
        return (0, CELL)

    if dx == 0 and dy == -CELL:
        return (0, -CELL)

    return None


def hard_path_is_safe(path):
    
    """
    Kiểm tra đường A* trong HARD.

    Không bắt free_space lớn ở từng bước.
    Chỉ kiểm tra:
    1. Không đâm tường
    2. Không đâm thân
    3. Toàn bộ đường đi hợp lệ
    4. Sau khi tới food vẫn có thể sống
    """

    if not path:
        return False

    test_snake = snake.copy()

    for index, target in enumerate(path):

        move = get_hard_move_between(
            test_snake[0],
            target
        )

        if move is None:
            return False

        # Không quay 180° ở bước đầu
        if index == 0:

            if is_opposite_direction(
                move,
                direction
            ):
                return False

        test_snake = simulate_move(
            test_snake,
            move,
            food,
            "HARD"
        )

        # Đâm tường / thân
        if test_snake is None:
            return False

    # Phải thật sự tới food
    if test_snake[0] != food:
        return False

    # =============================================
    # KIỂM TRA KHÔNG GIAN SAU KHI ĂN
    # =============================================

    free_space = count_free_space(
        test_snake[0],
        test_snake[1:],
        "HARD"
    )

    # Chỉ loại nếu thực sự bị nhốt quá nặng
    minimum_space = max(
        len(test_snake) + 1,
        5
    )

    if (
        free_space < minimum_space
        and
        len(test_snake) < TOTAL_CELLS
    ):
        return False

    # =============================================
    # KIỂM TRA CÓ THỂ VỀ ĐUÔI
    # =============================================

    if not can_reach_tail(
        test_snake,
        "HARD"
    ):
        return False

    return True


def get_hard_survival_direction():
    
    possible_directions = [
        (CELL, 0),
        (-CELL, 0),
        (0, CELL),
        (0, -CELL)
    ]

    candidates = []

    for move in possible_directions:

        # Không quay 180°
        if is_opposite_direction(
            move,
            direction
        ):
            continue

        test_snake = simulate_move(
            snake,
            move,
            food,
            "HARD"
        )

        if test_snake is None:
            continue

        head = test_snake[0]

        # =============================================
        # FREE SPACE
        # =============================================

        free_space = count_free_space(
            head,
            test_snake[1:],
            "HARD"
        )

        # =============================================
        # CÓ ĐƯỜNG VỀ ĐUÔI?
        # =============================================

        tail_safe = can_reach_tail(
            test_snake,
            "HARD"
        )

        # =============================================
        # CÓ ĐƯỜNG TỚI FOOD?
        # =============================================

        food_path = find_path_astar_hard(
            test_snake,
            food
        )

        if food_path is None:

            food_reachable = False
            food_distance = 999

        else:

            food_reachable = True
            food_distance = len(food_path)

        # =============================================
        # KHOẢNG CÁCH FOOD
        # =============================================

        manhattan_food = (
            abs(head[0] - food[0])
            +
            abs(head[1] - food[1])
        ) // CELL

        # =============================================
        # LOOP DETECTION
        # =============================================

        visit_count = recent_positions.count(
            head
        )

        # =============================================
        # SCORE
        # =============================================

        value = 0

        # Không gian
        value += free_space * 10

        # Có đường về đuôi
        if tail_safe:
            value += 3500
        else:
            value -= 2500

        # Có đường tới food
        if food_reachable:

            value += 3000

            value -= food_distance * 12

        else:

            # Không tìm được đường food
            # vẫn phải ưu tiên tiến gần food
            value -= manhattan_food * 15

        # Đi gần food
        value -= manhattan_food * 8

        # =============================================
        # ĐÃ ĂN FOOD
        # =============================================

        if head == food:

            if tail_safe:
                value += 15000
            else:
                value -= 5000

        # =============================================
        # ANTI LOOP
        # =============================================

        value -= visit_count * 4000

        candidates.append(
            (
                value,
                move
            )
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return candidates[0][1]

def get_hard_tail_escape_direction():
    
    if len(snake) <= 2:
        return None

    tail = snake[-1]

    path = find_path_astar_hard(
        snake,
        tail
    )

    if not path:
        return None

    move = get_hard_move_between(
        snake[0],
        path[0]
    )

    if move is None:
        return None

    # Không quay 180°
    if is_opposite_direction(
        move,
        direction
    ):
        return None

    test_snake = simulate_move(
        snake,
        move,
        food,
        "HARD"
    )

    if test_snake is None:
        return None

    return move


def get_hard_ai_direction():
    
    global hard_escape_steps

    head = snake[0]

    # =====================================================
    # PHÁT HIỆN ĐI VÒNG
    # =====================================================

    visit_count = recent_positions.count(
        head
    )

    if visit_count >= 3 and hard_escape_steps == 0:
    
        hard_escape_steps = 6

    # =====================================================
    # ESCAPE MODE
    # =====================================================

    if hard_escape_steps > 0:
        
        # =============================================
        # THỬ TỚI FOOD LẠI TRƯỚC
        # =============================================

        path = find_path_astar_hard(
            snake,
            food
        )

        if path:

            if len(path) <= 60:

                if hard_path_is_safe(path):

                    move = get_hard_move_between(
                        snake[0],
                        path[0]
                    )

                    if (
                        move is not None
                        and
                        not is_opposite_direction(
                            move,
                            direction
                        )
                    ):

                        hard_escape_steps = 0

                        return move

        # =============================================
        # FOOD CHƯA AN TOÀN → ESCAPE
        # =============================================

        escape_move = (
            get_hard_tail_escape_direction()
        )

        if escape_move is not None:

            hard_escape_steps -= 1

            return escape_move

        hard_escape_steps = 0

    # =====================================================
    # 1. A* TỚI FOOD
    # =====================================================

    path = find_path_astar_hard(
        snake,
        food
    )

    if path:

        # Đường không quá dài
        if len(path) <= 100:

            if hard_path_is_safe(path):

                move = get_hard_move_between(
                    snake[0],
                    path[0]
                )

                if move is not None:

                    if not is_opposite_direction(
                        move,
                        direction
                    ):

                        return move

    # =====================================================
    # 2. SURVIVAL AI
    # =====================================================

    survival_move = (
        get_hard_survival_direction()
    )

    if survival_move is not None:

        return survival_move

    # =====================================================
    # 3. HAMILTONIAN FALLBACK
    # =====================================================

    cycle_move = (
        get_cycle_direction_from_head(
            snake[0]
        )
    )

    if not is_opposite_direction(
        cycle_move,
        direction
    ):

        test_snake = simulate_move(
            snake,
            cycle_move,
            food,
            "HARD"
        )

        if test_snake is not None:

            return cycle_move

    # =====================================================
    # 4. LAST RESORT
    # =====================================================

    return find_best_direction(
        snake,
        food,
        direction,
        "HARD",
        recent_positions
    )

def get_hamiltonian_direction():

    """
    HARD AUTO:
    chỉ đi theo Hamiltonian Cycle.
    """

    setup_hamiltonian()

    head = snake[0]

    move = get_cycle_direction_from_head(
        head
    )

    test_snake = simulate_move(
        snake,
        move,
        food,
        game_mode
    )

    if test_snake is None:

        return find_best_direction(
            snake,
            food,
            direction,
            game_mode,
            recent_positions
        )

    return move


def get_normal_shortcut_direction():

    global shortcut_active
    global shortcut_path
    global shortcut_index
    global shortcut_food

    setup_hamiltonian()

    head = snake[0]

    # =====================================================
    # ĐANG THỰC HIỆN SHORTCUT
    # =====================================================

    if shortcut_active:

        # Food đã đổi thì shortcut cũ vô hiệu
        if shortcut_food != food:

            shortcut_active = False
            shortcut_path = []
            shortcut_index = 0
            shortcut_food = None

        elif shortcut_index >= len(
            shortcut_path
        ):

            shortcut_active = False
            shortcut_path = []
            shortcut_index = 0
            shortcut_food = None

        else:

            target = shortcut_path[
                shortcut_index
            ]

            move = get_normal_move_between(
                head,
                target
            )

            if move is not None:

                # Không quay đầu
                if not is_opposite_direction(
                    move,
                    direction
                ):

                    shortcut_index += 1

                    # Đây là bước ăn food
                    if target == food:

                        shortcut_active = False
                        shortcut_path = []
                        shortcut_index = 0
                        shortcut_food = None

                    return move

            # Shortcut bị lỗi -> hủy
            shortcut_active = False
            shortcut_path = []
            shortcut_index = 0
            shortcut_food = None

    # =====================================================
    # CHƯA SHORTCUT -> THỬ TẠO SHORTCUT MỚI
    # =====================================================

    if is_snake_aligned_with_cycle(
        snake
    ):

        new_path = build_safe_shortcut()

        if new_path:

            shortcut_active = True
            shortcut_path = new_path
            shortcut_food = food

            # Bước đầu tiên
            target = shortcut_path[0]

            move = get_normal_move_between(
                head,
                target
            )

            if move is not None:

                if not is_opposite_direction(
                    move,
                    direction
                ):

                    shortcut_index = 1

                    # Shortcut chỉ có 1 bước
                    if target == food:

                        shortcut_active = False
                        shortcut_path = []
                        shortcut_index = 0
                        shortcut_food = None

                    return move

            # Không dùng được shortcut
            shortcut_active = False
            shortcut_path = []
            shortcut_index = 0
            shortcut_food = None

    # =====================================================
    # KHÔNG SHORTCUT -> HAMILTONIAN
    # =====================================================

    return get_hamiltonian_direction()

def draw_game(
    snake,
    food,
    score,
    auto_mode,
    game_mode,
    game_speed

):

    screen.fill(BG)

    # =====================================================
    # GRID
    # =====================================================

    for x in range(
        0,
        WIDTH,
        CELL
    ):

        pygame.draw.line(
            screen,
            GRID,
            (x, 0),
            (x, HEIGHT)
        )

    for y in range(
        0,
        HEIGHT,
        CELL
    ):

        pygame.draw.line(
            screen,
            GRID,
            (0, y),
            (WIDTH, y)
        )

    # =====================================================
    # SNAKE
    # =====================================================

    for index, part in enumerate(snake):

        if index == 0:

            color = GREEN

        else:

            color = DARK_GREEN

        pygame.draw.rect(
            screen,
            color,
            (
                part[0],
                part[1],
                CELL,
                CELL
            )
        )

    # =====================================================
    # FOOD
    # =====================================================

    if food is not None:

        pygame.draw.rect(
            screen,
            RED,
            (
                food[0],
                food[1],
                CELL,
                CELL
            )
        )

    # =====================================================
    # SCORE
    # =====================================================

    score_text = score_font.render(
        f"Score: {score}",
        True,
        WHITE
    )

    screen.blit(
        score_text,
        (10, 8)
    )

    # =====================================================
    # INFO
    # =====================================================

    speed_multiplier = game_speed / 10

    info_text = small_font.render(
        f"{game_mode} | "
        f"{'AUTO' if auto_mode else 'MANUAL'} | "
        f"Speed: x{speed_multiplier:.1f}",
        True,
        WHITE
)

    screen.blit(
        info_text,
        (10, 34)
    )

    # =====================================================
    # AUTO / MANUAL BUTTON
    # =====================================================

    mode_button = pygame.Rect(
        WIDTH - 215,
        10,
        100,
        35
    )

    if auto_mode:

        mode_color = BLUE
        mode_label = "AUTO"

    else:

        mode_color = GREEN
        mode_label = "MANUAL"

    pygame.draw.rect(
        screen,
        mode_color,
        mode_button
    )

    mode_text = button_font.render(
        mode_label,
        True,
        WHITE
    )

    screen.blit(
        mode_text,
        mode_text.get_rect(
            center=mode_button.center
        )
    )

    # =====================================================
    # MENU BUTTON
    # =====================================================

    menu_button = pygame.Rect(
        WIDTH - 105,
        10,
        95,
        35
    )

    pygame.draw.rect(
        screen,
        BLUE,
        menu_button
    )

    menu_text = button_font.render(
        "MENU",
        True,
        WHITE
    )

    screen.blit(
        menu_text,
        menu_text.get_rect(
            center=menu_button.center
        )
    )

    return mode_button, menu_button
# =========================================================
# DRAW PAUSE MENU
# =========================================================

def draw_pause(
    game_mode,
    auto_mode,
    game_speed
):

    overlay = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    overlay.fill(
        (0, 0, 0, 180)
    )

    screen.blit(
        overlay,
        (0, 0)
    )

    # =====================================================
    # TITLE
    # =====================================================

    title = title_font.render(
        "PAUSED",
        True,
        WHITE
    )

    screen.blit(
        title,
        title.get_rect(
            center=(WIDTH // 2, 45)
        )
    )

    info = small_font.render(
        f"{game_mode} | "
        f"{'AUTO' if auto_mode else 'MANUAL'} | "
        f"Speed: x{game_speed / 10:.1f}",
        True,
        GRAY
    )

    screen.blit(
        info,
        info.get_rect(
            center=(WIDTH // 2, 82)
        )
    )

    # =====================================================
    # RESUME
    # =====================================================

    resume_button = pygame.Rect(
        200,
        120,
        200,
        45
    )

    pygame.draw.rect(
        screen,
        GREEN,
        resume_button
    )

    text = button_font.render(
        "RESUME",
        True,
        WHITE
    )

    screen.blit(
        text,
        text.get_rect(
            center=resume_button.center
        )
    )

    # =====================================================
    # AUTO / MANUAL
    # =====================================================

    # =====================================================
    # AUTO / MANUAL
    # =====================================================

    pause_mode_button = pygame.Rect(
        200,
        175,
        200,
        45
    )

    if auto_mode:

        color = BLUE
        label = "AUTO"

    else:

        color = GREEN
        label = "MANUAL"

    pygame.draw.rect(
        screen,
        color,
        pause_mode_button
    )

    text = button_font.render(
        f"MODE: {label}",
        True,
        WHITE
    )

    screen.blit(
        text,
        text.get_rect(
            center=pause_mode_button.center
        )
    )



    # =====================================================
    # MAIN MENU
    # =====================================================

    main_menu_button = pygame.Rect(
        200,
        230,
        200,
        45
    )

    pygame.draw.rect(
        screen,
        BLUE,
        main_menu_button
    )

    text = button_font.render(
        "MAIN MENU",
        True,
        WHITE
    )

    screen.blit(
        text,
        text.get_rect(
            center=main_menu_button.center
        )
    )

    # =====================================================
    # QUIT
    # =====================================================

    quit_button = pygame.Rect(
        200,
        285,
        200,
        45
    )

    pygame.draw.rect(
        screen,
        RED,
        quit_button
    )

    text = button_font.render(
        "QUIT GAME",
        True,
        WHITE
    )

    screen.blit(
        text,
        text.get_rect(
            center=quit_button.center
        )
    )

    return (
        resume_button,
        pause_mode_button,
        main_menu_button,
        quit_button
    )


# =========================================================
# END SCREEN
# =========================================================

def draw_end_screen(
    title_text,
    title_color
):

    screen.fill(BG)

    title = title_font.render(
        title_text,
        True,
        title_color
    )

    screen.blit(
        title,
        title.get_rect(
            center=(WIDTH // 2, 100)
        )
    )

    # =====================================================
    # PLAY AGAIN
    # =====================================================

    play_again_button = pygame.Rect(
        200,
        170,
        200,
        45
    )

    pygame.draw.rect(
        screen,
        GREEN,
        play_again_button
    )

    text = button_font.render(
        "PLAY AGAIN",
        True,
        WHITE
    )

    screen.blit(
        text,
        text.get_rect(
            center=play_again_button.center
        )
    )

    # =====================================================
    # MAIN MENU
    # =====================================================

    main_menu_button = pygame.Rect(
        200,
        230,
        200,
        45
    )

    pygame.draw.rect(
        screen,
        BLUE,
        main_menu_button
    )

    text = button_font.render(
        "MAIN MENU",
        True,
        WHITE
    )

    screen.blit(
        text,
        text.get_rect(
            center=main_menu_button.center
        )
    )

    # =====================================================
    # QUIT
    # =====================================================

    quit_button = pygame.Rect(
        200,
        290,
        200,
        45
    )

    pygame.draw.rect(
        screen,
        RED,
        quit_button
    )

    text = button_font.render(
        "QUIT",
        True,
        WHITE
    )

    screen.blit(
        text,
        text.get_rect(
            center=quit_button.center
        )
    )

    return (
        play_again_button,
        main_menu_button,
        quit_button
    )


# =========================================================
# GAME VARIABLES
# =========================================================

snake, direction, food, score = reset_game()

running = True

menu = True
paused = False
game_over = False
win = False

auto_mode = False
game_speed = 10

game_mode = "NORMAL"
hard_algorithm = "A_STAR"


target_score = 597
input_text = "597"

# AI anti-loop
recent_positions = deque(maxlen=35)

pattern_started = False
pattern_path = []
spiral_phase = "IN"
spiral_clockwise = True

# =========================================================
# MAIN LOOP
# =========================================================

while running:

    # =====================================================
    # MAIN MENU
    # =====================================================

    if menu:

        screen.fill(BG)

        # =================================================
        # TITLE
        # =================================================

        title = title_font.render(
            "SNAKE",
            True,
            GREEN
        )

        screen.blit(
            title,
            title.get_rect(
                center=(WIDTH // 2, 35)
            )
        )

        # =================================================
        # TARGET
        # =================================================

        target_text = score_font.render(
            f"Target Score: {input_text}",
            True,
            WHITE
        )

        screen.blit(
            target_text,
            target_text.get_rect(
                center=(WIDTH // 2, 78)
            )
        )

        max_text = small_font.render(
            f"Enter 1 - {MAX_SCORE}",
            True,
            GRAY
        )

        screen.blit(
            max_text,
            max_text.get_rect(
                center=(WIDTH // 2, 102)
            )
        )

        # =================================================
        # PLAY
        # =================================================

        play_button = pygame.Rect(
            200,
            120,
            200,
            42
        )

        pygame.draw.rect(
            screen,
            GREEN,
            play_button
        )

        text = button_font.render(
            "PLAY",
            True,
            WHITE
        )

        screen.blit(
            text,
            text.get_rect(
                center=play_button.center
            )
        )

        # =================================================
        # AUTO PLAY
        # =================================================

        auto_button = pygame.Rect(
            200,
            168,
            200,
            42
        )

        pygame.draw.rect(
            screen,
            BLUE,
            auto_button
        )

        text = button_font.render(
            "AUTO PLAY",
            True,
            WHITE
        )

        screen.blit(
            text,
            text.get_rect(
                center=auto_button.center
            )
        )

        # =================================================
        # NORMAL
        # =================================================

        normal_button = pygame.Rect(
            100,
            218,
            180,
            42
        )

        if game_mode == "NORMAL":
            
            color = GREEN

        else:

            color = (70, 70, 70)

        pygame.draw.rect(
            screen,
            color,
            normal_button
        )

        text = button_font.render(
            "NORMAL",
            True,
            WHITE
        )

        screen.blit(
            text,
            text.get_rect(
                center=normal_button.center
            )
        )

        # =================================================
        # HARD
        # =================================================

        hard_button = pygame.Rect(
            320,
            218,
            180,
            42
        )

        if game_mode == "HARD":

            color = RED

        else:

            color = (70, 70, 70)

        pygame.draw.rect(
            screen,
            color,
            hard_button
        )

        text = button_font.render(
            "HARD",
            True,
            WHITE
        )

        screen.blit(
            text,
            text.get_rect(
                center=hard_button.center
            )
        )


        # =================================================
        # QUIT
        # =================================================

        quit_button = pygame.Rect(
            200,
            272,
            200,
            42
        )

        pygame.draw.rect(
            screen,
            RED,
            quit_button
        )

        text = button_font.render(
            "QUIT",
            True,
            WHITE
        )

        screen.blit(
            text,
            text.get_rect(
                center=quit_button.center
            )
        )

        # =================================================
        # MENU EVENTS
        # =================================================

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                running = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_BACKSPACE:

                    input_text = input_text[:-1]

                elif event.key == pygame.K_RETURN:

                    if input_text.isdigit():

                        number = int(input_text)

                        if 1 <= number <= MAX_SCORE:

                            target_score = number

                elif event.unicode.isdigit():

                    if len(input_text) < 3:

                        input_text += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN:

                mouse_pos = event.pos

                # PLAY
                if play_button.collidepoint(mouse_pos):

                    if input_text.isdigit():

                        number = int(input_text)

                        if 1 <= number <= MAX_SCORE:

                            target_score = number

                            snake, direction, food, score = reset_game()

                            menu = False
                            paused = False
                            game_over = False
                            win = False
                            auto_mode = False

                            recent_positions.clear()

                # AUTO PLAY
                elif auto_button.collidepoint(mouse_pos):

                    if input_text.isdigit():

                        number = int(input_text)

                        if 1 <= number <= MAX_SCORE:

                            target_score = number

                            snake, direction, food, score = reset_game()

                            menu = False
                            paused = False
                            game_over = False
                            win = False
                            auto_mode = True

                            recent_positions.clear()

                # NORMAL
                elif normal_button.collidepoint(mouse_pos):

                    game_mode = "NORMAL"

                # HARD
                elif hard_button.collidepoint(mouse_pos):

                    game_mode = "HARD"


                # QUIT
                elif quit_button.collidepoint(mouse_pos):

                    running = False

        pygame.display.flip()

        clock.tick(30)

        continue


    # =====================================================
    # GAME OVER
    # =====================================================

    if game_over:

        buttons = draw_end_screen(
            "GAME OVER",
            RED
        )

        play_again_button = buttons[0]
        main_menu_button = buttons[1]
        quit_button = buttons[2]

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:

                mouse_pos = event.pos

                if play_again_button.collidepoint(
                    mouse_pos
                ):

                    snake, direction, food, score = reset_game()

                    game_over = False
                    paused = False
                    win = False

                    recent_positions.clear()

                elif main_menu_button.collidepoint(
                    mouse_pos
                ):

                    snake, direction, food, score = reset_game()

                    menu = True
                    game_over = False
                    paused = False
                    win = False
                    auto_mode = False

                    recent_positions.clear()

                elif quit_button.collidepoint(
                    mouse_pos
                ):

                    running = False

        pygame.display.flip()

        clock.tick(30)

        continue


    # =====================================================
    # WIN
    # =====================================================

    if win:

        buttons = draw_end_screen(
            "YOU WIN!",
            GREEN
        )

        play_again_button = buttons[0]
        main_menu_button = buttons[1]
        quit_button = buttons[2]

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:

                mouse_pos = event.pos

                if play_again_button.collidepoint(
                    mouse_pos
                ):

                    snake, direction, food, score = reset_game()

                    win = False
                    paused = False
                    game_over = False

                    recent_positions.clear()

                elif main_menu_button.collidepoint(
                    mouse_pos
                ):

                    snake, direction, food, score = reset_game()

                    menu = True
                    win = False
                    game_over = False
                    paused = False
                    auto_mode = False

                    recent_positions.clear()

                elif quit_button.collidepoint(
                    mouse_pos
                ):

                    running = False

        pygame.display.flip()

        clock.tick(30)

        continue


    # =====================================================
    # DRAW GAME
    # =====================================================

    mode_button, menu_button = draw_game(
        snake,
        food,
        score,
        auto_mode,
        game_mode,
        game_speed
    )


    # =====================================================
    # PAUSE
    # =====================================================

    if paused:

        buttons = draw_pause(
            game_mode,
            auto_mode,
            game_speed

        )

        (
            resume_button,
            pause_mode_button,
            main_menu_button,
            quit_button
        ) = buttons

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                running = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:

                    paused = False

            elif event.type == pygame.MOUSEBUTTONDOWN:

                mouse_pos = event.pos

                # RESUME
                if resume_button.collidepoint(
                    mouse_pos
                ):

                    paused = False

                # AUTO / MANUAL
                elif pause_mode_button.collidepoint(
                    mouse_pos
                ):

                    auto_mode = not auto_mode

                    recent_positions.clear()


                # MAIN MENU
                elif main_menu_button.collidepoint(
                    mouse_pos
                ):

                    snake, direction, food, score = reset_game()

                    menu = True
                    paused = False
                    game_over = False
                    win = False
                    auto_mode = False

                    recent_positions.clear()

                # QUIT
                elif quit_button.collidepoint(
                    mouse_pos
                ):

                    running = False

        pygame.display.flip()

        clock.tick(30)

        continue


    # =====================================================
    # ACTIVE GAME EVENTS
    # =====================================================

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

        elif event.type == pygame.KEYDOWN:

            # =================================================
            # ESC = PAUSE
            # =================================================

            if event.key == pygame.K_ESCAPE:

                paused = True

                continue
         

            # =================================================
            # SPEED CONTROL - SPACE
            # =================================================


            # =================================================
            # SPEED CONTROL
            # =================================================

            # SPACE = tăng tốc
            if event.key == pygame.K_SPACE:

                game_speed *= 2

                if game_speed > 1000:
                    game_speed = 5

                continue


            # F = giảm tốc
            elif event.key == pygame.K_f:

                game_speed //= 2

                if game_speed < 5:
                    game_speed = 5

                continue

            new_direction = None

            # =================================================
            # WASD + ARROWS
            # =================================================

            if event.key == pygame.K_w or event.key == pygame.K_UP:

                new_direction = (0, -CELL)

            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:

                new_direction = (0, CELL)

            elif event.key == pygame.K_a or event.key == pygame.K_LEFT:

                new_direction = (-CELL, 0)

            elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:

                new_direction = (CELL, 0)

            # =================================================
            # MOVEMENT KEY PRESSED
            # =================================================

            if new_direction is not None:

                # ---------------------------------------------
                # AUTO -> MANUAL
                # ---------------------------------------------

                if auto_mode:

                    auto_mode = False

                    recent_positions.clear()

                # ---------------------------------------------
                # NO 180 DEGREE TURN
                # ---------------------------------------------

                if not (
                    new_direction[0] == -direction[0]
                    and
                    new_direction[1] == -direction[1]
                ):

                    direction = new_direction


        elif event.type == pygame.MOUSEBUTTONDOWN:

            mouse_pos = event.pos

            # =================================================
            # QUICK AUTO / MANUAL
            # =================================================

            if mode_button.collidepoint(
                mouse_pos
            ):

                auto_mode = not auto_mode

                recent_positions.clear()

            # =================================================
            # PAUSE MENU
            # =================================================

            elif menu_button.collidepoint(
                mouse_pos
            ):

                paused = True


    # =====================================================
    # AUTO AI
    # =====================================================

    if auto_mode and not paused:
        
        if game_mode == "NORMAL":

            direction = get_normal_shortcut_direction()

        else:

            direction = get_hard_ai_direction()

    # =====================================================
    # MOVE
    # =====================================================

    if not paused:
        
    # Đảm bảo direction luôn hợp lệ
        if direction is None:
            direction = (CELL, 0)

        new_snake = simulate_move(
            snake,
            direction,
            food,
            game_mode
        )

        # =================================================
        # COLLISION
        # =================================================

        if new_snake is None:

            game_over = True

        else:

            snake = new_snake

            # =================================================
            # EAT FOOD
            # =================================================

            if snake[0] == food:

                score += 1
                hard_escape_steps = 0

                food = create_food(snake)

                # Target reached
                if score >= target_score:

                    win = True

                # Board full
                elif food is None:

                    win = True

            # =================================================
            # AI MEMORY
            # =================================================

            recent_positions.append(
                snake[0]
            )


    pygame.display.flip()

   

    clock.tick(game_speed)


pygame.quit()