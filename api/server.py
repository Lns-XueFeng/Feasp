from socket import *


IP = "127.0.0.1"
PORT = 5000
BUFLEN = 512

listen_socket = socket(AF_INET, SOCK_STREAM)
listen_socket.bind((IP, PORT))

listen_socket.listen(5)
print(f"Server fire success, On {PORT} process waiting client...")

data_socket, addr = listen_socket.accept()
print(f"Accepting a connect: {addr}")

while True:
    recv_data = data_socket.recv(BUFLEN)
    if not recv_data:
        break

    info = recv_data.decode()   # 将字节数据解码为字符串
    print(f"Receive from client: {info}")

    data_socket.send(f"Server has received success".encode())

data_socket.close()
listen_socket.close()
