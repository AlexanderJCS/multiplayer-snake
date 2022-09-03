import json


HEADERSIZE = 10


def send(message, client_socket):
    message = json.dumps(message, ensure_ascii=False).encode("utf-8")
    header_info = f"{len(message):<{HEADERSIZE}}".encode("utf-8")

    try:
        client_socket.send(header_info)
        client_socket.send(message)

    except ConnectionResetError:
        print("An existing connection was forcibly closed by the remote host")
        exit()


def receive(client_socket):
    message_length = client_socket.recv(HEADERSIZE)

    if message_length == b"":
        print("Server disconnected")
        exit()

    message = client_socket.recv(int(message_length))

    return json.loads(message)
