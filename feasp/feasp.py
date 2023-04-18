import os
import threading


class NotFoundImage(Exception):
    pass


class NotFoundViewFunc(Exception):
    pass


def redirect(request_url):
    """
      提供一个方便重定向的函数
      传入一个需要跳转的路径, 此函数生成对应的响应
    """
    url_func_map = global_var["url_func_map"]
    if request_url in url_func_map:
        view_func = url_func_map[request_url][1]
        return view_func()
    raise NotFoundViewFunc("not found view function")


def url_for(endpoint=None, relative_path=None):
    """
      提供一个更方便构建文件路径的函数
      endpoint: 端点, 可以是static, templates, view_func_name
      relative_path: 为相对应端点的相对路径
      目前不支持在模板中使用, 仅支持在视图函数中使用
    """
    # 找到要url_for到的视图函数的请求路径
    if not endpoint is None and relative_path is None:
        url_func_map = global_var["url_func_map"]
        for path, values in url_func_map.items():
            if endpoint in values:
                return path
        raise NotFoundViewFunc("not found view function")
    # 处理模板内的url_for
    if endpoint in ("static", "templates") and relative is not None:
        pass


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

    filepath = os.path.join(global_var["user_base_dir"], "templates", filename)
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

    filepath = os.path.join(global_var["user_base_dir"], "static", image_path)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as fp:
            content = fp.read()
        return content
    raise NotFoundImage(f"not found {image_path}")


class Request:

    """ Request为解析类, 解析WSGI中的HTTP参数
      self.protocol: http协议类型
      self.method: http请求方法
      self.path: http请求路径(资源路径)
      self.args: url中的参数 """

    def __init__(self, environ):
        self.protocol = environ.get('SERVER_PROTOCOL', None)
        self.method = environ.get("REQUEST_METHOD", None)
        self.path = environ.get("PATH_INFO", None)
        self.args = environ.get("QUERY_STRING", None)
        self.uri = environ.get("REQUEST_URI", None)

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

      app = Feasp(__name)

      @app.route('/', methods=['GET'])
      def index():
          return 'Hello Feasp !' """

    def __init__(self, filename):
        # url与view_func的映射
        self.url_func_map = dict()
        # 用户的包文件路径
        self.user_base_dir = os.path.abspath(os.path.dirname(filename))
        global_var["user_base_dir"] = self.user_base_dir
        # self.url_func_map 传入全局字典
        global_var["url_func_map"] = self.url_func_map

    def dispatch(self, path, method):
        """ 处理请求并返回对应视图函数的响应 """

        # 处理图片相关请求
        for bq in (".ico", ".jpg", ".png"):
            if bq in path:
                mimetype = "image/x-icon"
                content = deal_images(path)
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

            endpoint = func.__name__   # 此处端点为视图函数的名称
            self.url_func_map[path] = (endpoint, func, methods)
            return wrapper
        return decorator

    def wsgi_apl(self, environ, start_response):
        http_local.request = Request(environ)
        http_local.response = self.dispatch(
            http_local.request.path, http_local.request.method)
        return http_local.response(environ, start_response)

    def run(self, host, port):
        from werkzeug.serving import run_simple
        run_simple(host, port, self.wsgi_apl)


global_var = dict()   # 存一些需要全局使用的变量
http_local = threading.local()   # 保证多线程请求的线程安全
