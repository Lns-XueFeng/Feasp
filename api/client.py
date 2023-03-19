from socket import *


SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000
BUFLEN = 512


data_socket = socket(AF_INET, SOCK_STREAM)

data_socket.connect((SERVER_IP, SERVER_PORT))

while True:
    to_send = input(">>>")
    if to_send == "exit":
        break

    data_socket.send(to_send.encode())

    recv_data = data_socket.recv(BUFLEN)
    if not recv_data:
        break

    print(f"Receive from server: {recv_data.decode()}")

data_socket.close()
