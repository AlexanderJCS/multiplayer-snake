import threading
import logging
import socket
import json
import time


with open("preferences.json") as f:
    OPTIONS = json.load(f)


logging.basicConfig(
    filename="log.txt",
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


logger = logging.getLogger()
logger.setLevel(OPTIONS["logging_level"])


IP = socket.gethostbyname(socket.gethostname())
PORT = 9850

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP, PORT))
server_socket.listen(2)

HEADERSIZE = 10


def send(client, message):  # returns: whether the message was sent
    logging.debug(f"Sending message {message}")

    message = json.dumps(message, ensure_ascii=False).encode("utf-8")
    header_info = f"{len(message):<{HEADERSIZE}}".encode("utf-8")

    print(f"Header: {header_info}, message: {message}")

    try:
        client.clientsocket.send(header_info)
        client.clientsocket.send(message)
        return True

    except ConnectionResetError:
        return False


def receive(client):
    logging.debug("Attemting to receive packet")

    try:
        header = client.clientsocket.recv(HEADERSIZE)

        if header == b"":
            logging.warning(f"Socket {client} disconnected")
            return "Client disconnected"

        message_length = int(header.decode('utf-8').strip())
        message = client.clientsocket.recv(message_length)

    except (ConnectionResetError, ConnectionAbortedError):
        logging.warning(f"Connection reset or connection aborted error: socket {client} disconnected")
        return "Client disconnected"

    return json.loads(message)


class Client:
    def __init__(self, clientsocket, ip):
        self.clientsocket = clientsocket
        self.ip = ip


class GameSetup:
    def __init__(self, clients):
        self.clients = clients
        self.board_size = OPTIONS["board_size"]  # board_size x board_size board
        self.speed = OPTIONS["speed"]  # server tickrate and movement speed, updates every speed / 60 seconds
        self.apple_goal = OPTIONS["apple_goal"]  # how long your snake needs to be to win

    # Wait for two players to connect and start the game
    def wait_for_players(self):
        while len(self.clients) < 2:
            clientsocket, address = server_socket.accept()
            logging.info(f"Accepted client with address {address}")
            self.clients.append(Client(clientsocket, address))

    """
    Give starting game information to the clients
    The order is: "start" string, self.board_size, self.speed, self.apple_goal
    """
    def give_start_info(self):
        logging.info("Giving start info")

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

    """
    Gets giver's screen and sends it to recipient. This allows the client
    to see the other client's board.
    
    giver: clientsocket that gives the board
    recipient: clientsocket that receives the board
    
    IMPORTANT: The client will freeze until it receives this packet.
    """
    def get_player_screen(self, giver, recipient):
        while not self.ended:
            try:
                screen = receive(giver)

                if screen == "ready":  # If the client is ready for a new game, start one
                    break

                send(recipient, screen)

                # If the player won or lost
                if screen in ("won", "lost", "Client disconnected"):
                    logging.info(f"Client {screen}")
                    self.ended = True

            except json.JSONDecodeError:
                logging.warning(f"Invalid packet received from socket {giver}")

    """
    Starts two get_player_screen threads to allow both clients to see each other's boards.
    Execute this method to run the game.
    """
    def run(self):
        t1 = threading.Thread(target=self.get_player_screen, args=(self.clients[0], self.clients[1]))
        t2 = threading.Thread(target=self.get_player_screen, args=(self.clients[1], self.clients[0]))

        t1.start()
        t2.start()

        while not self.ended:  # Wait for the game to end on the main thread
            time.sleep(0.1)

        t1.join()
        t2.join()


def main():
    clients = []

    while True:
        setup = GameSetup(clients)
        clients = setup.setup()

        game = Game(clients)
        game.run()

        # Clear queued messages from both clients
        for client in clients:
            packet = receive(client)

            if packet == "Client disconnected":
                clients = []
                continue

            while packet != "ready2":
                packet = receive(client)


if __name__ == "__main__":
    main()
