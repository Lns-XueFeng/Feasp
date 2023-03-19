class Response(object):
    """响应类"""

    # 根据状态码获取原因短语
    reason_phrase = {
        200: 'OK',
        405: 'METHOD NOT ALLOWED',
    }

    # 默认响应首部字段，指定响应内容的类型为 HTML
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
