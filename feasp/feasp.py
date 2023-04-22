"""
Author: Lns-XueFeng
Create Time: 2023.03.27
"""


import os
import json
import re
import threading
from urllib.parse import parse_qs


class NotFound(Exception):
    pass


def redirect(request_url):
    """
      提供一个方便重定向的函数
      传入一个需要跳转的路径, 此函数生成对应的响应
      例子见: example/app.py -> redirect_视图函数
    """

    url_func_map = _global_var["url_func_map"]
    if request_url in url_func_map:
        view_func = url_func_map[request_url][1]
        return view_func()
    raise NotFound("not found view function")


def url_for(endpoint):
    """
      提供一个更方便构建文件路径的函数
      仅支持在视图函数中使用, 传入需要url_for的view_func_name
      例子见: example/app.py -> redirect_视图函数
    """

    # 找到要url_for到的视图函数的请求路径
    url_func_map = _global_var["url_func_map"]
    for path, values in url_func_map.items():
        if endpoint in values:
            return path
    raise NotFound("not found view function")


def render_template(filename, **context):
    """
      渲染templates下的html文件
      因此你需要将所有html文件放在templates目录中
      filename为html文件在templates中的相对路径
      **context为用户传入的上下文变量, 其为一个个键值对
      你应该这样传入filename：/index.html 或者 index.html
      例子见: example/app.py -> index and show_variable视图函数
    """

    if filename[0] == "/":
        filename = filename[1:]

    filepath = os.path.join(
        _global_var["user_pkg_abspath"], "templates", filename)
    with open(filepath, 'r', encoding="utf-8") as fp:
        text = fp.read()
    return Template(text, context).render()


def _deal_images(image_path):
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


def _deal_static(link_path):
    """
      处理css, js文件的请求
      link_path: static目录下的文件路径
      比如example/static下的style.css
      你应该在html中这样写：/style.css 或者 style.css
    """

    if link_path[0] == "/":
        link_path = link_path[1:]

    filepath = os.path.join(_global_var["user_pkg_abspath"], "static", link_path)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding="utf-8") as fp:
            content = fp.read()
        return content
    raise NotFound(f"not found {link_path}")


class Template:

    """ Template为渲染类, 解析html模板
      目前支持定义变量与循环并进行渲染:
        定义变量: 占位符为花括号{{}}, 变量定义在花括号内即可, 比如{{name}}
        定义循环: {% for name in name_list %}
                    {{name}}
                 {% endfor %}
      注意：传入的变量必须与在模板中定义的变量一致, 而后以key=value的形式传入渲染函数 """

    def __init__(self, text, context):
        # text为模板的HTML代码
        self.text = text

        # context为用户传入的上下文变量
        self.context = context

        # 匹配出所有的for语句, 模板变量
        self.snippets = re.split("({{.*?}}|{%.*?%})", self.text, flags=re.DOTALL)

        # 保存从HTML中解析出来的for语句代码片段
        self.for_snippet = []

        # 保存最终地渲染结果
        self.result = []

        # 处理snippets中的代码段
        self._deal_code_segment()

    def _get_var_value(self, var):
        """ 根据变量名获取变量的值 """

        if '.' not in var:
            value = self.context.get(var)
        else:
            obj, attr = var.split('.')
            value = getattr(self.context.get(obj), attr)

        if not isinstance(value, str):
            value = str(value)
        return value

    def _deal_code_segment(self):
        """ 处理所有匹配出来的代码段 """
        # 标记是否为for语句代码段
        is_for_snippet = False

        # 遍历所有匹配出来的代码片段
        for snippet in self.snippets:
            # 解析模板变量
            if snippet.startswith("{{"):
                if is_for_snippet is False:
                    var = snippet[2:-2].strip()
                    snippet = self._get_var_value(var)
            # 解析for语句
            elif snippet.startswith("{%"):
                if "in" in snippet:
                    is_for_snippet = True
                    self.result.append("{}")
                else:
                    is_for_snippet = False
                    snippet = ''

            if is_for_snippet:
                # 如果是for语句代码段, 需要进行二次处理, 暂时保存到for语句片段列表中
                self.for_snippet.append(snippet)
            else:
                # 如果是模板变量, 直接将变量值追加到结果列表中
                self.result.append(snippet)

    def _parse_for_snippet(self):
        """ 解析for语句片段代码 """
        result = []   # 保存for语句片段解析结果
        if self.for_snippet:
            # 解析for语句开始代码片段
            words = self.for_snippet[0][2:-2].strip().split()
            iter_obj_from_context = self.context.get(words[-1])
            for value in iter_obj_from_context:
                # 遍历for语句片段的代码块
                for snippet in self.for_snippet[1:]:
                    if snippet.startswith("{{"):
                        var = snippet[2:-2].strip()
                        if '.' not in var:
                            snippet = value
                        else:
                            obj, attr = var.split('.')
                            snippet = getattr(value, attr)

                    if not isinstance(snippet, str):
                        snippet = str(snippet)
                    result.append(snippet)   # 将解析出来的循环变量结果追加到for语句片段解析结果列表中
        return result

    def render(self):
        for_result = self._parse_for_snippet()   # 获取for语句片段解析结果
        return "".join(self.result).format(''.join(for_result))

    def __repr__(self):
        return f"<{type(self).__name__} {self.context}>"


