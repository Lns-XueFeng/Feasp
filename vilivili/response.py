"""
响应报文包含状态行、报文首部、空行、报文主体四个部分
在响应报文中，状态行和报文首部可以看成一个整体叫作响应头，报文主体又叫响应体

因此最后在Response返回：响应头 + 空行 + 响应体
完整的返回给浏览器：
    b'HTTP/1.1 200 OK\r\n'              # 状态行
    b'Content-Type: text/html\r\n\r\n'  # 响应头
    b'<h1>Hello World</h1>'             # 响应体
"""


class Response(object):
    """响应类"""

    reason_phrase = {
        200: 'OK',
        405: 'METHOD NOT ALLOWED',
    }
    
    _headers = {
        'Content-Type': 'text/html; charset=utf-8',
    }

    def __init__(self, body, headers=None, status=200):

        if headers is not None:
            self._headers.update(headers)
        self.headers = self._headers  # 响应头
        self.body = body  # 响应体
        self.status = status  # 状态码

    def __bytes__(self):
        """构造响应报文"""
        header = f'HTTP/1.1 {self.status} {self.reason_phrase.get(self.status, "")}\r\n'
        header += ''.join(f'{k}: {v}\r\n' for k, v in self.headers.items())
        blank_line = '\r\n'
        body = self.body
        response_message = header + blank_line + body
        return response_message.encode('utf-8')
