"""
Author: Lns-XueFeng
Create Time: 2023.03.27
"""


import os
import json
import threading


class NotFound(Exception):
    pass


class UrlForError(Exception):
    pass


def redirect(request_url):
    """
      提供一个方便重定向的函数
      传入一个需要跳转的路径, 此函数生成对应的响应
    """

    url_func_map = _global_var["url_func_map"]
    if request_url in url_func_map:
        view_func = url_func_map[request_url][1]
        return view_func()
    raise NotFound("not found view function")


def url_for(endpoint, relative_path=None):
    """
      提供一个更方便构建文件路径的函数
      endpoint: 端点, 可以是static, templates, view_func_name
      relative_path: 为相对应端点的相对路径
      你应该这样传入relative_path：/index.html 或者 index.html 或者不传

      目前不支持在模板中使用, 仅支持在视图函数中使用
    """

    # 找到要url_for到的视图函数的请求路径
    if relative_path is None:
        url_func_map = _global_var["url_func_map"]
        for path, values in url_func_map.items():
            if endpoint in values:
                return path
        raise NotFound("not found view function")
    # 以下代码需要等到支持模板渲染时才可用
    if endpoint in ("static", "templates") and relative_path is not None:
        if relative_path[0] == "/":
            relative_path = relative_path[1:]

        abspath = os.path.join(_global_var["user_pkg_abspath"], endpoint, relative_path)
        return abspath
    raise UrlForError("url_for func error")


def render_template(filename):
    """
      渲染templates下的html文件
      因此你需要将所有html文件放在templates目录中
      filename为html文件在templates中的相对路径
      你应该这样传入filename：/index.html 或者 index.html
      后续增加可传变量、引擎解析等
    """

    if filename[0] == "/":
        filename = filename[1:]

    filepath = os.path.join(_global_var["user_pkg_abspath"], "templates", filename)
    with open(filepath, 'r') as fp:
        content = fp.read()
    return content


def deal_images(image_path):
    """
      处理图片请求相关, 支持jpg, png, ico
      image_path: static目录下的文件路径
      比如example/static下的favicon。ico
      你应该在html中这样写：/favicon.ico 或者 favicon.ico
    """

    if image_path[0] == "/":
        image_path = image_path[1:]

    filepath = os.path.join(_global_var["user_pkg_abspath"], "static", image_path)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as fp:
            content = fp.read()
        return content
    raise NotFound(f"not found {image_path}")


def deal_static(link_path):
    """
      处理css, js文件的请求
    """
    if link_path[0] == "/":
        link_path = link_path[1:]

    filepath = os.path.join(_global_var["user_pkg_abspath"], "static", link_path)
    if os.path.exists(filepath):
        with open(filepath, 'r') as fp:
            content = fp.read()
        return content
    raise NotFound(f"not found {link_path}")


class Template:
    pass


class Request:

    """ Request为解析类, 解析WSGI中的HTTP参数
      self.protocol: http协议类型
      self.method: http请求方法
      self.path: http请求路径(资源路径)
      self.args: url中的参数
      self.cookie: 存储已解析浏览器的cookie """

    def __init__(self, environ):
        self.protocol = environ.get('SERVER_PROTOCOL')
        self.method = environ.get("REQUEST_METHOD")
        self.path = environ.get("PATH_INFO")
        self.qs = environ.get("QUERY_STRING")
        self.uri = environ.get("REQUEST_URI")

        http_cookie = environ.get("HTTP_COOKIE")
        self.cookie = dict()   # 存储浏览器返回的cookie
        if http_cookie is not None:
            cl = http_cookie.split(" ")
            for kv in cl:
                k, v = tuple(kv.split("="))
                self.cookie[k] = v

    def __repr__(self):
        return f"<{type(self).__name__} {self.method} {self.protocol} {self.path}>"


