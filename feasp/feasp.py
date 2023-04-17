import os
import threading


def render_template(filename):
    filepath = os.path.join(global_var["user_base_dir"], "template", filename)
    with open(filepath, 'r') as fp:
        content = fp.read()
    return content


def deal_favicon():
    filepath = os.path.join(global_var["user_base_dir"], "static", "favicon.ico")
    if os.path.exists(filepath):
        with open(filepath, 'rb') as fp:
            content = fp.read()
        return content
    return Error.http_404


class Request:
    def __init__(self, environ):
        self.protocol = environ.get('SERVER_PROTOCOL', None)
        self.method = environ.get("REQUEST_METHOD", None)
        self.path = environ.get("PATH_INFO", None)
        self.args = environ.get("QUERY_STRING", None)
        self.uri = environ.get("REQUEST_URI", None)

    def __repr__(self):
        return f"<{type(self).__name__} {self.method} {self.protocol} {self.path})"


class Response:

    reason_phrase = {
        200: "OK",
        302: "FOUND",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Server Internal Error",
    }

    def __init__(self, body, mimetype, status=200):
        self.body = body   # 响应体
        self.status = status   # 状态码
        self.mimetype = mimetype   # 文本类型
        self.headers = {
            "Content-Type": f"{self.mimetype}; charset=utf-8",
        }   # 响应头

    def __call__(self, environ, start_response):
        start_response(
            f"{self.status} {self.reason_phrase[self.status]}",
            [(k, v) for k, v in self.headers.items()]
        )
        return [self.body.encode("utf-8")]

    def __repr__(self):
        return f"<{type(self).__name__} {self.mimetype} {self.status} {self.reason_phrase}"


class Method:
    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"
    PUT = "PUT"


class Error:
    http_404 = Response("<h1>Not Found 404</h1>", mimetype="text/html")
    http_404.status = 404
    http_405 = Response("<h1>Method Not Allowed</h1>", mimetype="text/html")
    http_405.status = 405
    http_500 = Response("<h1>Server Internal Error</h1>", mimetype="text/html")
    http_500.status = 500


class Feasp:

    def __init__(self, filename):
        # url与view_func的映射
        self.url_func_map = {"/favicon.ico": (deal_favicon, ["GET"])}
        # 用户的包文件路径
        self.user_base_dir = os.path.abspath(os.path.dirname(filename))
        global_var["user_base_dir"] = self.user_base_dir

    def dispatch(self, path, method):
        """ 处理请求并返回对应视图函数的响应 """
        values = self.url_func_map.get(path, None)
        if values is None:
            return Error.http_404

        view_func, methods = values
        view_func_return = view_func()
        if method not in methods:
            return Error.http_405

        if isinstance(view_func_return, str):
            mimetype = "text/html"
        elif isinstance(view_func_return, bytes):
            mimetype = "image/x-icon"
        elif isinstance(view_func_return, dict):
            temp = "{"
            for k, v in view_func_return.items():
                temp += f"{k}': '{v}, "
            view_func_return = temp + "}"
            mimetype = "text/plain"
        elif isinstance(view_func_return, list) \
                or isinstance(view_func_return, tuple):
            temp = ", ".join(view_func_return)
            view_func_return = "[" + temp + "]"
            mimetype = "text/plain"
        else:
            return Error.http_500

        return Response(view_func_return, mimetype=mimetype)

    def route(self, path, methods):
        """ 将路径与视图函数进行绑定 """
        if methods is None:
            methods = [Method.GET]

        def decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            self.url_func_map[path] = (func, methods)
            return wrapper
        return decorator

    def wsgi_apl(self, environ, start_response):
        http_local.request = Request(environ)
        response = self.dispatch(
            http_local.request.path, http_local.request.method)
        return response(environ, start_response)

    def run(self, host, port):
        from werkzeug.serving import run_simple
        run_simple(host, port, self.wsgi_apl)


global_var = dict()   # 存一些需要全局使用的变量
http_local = threading.local()   # 保证多线程请求的线程安全