class Request:

    """ Request为解析类, 解析WSGI中的HTTP参数
      self.protocol: http协议类型
      self.method: http请求方法
      self.path: http请求路径(资源路径)
      self.args: url中的参数
      self.cookie: 存储已解析浏览器的cookie
      self.form: 如果有POST请求则进行存储 """

    def __init__(self, environ):
        self.protocol = environ.get('SERVER_PROTOCOL')
        self.method = environ.get("REQUEST_METHOD")
        self.path = environ.get("PATH_INFO")
        self.qs = environ.get("QUERY_STRING")
        self.uri = environ.get("REQUEST_URI")
        self.cookie = self.get_cookie(environ)
        self.form = self.get_form(environ)

    @staticmethod
    def get_cookie(environ):
        cookie = {}
        http_cookie = environ.get("HTTP_COOKIE")
        if http_cookie is not None:
            cl = http_cookie.split(" ")
            for kv in cl:
                k, v = tuple(kv.split("="))
                cookie[k] = v
        return cookie

    @staticmethod
    def get_form(environ):
        rb_size = int(environ.get('CONTENT_LENGTH', 0))
        rb = environ["wsgi.input"].read(rb_size)
        rb_form = parse_qs(rb)
        # 需要将rb_form中bytes的key和value解码成字符串
        sb_form = {bk.decode(): [bv[0].decode()][0] for bk, bv in rb_form.items()}
        return sb_form

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
      实现了路由注册(支持GET、POST), WSGI Application, 请求的分发, 支持多线程及响应安全返回
      提供各种资源的自动处理, 在视图路径中定义固定变量, 在视图函数中用session设置cookie, 使用app.request读取相关属性
      使用示例:
      from feasp import Feasp

      app = Feasp(__name__)

      @app.route('/', methods=['GET'])
      def index():
          return 'Hello Feasp !' """

    # 指向Request类
    request_class = Request

    # 指向Response类
    response_class = Response

    def __init__(self, filename):
        # url与view_func的映射
        self.__url_func_map = {"path_and_var": {}}

        # self.__url_func_map 传入全局字典
        _global_var["url_func_map"] = self.__url_func_map

        # 用户的包文件路径
        self.__user_pkg_abspath = os.path.abspath(os.path.dirname(filename))
        _global_var["user_pkg_abspath"] = self.__user_pkg_abspath

        # 指向当前请求对象, 可使用户访问
        self.request = None

    def dispatch(self, path, method):
        """ 处理请求并返回对应视图函数的响应 """
        # 处理图片相关请求
        for bq in (".ico", ".jpg", ".png"):
            if bq in path:
                mimetype = "image/x-icon"
                content = _deal_images(path)
                return self.response_class(content, mimetype=mimetype)
        # 处理css, js文件请求
        for bq in (".css", ".js"):
            if bq in path and bq == ".css":
                mimetype = "text/css"
                content = _deal_static(path)
                return self.response_class(content, mimetype=mimetype)
            if bq in path and bq == ".js":
                mimetype = "application/javascript"
                content = _deal_static(path)
                return self.response_class(content, mimetype=mimetype)

        # 处理视图函数相关请求
        values = self.__url_func_map.get(path, None)
        variable = None
        if values is None:   # 判断path是否携带变量
            for_path, variable = path.split("/")[:-1], path.split("/")[-1]
            path = "/".join(for_path)
            values = self.__url_func_map["path_and_var"].get(path, None)
        if values is None:   # 如果还是None, 抛出错误
            return Error.http_404

        endpoint, view_func, methods = values
        if variable:   # 如果有variable, 则传入视图函数
            view_func_return = view_func(variable)
        else:
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

        return self.response_class(view_func_return, mimetype=mimetype)

    def route(self, path, methods):
        """ 将路径与视图函数进行绑定 """
        if methods is None:
            methods = [Method.GET]

        def decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            endpoint = func.__name__  # 此处端点为视图函数的名称
            if "<variable:value>" in path:   # 支持url变量定义, 固定为此形式
                new_path = "/".join(path.split("/")[:-1])
                self.__url_func_map["path_and_var"][new_path] = (endpoint, func, methods)
            else:
                self.__url_func_map[path] = (endpoint, func, methods)
            return wrapper
        return decorator

    def wsgi_apl(self, environ, start_response):
        _http_local.request = self.request_class(environ)

        # 当并发请求时, 可能会造成request或session的错误竞争存取
        # 因此使用锁将取session和返回响应(包括session相关操作)设置为原子性执行
        # 这样就可以确保并发时每一个请求都能返回正确的request以及响应给用户
        with threading.Lock():
            self.request = _http_local.request   # 传递给进入临界区的线程其对应的request
            _http_local.response = self.dispatch(
                _http_local.request.path,
                _http_local.request.method
            )
        return _http_local.response(environ, start_response)

    def run(self, host, port, multithread=False):
        if not multithread:   # 默认make_server: 仅支持单线程
            from wsgiref.simple_server import make_server
            with make_server(host, port, self.wsgi_apl) as httpd:
                print(f"* Running on http://{host}:{port}")
                httpd.serve_forever()

        if multithread:   # run_simple: 支持多线程
            from werkzeug.serving import run_simple
            run_simple(host, port, self.wsgi_apl)


_global_var = {}   # 存一些需要全局使用的变量
_http_local = threading.local()   # 保证多线程请求时的线程安全
session = {}   # session会话: 用户用于让浏览器设置并存储cookie在本地
