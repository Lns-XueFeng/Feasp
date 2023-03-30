import os
import threading

from werkzeug.wrappers import Request as BaseRequest, Response as BaseResponse


global_var = {}   # 存一些需要全局使用的变量
http_local = threading.local()


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


class Request(BaseRequest):
    pass


class Response(BaseResponse):
    pass


class Error:
    http_404 = Response("<html><body>Not Found 404</body></html>", mimetype="text/html")
    http_404.status = "404 Not Found"
    http_405 = Response('<html><body>Method Not Allowed</body></html>', mimetype="text/html")
    http_405.status = "405 Method Not Allowed"
    http_500 = Response('<html><body>Server Internal Error</body></html>', mimetype="text/html")
    http_500.status = "500 Server Internal Error"


class Method:
    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"
    PUT = "PUT"


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

    def run(self):
        from werkzeug.serving import run_simple
        run_simple("127.0.0.1", 8000, self.wsgi_apl)
