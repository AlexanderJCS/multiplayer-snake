import threading
import logging
import random
import pygame
import socket
import json
import time

import gui_text
import ip_connection_screen as connect

from networking import send, receive


logging.basicConfig(
    filename=f"log_{int(time.time())}.txt",
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger()
logger.setLevel(20)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.settimeout(10)

HEADERSIZE = 10

with open("preferences.json") as f:
    SETTINGS = json.load(f)

with open("screen_sizes.json") as f:
    SIZES = json.load(f)

GUI = "small" if SETTINGS.get("small_gui") else "large"

WIDTH = SIZES[GUI]["width"]
PLAYER_OFFSET = SIZES[GUI]["player_offset"]
OPPONENT_OFFSET = SIZES[GUI]["opponent_offset"]
HEIGHT = SIZES[GUI]["height"]

FONT = pygame.font.SysFont("Calibri Light", 30)

SNAKE_COLOR = SETTINGS["snake_color"]
APPLE_COLOR = SETTINGS["apple_color"]

ENDGAME_MESSAGES = {
    "won": "You lost.",
    "lost": "You won!",
    "Client disconnected": "Enemy left."
}


pygame.init()


class Cube:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color

    def draw(self, surface, board_size, y_offset) -> None:
        if self.x < 0 or self.x >= board_size or self.y < 0 or self.y >= board_size:
            return

        dist = WIDTH // board_size

        x = self.x
        y = self.y

        pygame.draw.rect(surface, self.color, (x * dist + 1, y * dist + y_offset + 1, dist - 2, dist - 2))


class Snake:
    def __init__(self, default_coords):
        self.coords = [Cube(coord[0], coord[1], SNAKE_COLOR) for coord in default_coords]
        self.dir = (0, 0)
        self.pop = True  # pop the end of the snake when moving, used for eating an apple
        self.prev_frame_dir = (0, 0)

    def get_input(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] and self.prev_frame_dir != (1, 0):
            self.dir = (-1, 0)

        elif keys[pygame.K_RIGHT] and self.prev_frame_dir != (-1, 0):
            self.dir = (1, 0)

        elif keys[pygame.K_UP] and self.prev_frame_dir != (0, 1):
            self.dir = (0, -1)

        elif keys[pygame.K_DOWN] and self.prev_frame_dir != (0, -1):
            self.dir = (0, 1)

    def check_apple_eaten(self, apple) -> bool:
        apple_x, apple_y = apple.get_xy()

        if self.coords[-1].x == apple_x and self.coords[-1].y == apple_y:
            self.pop = False
            return True

        return False

    def move(self) -> None:
        self.coords.append(Cube(self.coords[-1].x + self.dir[0],
                                self.coords[-1].y + self.dir[1],
                                SNAKE_COLOR))

        if self.pop:
            self.coords.pop(0)

        self.pop = True
        self.prev_frame_dir = self.dir

    def draw_snake(self, surface, board_size, y_offset=0) -> None:
        for cube in self.coords:
            cube.draw(surface, board_size, y_offset)

    def won(self, win_len) -> bool:
        return len(self.coords) >= win_len

    def lost(self, board_size) -> bool:
        head = self.coords[-1]

        if head.x >= board_size or head.x < 0 or head.y >= board_size or head.y < 0:
            return True

        for i, block in enumerate(self.coords):
            if i == len(self.coords) - 1:  # skip the head
                continue

            if block.x == head.x and block.y == head.y:  # if a block intersects the head
                return True

        return False


class Apple:
    def __init__(self, start_x=0, start_y=0):
        self.cube = Cube(start_x, start_y, APPLE_COLOR)

    """
    Draws the cube on the given surface
    
    surface: surface
    board_size: the board's width (width dimensions are the same as height dimensions)
    y_offset: the offest in pixels of the board, higher = lower on the screen
    """
    def draw(self, surface, board_size, y_offset) -> None:
        self.cube.draw(surface, board_size, y_offset)

    """
    Returns the x and y coordinates of the cube
    """
    def get_xy(self) -> tuple:
        return self.cube.x, self.cube.y

    """
    Find new coords for the apple
    
    snake: the snake Cube object array
    board_size: The width of the board (height is the same as the width)
    """
    def regenerate_coords(self, snake, board_size: int) -> None:
        while True:
            x = random.randint(0, board_size - 1)
            y = random.randint(0, board_size - 1)

            for block in snake.coords:
                if block.x == x and block.y == y:
                    break

            else:  # nobreak
                self.cube.x = x
                self.cube.y = y
                return


class Game:
    def __init__(self, surface):
        self.board_size = receive(client_socket)
        self.speed = receive(client_socket)
        self.apple_goal = receive(client_socket)

        self.snake = Snake([(self.board_size // 2, self.board_size // 2)])
        self.apple = Apple(2, 2)

        self.opponent_board = []

        self.surface = surface

        self.your_board_text = gui_text.Text("Your board:", FONT, (255, 255, 255), (60, PLAYER_OFFSET // 2))
        self.opponent_board_text = gui_text.Text("Enemy board:", FONT, (255, 0, 0), (70, HEIGHT - WIDTH - 30))
        self.score_text = gui_text.Text("Score: 1", FONT, (255, 255, 255), (WIDTH - 70, PLAYER_OFFSET // 2))
        self.opponent_score_text = gui_text.Text("Enemy Score: 1", FONT, (255, 0, 0),
                                                 (WIDTH - 70, OPPONENT_OFFSET - 30))

    """
    Draw the grid for the snake board.
    
    y_offset (optional parameter): the y offset of the board, higher = lower on the screen
    """
    def draw_grid(self, y_offset=0) -> None:
        size_between = WIDTH // self.board_size

        x = 0
        y = y_offset

        for _ in range(self.board_size + 1):
            # Draw vertical lines
            pygame.draw.line(self.surface, (100, 100, 100),
                             (x, y_offset),
                             (x, self.board_size * size_between + y_offset))

            # Draw horizontal lines
            pygame.draw.line(self.surface, (100, 100, 100), (0, y), (WIDTH, y))

            x += size_between
            y += size_between

    """
    Give essential data for the snake position and apple position to the server
    """
    def send_screen_info(self) -> None:
        pos_data = [(cube.x, cube.y, SNAKE_COLOR) for cube in self.snake.coords]
        pos_data.insert(0, (self.apple.cube.x, self.apple.cube.y, (255, 0, 0)))
        send(pos_data, client_socket)

    """
    Receive the other player's board
    """
    def get_other_board(self) -> None:
        self.opponent_board = receive(client_socket)

    """
    Draws the opponent board at the offest OPPONENT_OFFEST. This can be configured in screen_sizes.json.
    """
    def draw_opponent_board(self) -> None:
        self.draw_grid(OPPONENT_OFFSET)

        opponent_cubes = [Cube(*pos_data) for pos_data in self.opponent_board]

        for cube in opponent_cubes:
            cube.draw(self.surface, self.board_size, OPPONENT_OFFSET)

    """
    Draws the text on the screen.
    """
    def draw_text(self) -> None:
        self.score_text.change_text(f"Score: {len(self.snake.coords)} / {self.apple_goal}")
        self.opponent_score_text.change_text(f"Score: {len(self.opponent_board) - 1} / {self.apple_goal}")

        self.your_board_text.draw(self.surface)
        self.opponent_board_text.draw(self.surface)
        self.score_text.draw(self.surface)
        self.opponent_score_text.draw(self.surface)

    """
    Returns if the opponent ended the game (either if they won or lost)
    """
    def check_endgame(self) -> bool:
        return type(self.opponent_board) == str

    """
    Show the end screen.
    
    message: The message that should be displayed
    color: The color of the message text
    """
    def show_end_screen(self, message, color) -> None:
        self.surface.fill((0, 0, 0))

        self.draw_grid(OPPONENT_OFFSET)
        self.snake.draw_snake(self.surface, self.board_size, OPPONENT_OFFSET)
        self.apple.draw(self.surface, self.board_size, OPPONENT_OFFSET)

        font = pygame.font.SysFont("Calibri Light", 40)
        text = font.render(message, True, color)

        text_rect = text.get_rect()
        text_rect.center = (WIDTH // 2, HEIGHT - WIDTH - 50)

        self.surface.blit(text, text_rect)

        pygame.display.update()

        pygame.time.wait(3000)

    """
    Main game loop. The loop runs in the order of:
    1. Get input and move the snake
    2. Check if an apple is eaten
    3. Draw the board
    4. Check if the game ended from the opponent winning/losing
    5. Draw the opponent board
    6. Check if the client won/lost
    7. Start the send/receive threads again for less latency
    """
    def run(self) -> None:
        clock = pygame.time.Clock()

        receive_thread = threading.Thread(target=self.get_other_board)
        receive_thread.start()

        send_thread = threading.Thread(target=self.send_screen_info)
        send_thread.start()

        frame_count = 0

        while True:
            # Wait until the game ticks
            if frame_count != self.speed:
                self.snake.get_input()

                frame_count += 1
                clock.tick(60)
                continue

            # Move
            self.snake.get_input()
            self.snake.move()

            # Check if the apple is eaten
            if self.snake.check_apple_eaten(self.apple):
                self.apple.regenerate_coords(self.snake, self.board_size)

            # Draw the board
            self.surface.fill((0, 0, 0))
            self.draw_grid(PLAYER_OFFSET)
            self.draw_text()

            self.apple.draw(self.surface, self.board_size, PLAYER_OFFSET)
            self.snake.draw_snake(self.surface, self.board_size, PLAYER_OFFSET)

            receive_thread.join()
            send_thread.join()

            # Check if the opponent won/lost
            if self.opponent_board == "Client disconnected":
                self.show_end_screen(ENDGAME_MESSAGES[self.opponent_board], (255, 255, 255))
                pygame.quit()
                exit()

            if self.check_endgame() is True:
                self.show_end_screen(ENDGAME_MESSAGES[self.opponent_board], (255, 255, 255))
                break

            # Draw the opponent board
            self.draw_opponent_board()

            # Check if the snake won or lost
            if self.snake.won(self.apple_goal):
                send("won", client_socket)
                self.show_end_screen(f"You won with a score of {len(self.snake.coords)}!", (0, 255, 0))
                break

            elif self.snake.lost(self.board_size):
                send("lost", client_socket)
                self.show_end_screen(f"You lost with a score of {len(self.snake.coords)}.", (255, 0, 0))
                break

            pygame.display.update()

            receive_thread = threading.Thread(target=self.get_other_board)
            receive_thread.start()

            send_thread = threading.Thread(target=self.send_screen_info)
            send_thread.start()

            frame_count = 0
            clock.tick(60)

        send_thread.join()
        receive_thread.join()


def main():
    global client_socket

    # Setup pygame
    pygame.display.set_caption("Multiplayer Snake")
    surface = pygame.display.set_mode((WIDTH, HEIGHT))

    # Run the IP connection screen
    conn = connect.IPConnectionScreen(surface, WIDTH, PLAYER_OFFSET, client_socket)

    while True:
        connected = conn.run()

        if connected:
            break

        # Reset the client socket to avoid errors if the connection failed
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn = connect.IPConnectionScreen(surface, WIDTH, PLAYER_OFFSET, client_socket, "Failed")

    client_socket.settimeout(1000)

    # Run the game
    while True:
        game = Game(surface)

        client_socket.settimeout(5)

        game.run()

        send("ready", client_socket)
        send("ready2", client_socket)

        # Clear all pending messages from the server before replaying
        client_socket.settimeout(1000)

        while receive(client_socket) != "start":
            pass


if __name__ == "__main__":
    main()
