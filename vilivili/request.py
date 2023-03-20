"""
请求报文包含请求行、报文首部、空行、报文主体四个部分
在请求报文中，请求行和报文首部可以看成一个整体叫作请求头，报文主体又叫请求体
"""


class Request(object):
    """请求类"""

    def __init__(self, request_message):
        method, path, headers = self.parse_data(request_message)
        self.method = method  # 请求方法 GET、POST
        self.path = path  # 请求路径 /index
        self.headers = headers  # 请求头 {'Host': '127.0.0.1:8000'}

    def parse_data(self, data):
        """解析请求报文数据, 得到请求方法、请求路径、请求头"""
        header, body = data.split('\r\n\r\n', 1)
        method, path, headers = self._parse_header(header)
        return method, path, headers

    def _parse_header(self, data):
        """解析请求头, 得到请求方法、请求路径、请求头"""
        request_line, request_header = data.split('\r\n', 1)
        method, path, _ = request_line.split()
        headers = {}
        for header in request_header.split('\r\n'):
            k, v = header.split(': ', 1)
            headers[k] = v

        return method, path, headers
