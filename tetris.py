import pygame
import random

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 300
SCREEN_HEIGHT = 600
BLOCK_SIZE = 30
NEXT_BLOCK_WIDTH = 4  # Width of the next block preview
NEXT_BLOCK_HEIGHT = 4  # Height of the next block preview
PREVIEW_OFFSET_X = 320  # Horizontal offset for the next block preview
HOLD_OFFSET_X = 320  # Horizontal offset for the hold piece display
HOLD_OFFSET_Y = 400  # Vertical offset for the hold piece display

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
COLORS = [
    (0, 255, 255),  # Cyan
    (255, 255, 0),  # Yellow
    (255, 165, 0),  # Orange
    (0, 0, 255),    # Blue
    (0, 255, 0),    # Green
    (128, 0, 128),  # Purple
    (255, 0, 0)     # Red
]

# Shapes and their rotations
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 0, 1]],  # J
    [[1, 1], [1, 1]],  # O
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 0], [0, 1, 1]]   # Z
]

# Wall kick tests for each rotation state
WALL_KICK_TESTS = [
    [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2), (1, 0), (1, -1), (0, 2), (1, 2)], # 0 -> 1
    [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2), (-1, 0), (-1, 1), (0, -2), (-1, -2)], # 1 -> 0
    [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2), (-1, 0), (-1, -1), (0, -2), (-1, 2)], # 1 -> 2
    [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2), (1, 0), (1, 1), (0, 2), (1, -2)], # 2 -> 1
    [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2), (-1, 0), (-1, -1), (0, 2), (-1, 2)], # 2 -> 3
    [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2), (1, 0), (1, 1), (0, -2), (1, -2)], # 3 -> 2
    [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2), (1, 0), (1, -1), (0, -2), (1, 2)], # 3 -> 0
    [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2), (-1, 0), (-1, 1), (0, 2), (-1, -2)]  # 0 -> 3
]

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH + 160, SCREEN_HEIGHT))  # Increase screen width to fit the preview
pygame.display.set_caption("Tetris")

# Clock
clock = pygame.time.Clock()

