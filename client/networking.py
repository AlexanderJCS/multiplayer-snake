import logging
import json


HEADERSIZE = 10


def send(message, client_socket):
    message = json.dumps(message, ensure_ascii=False).encode("utf-8")
    header_info = f"{len(message):<{HEADERSIZE}}".encode("utf-8")

    try:
        client_socket.send(header_info)
        client_socket.send(message)

    except ConnectionResetError:
        logging.critical("An existing connection was forcibly closed by the remote host")
        exit()


def receive(client_socket):
    logging.debug("Attempting to receive packet")

    message_length = client_socket.recv(HEADERSIZE)

    if message_length == b"":
        logging.critical("Server disconnected")
        exit()

    message = client_socket.recv(int(message_length))

    logging.debug("Received")

    return json.loads(message)
