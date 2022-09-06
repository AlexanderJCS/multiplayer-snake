import threading
import socket
import json

IP = socket.gethostbyname(socket.gethostname())
PORT = 9850

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP, PORT))
server_socket.listen(2)

HEADERSIZE = 10


with open("preferences.json") as f:
    OPTIONS = json.load(f)


def send(client, message):  # returns: whether the message was sent
    message = json.dumps(message, ensure_ascii=False).encode("utf-8")
    header_info = f"{len(message):<{HEADERSIZE}}".encode("utf-8")

    try:
        client.clientsocket.send(header_info)
        client.clientsocket.send(message)
        return True

    except ConnectionResetError:
        return False


def receive(client):
    header = client.clientsocket.recv(HEADERSIZE)
    if header == b"":
        return "Client disconnected"

    message_length = int(header.decode('utf-8').strip())
    message = client.clientsocket.recv(message_length)

    return json.loads(message)


class Client:
    def __init__(self, clientsocket, ip):
        self.clientsocket = clientsocket
        self.ip = ip


class GameSetup:
    def __init__(self, clients):
        self.clients = clients
        self.board_size = OPTIONS["board_size"]  # board_size x board_size board
        self.speed = OPTIONS["speed"]  # server tickrate and movement speed, lower = faster
        self.apple_goal = OPTIONS["apple_goal"]  # how long your snake needs to be to win

    def wait_for_players(self):
        while len(self.clients) < 2:
            clientsocket, address = server_socket.accept()
            print(f"Accepted client with address {address}")
            self.clients.append(Client(clientsocket, address))

        print("Starting game")

    def give_start_info(self):
        # Give the start info to the clients
        # Order is: "start", board_size, speed, apple_goal

        print("Giving start info")
        for client in self.clients:
            send(client, "start")
            send(client, self.board_size)
            send(client, self.speed)
            send(client, self.apple_goal)

    def setup(self):
        self.wait_for_players()
        self.give_start_info()

        return self.clients


class Game:
    def __init__(self, clients):
        self.clients = clients
        self.ended = False

    @staticmethod
    def determine_won_lost(snake):
        if len(snake) > OPTIONS["apple_goal"]:
            return "won"

        if snake[-1][0] >= OPTIONS["board_size"] or snake[-1][1] >= OPTIONS["board_size"] or \
                snake[-1][0] < 0 or snake[-1][1] < 0:
            return "lost"

        for i, cube in enumerate(snake):
            if i == len(snake) - 1:
                continue

            if cube == snake[-1]:
                return "lost"

        return ""

    def get_player_screen(self, giver, recipient):
        while not self.ended:
            screen = receive(giver)

            # If the player won or lost
            if result := self.determine_won_lost(screen):
                send(recipient, result)
                self.ended = True

            send(recipient, screen)

    def run(self):
        t1 = threading.Thread(target=self.get_player_screen, args=(self.clients[0], self.clients[1]))
        t2 = threading.Thread(target=self.get_player_screen, args=(self.clients[1], self.clients[0]))

        t1.start()
        t2.start()

        t1.join()
        t2.join()


def main():
    clients = []

    while True:
        g = GameSetup(clients)
        clients = g.setup()

        g = Game(clients)
        g.run()


if __name__ == "__main__":
    main()