# Grid
grid = [[0 for _ in range(SCREEN_WIDTH // BLOCK_SIZE)] for _ in range(SCREEN_HEIGHT // BLOCK_SIZE)]

# Lock delay settings
LOCK_DELAY_TIME = 500  # Delay in milliseconds before the block is locked in place

# Score and level
score = 0
level = 1
lines_cleared_total = 0

# Hold piece
hold_piece = None  # Initially, no piece is held
can_hold = True  # Whether the player can hold a piece (resets after placing a piece)

# Pause state
paused = False

# Load music
pygame.mixer.music.load('C:/Users/kenny/OneDrive/Desktop/Python Projects/Projects/tetris/tetris_theme.mp3')  # Replace with the path to your music file
pygame.mixer.music.set_volume(0.022)  # Set the volume (optional)

# Load sound effect for clearing lines
line_clear_sound = pygame.mixer.Sound('C:/Users/kenny/OneDrive/Desktop/Python Projects/Projects/tetris/line_clear.mp3')  # Replace with the path to your sound file
line_clear_sound.set_volume(0.08)

def draw_grid():
    for y in range(len(grid)):
        for x in range(len(grid[y])):
            if grid[y][x]:
                pygame.draw.rect(screen, COLORS[grid[y][x] - 1], (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))

def draw_borders():
    """Draw borders around the play area."""
    border_thickness = 2  # Thickness of the border lines
    # Left border
    pygame.draw.rect(screen, WHITE, (0, 0, border_thickness, SCREEN_HEIGHT))
    # Right border
    pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH - border_thickness, 0, border_thickness, SCREEN_HEIGHT))
    # Bottom border
    pygame.draw.rect(screen, WHITE, (0, SCREEN_HEIGHT - border_thickness, SCREEN_WIDTH, border_thickness))

def new_piece():
    shape = random.choice(SHAPES)
    color = random.randint(1, len(COLORS))
    return {
        'shape': shape,
        'color': color,
        'x': SCREEN_WIDTH // BLOCK_SIZE // 2 - len(shape[0]) // 2,
        'y': 0,
        'rotation_state': 0  # Track the rotation state of the piece
    }

def draw_piece(piece):
    for y, row in enumerate(piece['shape']):
        for x, cell in enumerate(row):
            if cell:
                pygame.draw.rect(screen, COLORS[piece['color'] - 1], ((piece['x'] + x) * BLOCK_SIZE, (piece['y'] + y) * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))

def draw_ghost(piece):
    ghost_piece = piece.copy()
    while not check_collision(ghost_piece, dy=1):
        ghost_piece['y'] += 1

    # Draw the outline of the ghost piece with the original color
    for y, row in enumerate(ghost_piece['shape']):
        for x, cell in enumerate(row):
            if cell:
                pygame.draw.rect(screen, COLORS[piece['color'] - 1], ((ghost_piece['x'] + x) * BLOCK_SIZE, (ghost_piece['y'] + y) * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 3)  # Draw only the outline with the block's color

def draw_next_piece(next_piece):
    """Draw the next piece in a small box to the right of the game area."""
    start_x = PREVIEW_OFFSET_X + (NEXT_BLOCK_WIDTH * BLOCK_SIZE - len(next_piece['shape'][0]) * BLOCK_SIZE * 0.7) // 2
    start_y = 100 + (NEXT_BLOCK_HEIGHT * BLOCK_SIZE - len(next_piece['shape']) * BLOCK_SIZE * 0.7) // 2
    for y, row in enumerate(next_piece['shape']):
        for x, cell in enumerate(row):
            if cell:
                pygame.draw.rect(screen, COLORS[next_piece['color'] - 1], (start_x + x * BLOCK_SIZE * 0.7, start_y + y * BLOCK_SIZE * 0.7, BLOCK_SIZE * 0.7, BLOCK_SIZE * 0.7))
    pygame.draw.rect(screen, WHITE, (PREVIEW_OFFSET_X - 5, 100 - 5, NEXT_BLOCK_WIDTH * BLOCK_SIZE + 10, NEXT_BLOCK_HEIGHT * BLOCK_SIZE + 10), 2)  # Box around the next piece

def draw_hold_piece(hold_piece):
    """Draw the held piece in a small box to the right of the game area."""
    start_x = HOLD_OFFSET_X
    start_y = HOLD_OFFSET_Y
    font = pygame.font.SysFont('Courier New', 15)
    hold_text = font.render('Hold (C)', True, WHITE)
    screen.blit(hold_text, (HOLD_OFFSET_X, HOLD_OFFSET_Y - 30))

    if hold_piece:
        start_x += (NEXT_BLOCK_WIDTH * BLOCK_SIZE - len(hold_piece['shape'][0]) * BLOCK_SIZE * 0.7) // 2
        start_y += (NEXT_BLOCK_HEIGHT * BLOCK_SIZE - len(hold_piece['shape']) * BLOCK_SIZE * 0.7) // 2
        for y, row in enumerate(hold_piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(screen, COLORS[hold_piece['color'] - 1], (start_x + x * BLOCK_SIZE * 0.7, start_y + y * BLOCK_SIZE * 0.7, BLOCK_SIZE * 0.7, BLOCK_SIZE * 0.7))

    pygame.draw.rect(screen, WHITE, (HOLD_OFFSET_X - 5, HOLD_OFFSET_Y - 5, NEXT_BLOCK_WIDTH * BLOCK_SIZE + 10, NEXT_BLOCK_HEIGHT * BLOCK_SIZE + 10), 2)  # Box around the hold piece

def draw_score_and_level():
    """Draw the score and level below the next block preview."""
    font = pygame.font.SysFont('Courier New', 20)
    score_text = font.render(f"Score: {score}", True, WHITE)
    level_text = font.render(f"Level: {level}", True, WHITE)
    screen.blit(score_text, (PREVIEW_OFFSET_X, 250))
    screen.blit(level_text, (PREVIEW_OFFSET_X, 300))

def check_collision(piece, dx=0, dy=0):
    for y, row in enumerate(piece['shape']):
        for x, cell in enumerate(row):
            if cell:
                new_x = piece['x'] + x + dx
                new_y = piece['y'] + y + dy
                if new_x < 0 or new_x >= len(grid[0]) or new_y >= len(grid) or (new_y >= 0 and (grid[new_y][new_x])):
                    return True
    return False

def merge_piece(piece):
    for y, row in enumerate(piece['shape']):
        for x, cell in enumerate(row):
            if cell:
                grid[piece['y'] + y][piece['x'] + x] = piece['color']

def clear_lines():
    global score, level, lines_cleared_total
    lines_cleared = 0
    for y in range(len(grid)):
        if all(grid[y]):
            del grid[y]
            grid.insert(0, [0 for _ in range(len(grid[0]))])
            lines_cleared += 1

    if lines_cleared > 0:
        # Play the line clear sound effect
        line_clear_sound.play()
        # Update score based on the number of lines cleared
        score += lines_cleared * 100 * level
        lines_cleared_total += lines_cleared
        # Increase level every 10 lines cleared
        if lines_cleared_total >= 10:
            level += 1
            lines_cleared_total -= 10
    return lines_cleared

def game_over():
    global score, level, lines_cleared_total, grid, piece, next_piece, fall_time, fall_speed, is_locked, lock_delay, hold_piece, can_hold

    font = pygame.font.SysFont('Courier New', 25)  # Smaller font size
    text = font.render('Game Over', True, WHITE)
    restart_text = font.render('Press R to Restart', True, WHITE)
    screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - text.get_height() // 2))
    screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))
    pygame.display.update()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Restart the game
                    # Reset game state
                    grid = [[0 for _ in range(SCREEN_WIDTH // BLOCK_SIZE)] for _ in range(SCREEN_HEIGHT // BLOCK_SIZE)]
                    score = 0
                    level = 1
                    lines_cleared_total = 0
                    piece = new_piece()
                    next_piece = new_piece()
                    fall_time = 0
                    fall_speed = 500
                    is_locked = False
                    lock_delay = 0
                    hold_piece = None
                    can_hold = True
                    return  # Exit the game_over function and restart the game

def main():
    global score, level, lines_cleared_total, grid, piece, next_piece, fall_time, fall_speed, is_locked, lock_delay, hold_piece, can_hold, paused

    while True:  # Outer loop to restart the game
        piece = new_piece()
        next_piece = new_piece()  # Generate the next piece
        fall_time = 0
        normal_fall_speed = 500  # Default fall speed in milliseconds
        fast_fall_speed = 100  # Speed when down key or 'S' is pressed
        fall_speed = normal_fall_speed  # Initial fall speed
        running = True

        move_time = 0  # Track time between movements
        move_delay = 175  # Delay in milliseconds to control movement speed

        lock_delay = 0  # Track time since the block landed
        is_locked = False  # Whether the block is in the lock delay phase

        pygame.mixer.music.play(-1)  # Start playing the music in a loop

        while running:
            screen.fill(BLACK)
            draw_grid()
            draw_borders()  # Draw borders around the play area
            draw_ghost(piece)  # Draw ghost piece
            draw_piece(piece)
            draw_next_piece(next_piece)  # Draw the next piece preview
            draw_hold_piece(hold_piece)  # Draw the held piece
            draw_score_and_level()  # Draw the score and level

            if paused:
                pause_font = pygame.font.SysFont('Courier New', 50)
                pause_text = pause_font.render('Paused', True, WHITE)
                screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, SCREEN_HEIGHT // 2 - pause_text.get_height() // 2))
                pygame.display.update()
                while paused:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            return
                        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                            paused = False
                continue

            keys = pygame.key.get_pressed()

            # Control movement speed
            if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and move_time >= move_delay:
                if not check_collision(piece, dx=-1):
                    piece['x'] -= 1
                move_time = 0  # Reset move time after moving
            if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and move_time >= move_delay:
                if not check_collision(piece, dx=1):
                    piece['x'] += 1
                move_time = 0  # Reset move time after moving

            # Key events (rotation, instant drop, and hold)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        paused = not paused
                    if event.key in (pygame.K_UP, pygame.K_w):
                        original_rotation_state = piece['rotation_state']
                        rotated_shape = list(zip(*reversed(piece['shape'])))
                        new_rotation_state = (piece['rotation_state'] + 1) % 4
                        for dx, dy in WALL_KICK_TESTS[original_rotation_state]:
                            if not check_collision({'shape': rotated_shape, 'x': piece['x'] + dx, 'y': piece['y'] + dy, 'color': piece['color']}):
                                piece['shape'] = rotated_shape
                                piece['x'] += dx
                                piece['y'] += dy
                                piece['rotation_state'] = new_rotation_state
                                break
                    # Instant drop when spacebar is pressed
                    if event.key == pygame.K_SPACE:
                        while not check_collision(piece, dy=1):  # Keep moving the piece down until it collides
                            piece['y'] += 1
                        merge_piece(piece)
                        lines_cleared = clear_lines()
                        if lines_cleared:
                            fall_speed = max(fast_fall_speed, fall_speed - 50 * lines_cleared)
                        piece = next_piece  # Get the new piece
                        next_piece = new_piece()  # Generate the next piece
                        if check_collision(piece):
                            game_over()
                            running = False
                        can_hold = True  # Reset hold ability after placing a piece
                    # Hold piece when 'C' is pressed
                    if event.key == pygame.K_c and can_hold:
                        if hold_piece is None:
                            hold_piece = {'shape': piece['shape'], 'color': piece['color']}
                            piece = next_piece
                            next_piece = new_piece()
                        else:
                            # Swap current piece with held piece
                            temp_piece = piece
                            piece = {'shape': hold_piece['shape'], 'color': hold_piece['color'], 'x': SCREEN_WIDTH // BLOCK_SIZE // 2 - len(hold_piece['shape'][0]) // 2, 'y': 0, 'rotation_state': 0}
                            hold_piece = {'shape': temp_piece['shape'], 'color': temp_piece['color']}
                        can_hold = False  # Disable hold until the next piece is placed

            # Adjust fall speed when down arrow or 'S' is pressed
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                fall_speed = fast_fall_speed  # Speed up falling when key is pressed
            else:
                fall_speed = max(50, normal_fall_speed - (level - 1) * 50)  # Default speed adjusted by level

            fall_time += clock.get_rawtime()
            clock.tick()

            if fall_time >= fall_speed:
                if not check_collision(piece, dy=1):
                    piece['y'] += 1
                    fall_time = 0
                    is_locked = False  # Reset lock delay if the block moves down
                else:
                    if not is_locked:
                        is_locked = True
                        lock_delay = 0  # Start the lock delay timer
                    else:
                        lock_delay += clock.get_rawtime()
                        if lock_delay >= LOCK_DELAY_TIME:
                            merge_piece(piece)
                            lines_cleared = clear_lines()
                            if lines_cleared:
                                fall_speed = max(fast_fall_speed, fall_speed - 50 * lines_cleared)
                            piece = next_piece  # Get the new piece
                            next_piece = new_piece()  # Generate the next piece
                            if check_collision(piece):
                                game_over()
                                running = False
                            is_locked = False  # Reset lock delay
                            can_hold = True  # Reset hold ability after placing a piece

            # Increase move time to simulate movement delay
            move_time += clock.get_rawtime()

            pygame.display.update()

if __name__ == "__main__":
    main()
