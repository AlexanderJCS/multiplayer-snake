import logging
import random
import pygame
import socket
import json

IP = input("IP: ")
PORT = int(input("Port: "))

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))


HEADERSIZE = 10
WIDTH = 400
PLAYER_OFFSET = 50
OPPONENT_OFFSET = 500 + PLAYER_OFFSET
HEIGHT = 950


logging.basicConfig(
    level=logging.DEBUG
)


ENDGAME_MESSAGES = {
    "won": "You lost.",
    "lost": "You won!",
    "Client disconnected": "Opponent disconnected. You win."
}

ENDGAME_COLOR = {
    "won": (0, 255, 0),
    "lost": (255, 0, 0),
    "Client disconnected": (0, 255, 0)
}


pygame.init()


def send(message):
    message = json.dumps(message, ensure_ascii=False).encode("utf-8")
    header_info = f"{len(message):<{HEADERSIZE}}".encode("utf-8")
    client_socket.send(header_info)
    client_socket.send(message)


def receive():
    message_length = client_socket.recv(HEADERSIZE)

    if message_length == b"":
        print("Server unexpectedly disconnected")
        exit()

    message = client_socket.recv(int(message_length))

    return json.loads(message)


class Cube:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color

    def draw(self, surface, board_size, y_offset):
        if self.x < 0 or self.x >= board_size or self.y < 0 or self.y >= board_size:
            return

        dist = WIDTH // board_size

        x = self.x
        y = self.y

        pygame.draw.rect(surface, self.color, (x * dist + 1, y * dist + y_offset + 1, dist - 2, dist - 2))


class Snake:
    def __init__(self, default_coords):
        self.coords = [Cube(coord[0], coord[1], (0, 155, 255)) for coord in default_coords]
        self.dir = (0, 0)
        self.pop = True  # pop the end of the snake when moving, used for eating an apple

    def get_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] and self.dir != (1, 0):
            self.dir = (-1, 0)

        elif keys[pygame.K_RIGHT] and self.dir != (-1, 0):
            self.dir = (1, 0)

        elif keys[pygame.K_UP] and self.dir != (0, -1):
            self.dir = (0, -1)

        elif keys[pygame.K_DOWN] and self.dir != (0, 1):
            self.dir = (0, 1)

    def check_apple_eaten(self, apple):
        apple_x, apple_y = apple.get_xy()

        if self.coords[-1].x == apple_x and self.coords[-1].y == apple_y:
            self.pop = False
            return True

        return False

    def move(self):
        self.coords.append(Cube(self.coords[-1].x + self.dir[0],
                                self.coords[-1].y + self.dir[1],
                                (0, 155, 255)))

        if self.pop:
            self.coords.pop(0)

        self.pop = True

    def draw_snake(self, surface, board_size, y_offset=0):
        for cube in self.coords:
            cube.draw(surface, board_size, y_offset)

    def won(self, win_len):
        return len(self.coords) >= win_len

    def lost(self, board_size):
        if self.coords[0].x >= board_size or self.coords[0].x < 0 or \
                self.coords[0].y >= board_size or self.coords[0].y < 0:
            return True

        for i, block in enumerate(self.coords):
            if i == 0:
                continue

            if block.x == self.coords[0].x and block.y == self.coords[0].y:
                return True

        return False


class Apple:
    def __init__(self, start_x=0, start_y=0):
        self.cube = Cube(start_x, start_y, (255, 0, 0))

    def draw(self, surface, board_size, y_offset):
        self.cube.draw(surface, board_size, y_offset)

    def get_xy(self):
        return self.cube.x, self.cube.y

    def regenerate_coords(self, snake, board_size):
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
    def __init__(self):
        self.board_size = receive()
        self.speed = receive()
        self.apple_goal = receive()

        self.snake = Snake([(self.board_size // 2, self.board_size // 2)])
        self.apple = Apple(2, 2)

        self.other_board = []

        self.surface = pygame.display.set_mode((WIDTH, HEIGHT))

    def draw_grid(self, y_offset=0):
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

    def send_screen_info(self):
        # Give essential data for the snake position
        pos_data = [(cube.x, cube.y, (0, 155, 255)) for cube in self.snake.coords]
        pos_data.insert(0, (self.apple.cube.x, self.apple.cube.y, (255, 0, 0)))
        send(pos_data)

    def get_other_board(self):
        self.other_board = receive()

    def draw_opponent_board(self):
        self.draw_grid(OPPONENT_OFFSET)

        opponent_cubes = [Cube(*pos_data) for pos_data in self.other_board]

        for cube in opponent_cubes:
            cube.draw(self.surface, self.board_size, OPPONENT_OFFSET)

    def draw_text(self):
        font = pygame.font.SysFont("Calibri Light", 30)

        text = font.render("Your board:", True, (255, 255, 255))
        opponent_text = font.render("Opponent's board:", True, (255, 0, 0))

        opponent_text_rect = opponent_text.get_rect()
        opponent_text_rect.center = (WIDTH // 2, HEIGHT - WIDTH - 30)

        text_rect = text.get_rect()
        text_rect.center = (WIDTH // 2, PLAYER_OFFSET // 2)

        self.surface.blit(text, text_rect)
        self.surface.blit(opponent_text, opponent_text_rect)

    def check_endgame(self):
        # The Pycharm warning can be ignored

        if type(self.other_board) != str or not ENDGAME_MESSAGES.get(self.other_board):
            return

        print(ENDGAME_MESSAGES[self.other_board])
        self.show_end_screen(ENDGAME_MESSAGES[self.other_board], ENDGAME_COLOR[self.other_board])

    def show_end_screen(self, message, color):
        self.surface.fill((0, 0, 0))

        self.draw_grid(OPPONENT_OFFSET)
        self.snake.draw_snake(self.surface, self.board_size, OPPONENT_OFFSET)
        self.apple.draw(self.surface, self.board_size, OPPONENT_OFFSET)

        font = pygame.font.SysFont("Calibri Light", 50)
        text = font.render(message, True, color)

        text_rect = text.get_rect()
        text_rect.center = (WIDTH // 2, HEIGHT - WIDTH - 50)

        self.surface.blit(text, text_rect)

        pygame.display.update()

        pygame.time.wait(5000)
        pygame.quit()
        exit()

    def run(self):
        clock = pygame.time.Clock()

        while True:
            self.surface.fill((0, 0, 0))

            self.snake.get_input()

            if self.snake.check_apple_eaten(self.apple):
                self.apple.regenerate_coords(self.snake, self.board_size)

            self.snake.move()

            self.draw_grid(PLAYER_OFFSET)
            self.draw_text()
            self.apple.draw(self.surface, self.board_size, PLAYER_OFFSET)
            self.snake.draw_snake(self.surface, self.board_size, PLAYER_OFFSET)

            self.send_screen_info()
            self.get_other_board()

            self.check_endgame()
            self.draw_opponent_board()

            if self.snake.won(self.apple_goal):
                send("won")
                self.show_end_screen("You won!", (0, 255, 0))

            elif self.snake.lost(self.board_size):
                send("lost")
                self.show_end_screen("You lost.", (255, 0, 0))

            pygame.display.update()
            pygame.time.delay(self.speed)
            clock.tick(self.speed)


def main():
    pygame.display.set_caption("Multiplayer Snake")

    game = Game()
    game.run()


if __name__ == "__main__":
    main()
