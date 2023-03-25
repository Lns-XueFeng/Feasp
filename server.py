# 请求入口
from socket import *
import threading

from vilivili.views import routes
from vilivili.request import Request
from vilivili.response import Response
from vilivili.config import *


def make_response(request, headers=None):
    """构造响应报文"""
    status = 200
    route, methods = routes.get(request.path, (None, None))

    if request.method not in methods:
        status = 405
        return_data = 'Method Not Allowed'
    else:
        return_data = route()   # 启动相应的视图函数

    response = bytes(Response(return_data, headers=headers, status=status))
    return response


def process_connect(data_socket):
    """处理客户端的连接"""
    req_bytes = b''
    while True:
        recv_data = data_socket.recv(BUFFER_SIZE)

        req_bytes = req_bytes + recv_data
        if len(req_bytes) < 1024:
            break

    req_msg = req_bytes.decode("utf-8")
    request = Request(req_msg)   # 解析请求报文
    response_bytes = make_response(request)   # 构造响应报文
    data_socket.sendall(response_bytes)   # 返回浏览器索要的数据

    data_socket.close()


def fire_server():
    """启动服务器"""
    listen_socket = socket(AF_INET, SOCK_STREAM)
    listen_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # 允许端口复用
    listen_socket.bind((HOST, PORT))
    listen_socket.listen(5)
    print("___________________________________________________________")
    print("  __          ________ _______")
    print("  \\ \\        / /  ____|  _____")
    print("   \\ \\  /\\  / /| |____  |____) )")
    print("    \\ \\/  \\/ / |  ____|  ____(   __  __     __ ___")
    print("     \\  /\\  /  | |____  |____) )(__ |_ \\  /|_ |___)")
    print("      \\/  \\/   |______|_______/  __)|__ \\/ |__|")
    print()
    print("            Welcome to use the Web Server!")
    print("                     Version 1.0")
    print("                       XueFeng")
    print(f"Server fire success, Please click http://127.0.0.1:{PORT}")
    print("___________________________________________________________")

    while True:
        # 等待客户端请求
        data_socket, addr = listen_socket.accept()
        print(f'Client Type: {type(data_socket)}, Addr: {addr}')

        # 一旦接受了一个客户端的请求便创建一个线程来处理该请求
        new_thread = threading.Thread(target=process_connect, args=(data_socket,))
        new_thread.start()


if __name__ == "__main__":
    fire_server()