class Response:

    """ Response为响应类, 基于WSGI的包装返回
      支持bytes以及非bytes的包装返回 """

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
        self.headers = {   # 响应头
            "Content-Type": f"{self.mimetype}; charset=utf-8",
        }

    def __call__(self, environ, start_response):
        global session
        if len(session) > 0:
            cookie_str = ""
            for k, v in session.items():
                cookie_str = cookie_str + f"{k}={v} "
            self.headers.update(
                {"Set-Cookie": f"{cookie_str}"}
            )
        session.clear()   # 设置完后清空session: 之前是将session重新赋值{}, 这样并不能清空session

        start_response(
            f"{self.status} {self.reason_phrase[self.status]}",
            [(k, v) for k, v in self.headers.items()]
        )

        if isinstance(self.body, bytes):
            return [self.body]
        return [self.body.encode("utf-8")]

    def __repr__(self):
        return f"<{type(self).__name__} {self.mimetype} {self.status} {self.reason_phrase[self.status]}>"


class Method:
    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"
    PUT = "PUT"


class Error:

    """ Error规定了:
      资源未找到、方法不允许、服务器错误三种响应错误 """

    http_404 = Response("<h1>Not Found 404</h1>", mimetype="text/html")
    http_404.status = 404
    http_405 = Response("<h1>Method Not Allowed</h1>", mimetype="text/html")
    http_405.status = 405
    http_500 = Response("<h1>Server Internal Error</h1>", mimetype="text/html")
    http_500.status = 500


class Feasp:

    """ Feasp: 一个简易的Web框架, 基于WSGI规范, 仅用来学习交流
      实现了路由注册, WSGI Application, 请求的分发, 并保证多线程情况下的请求-响应的安全返回
      使用示例:
      from feasp import Feasp

      app = Feasp(__name__)

      @app.route('/', methods=['GET'])
      def index():
          return 'Hello Feasp !' """

    def __init__(self, filename):
        # url与view_func的映射
        self.url_func_map = dict()
        # 用户的包文件路径
        self.user_pkg_abspath = os.path.abspath(os.path.dirname(filename))
        _global_var["user_pkg_abspath"] = self.user_pkg_abspath
        # self.url_func_map 传入全局字典
        _global_var["url_func_map"] = self.url_func_map
        # 待存储request中的cookie
        self.cookie = dict()

    def dispatch(self, path, method):
        """ 处理请求并返回对应视图函数的响应 """
        # 处理图片相关请求
        for bq in (".ico", ".jpg", ".png"):
            if bq in path:
                mimetype = "image/x-icon"
                content = deal_images(path)
                return Response(content, mimetype=mimetype)
        # 处理css, js文件请求
        for bq in (".css", ".js"):
            if bq in path and bq == ".css":
                mimetype = "text/css"
                content = deal_static(path)
                return Response(content, mimetype=mimetype)
            if bq in path and bq == ".js":
                mimetype = "application/javascript"
                content = deal_static(path)
                return Response(content, mimetype=mimetype)
        # 处理视图函数相关请求
        values = self.url_func_map.get(path, None)
        if values is None:
            return Error.http_404

        endpoint, view_func, methods = values
        view_func_return = view_func()
        if method not in methods:
            return Error.http_405

        if isinstance(view_func_return, str):
            mimetype = "text/html"
        elif isinstance(view_func_return, dict):
            view_func_return = json.dumps(view_func_return)
            mimetype = "Application/json"
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

            endpoint = func.__name__   # 此处端点为视图函数的名称
            self.url_func_map[path] = (endpoint, func, methods)
            return wrapper
        return decorator

    def wsgi_apl(self, environ, start_response):
        _http_local.request = Request(environ)

        # 当并发请求时, 可能会造成cookie或session的错误竞争存取
        # 因此使用锁将取cookie和返回响应(包括session相关操作)设置为原子性执行
        with threading.Lock():
            self.cookie = _http_local.request.cookie   # 传递cookie
            _http_local.response = self.dispatch(
                _http_local.request.path, _http_local.request.method)
        return _http_local.response(environ, start_response)

    def run(self, host, port, multithread=True):
        if multithread:   # 默认使用支持多线程的run_simple
            from werkzeug.serving import run_simple
            run_simple(host, port, self.wsgi_apl)

        if not multithread:   # 否则使用单线程的make_server
            from wsgiref.simple_server import make_server
            with make_server(host, port, self.wsgi_apl) as httpd:
                print(f"* Running on http://{host}:{port}")
                httpd.serve_forever()


_global_var = dict()   # 存一些需要全局使用的变量
_http_local = threading.local()   # 保证多线程请求时的线程安全
session = dict()   # session会话: 用户用于让浏览器设置cookie
