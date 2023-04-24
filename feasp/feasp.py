"""
Author: Lns-XueFeng
Create Time: 2023.03.27

Why write: 通过实现一个简单的Web框架来增强自己对Web开发的了解
"""

__author__ = "Lns-XueFeng"
__version__ = "0.6"
__license__ = "MIT"

import os
import json
import re
import threading


class NotFound(Exception):
    pass


def make_response(body, mimetype="text/html", status=200):
    """
      提供一个可自定义响应的函数, 可自定义下列三个参数
      body为响应体, mimetype为响应类型, status为响应状态码
    """

    if isinstance(body, str) or isinstance(body, bytes):
        return Response(body, mimetype, status)
    elif isinstance(body, Response):
        body.mimetype, body.status = mimetype, status
        return body
    return Response(*FeaspError.http_500)


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
    with open(filepath, "r", encoding="utf-8") as fp:
        text = fp.read()
    return FeaspTemplate(text, context).render()


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
        with open(filepath, "rb") as fp:
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
        with open(filepath, "r", encoding="utf-8") as fp:
            content = fp.read()
        return content
    raise NotFound(f"not found {link_path}")


class FeaspTemplate:
    """ Template为渲染类, 解析HTML模板
      目前支持定义变量与循环并进行渲染:
        定义变量: 占位符为花括号{{}}, 变量定义在花括号内即可, 比如{{ name }}
        定义循环(目前仅支持定义一个for循环):
            {% for name in name_list %}
                {{ name }}
            {% endfor %}
      注意：传入的变量必须与在模板中定义的变量一致, 而后以key=value的形式传入渲染函数 """

    def __init__(self, text, context):
        # text为模板的HTML代码
        self.text = text

        # context为用户传入的上下文变量
        self.context = context

        # 匹配出所有的模板变量, for语句
        self.snippet_list = re.split("({{.*?}}|{%.*?%})", self.text, flags=re.DOTALL)

        # 保存从HTML中解析出的for语句代码片段
        self.for_snippet = []

        # 保存最终地渲染结果
        self.finally_result = []

        # 处理snippets中的代码段
        self._deal_code_segment()

    def _get_var_value(self, var_name):
        """ 根据变量名获取变量的值 """
        if "." not in var_name:
            value = self.context.get(var_name)
        else:  # 处理obj.attr
            obj, attr = var_name.split(".")
            value = getattr(self.context.get(obj), attr)

        if not isinstance(value, str):
            value = str(value)
        return value

    def _deal_code_segment(self):
        """ 处理所有匹配出来的代码段 """
        is_for_snippet = False  # 标记是否为for语句代码段

        for snippet in self.snippet_list:
            # 解析模板变量
            if snippet.startswith("{{"):
                if not is_for_snippet:
                    var_name = snippet[2:-2].strip()
                    snippet = self._get_var_value(var_name)
            # 解析for语句
            elif snippet.startswith("{%"):
                if "in" in snippet:
                    # 注意此标记, 这意味着一旦进入for循环
                    # 便利用此处的代码处理循环变量, 直到退出循环, 恢复标记
                    is_for_snippet = True
                    # 为了后续使用format方法添加解析完的for代码段, 使用{}格式符
                    self.finally_result.append("{}")
                else:
                    is_for_snippet = False
                    snippet = ""

            if is_for_snippet:
                # 如果是for语句代码段, 需要进行二次处理, 暂时保存到for语句片段列表中
                self.for_snippet.append(snippet)
            else:
                # 如果是模板变量, 直接将变量值追加到结果列表中
                self.finally_result.append(snippet)

    def _parse_for_snippet(self):
        """ 解析for语句片段代码 """
        result = []  # 保存for语句片段解析结果
        if self.for_snippet:
            # 解析for语句开始代码片段
            words = self.for_snippet[0][2:-2].strip().split()
            iter_obj_from_context = self.context.get(words[-1])
            for value in iter_obj_from_context:
                # 遍历for语句片段的代码块, 将value与循环体内的代码块拼接
                for snippet in self.for_snippet[1:]:
                    if snippet.startswith("{{"):
                        var = snippet[2:-2].strip()
                        if "." not in var:
                            snippet = value
                        else:
                            obj, attr = var.split(".")
                            snippet = getattr(value, attr)
                    # 将解析出来的循环变量结果追加到for语句片段解析结果列表中
                    if not isinstance(snippet, str):
                        snippet = str(snippet)
                    result.append(snippet)
        return result

    def render(self):
        """ 组合原生html代码段与渲染完的语句代码片段 """
        for_result = self._parse_for_snippet()  # 获取for语句片段解析结果
        return "".join(self.finally_result).format("".join(for_result))

    def __repr__(self):
        return f"<{type(self).__name__} {self.context}>"


class Request(threading.local):
    """ Request为解析类, 解析WSGI中的HTTP参数
      接收environ字典, 以解析出可供利用的字段信息 """

    def __init__(self, environ):
        # HTTP请求相关信息, 字典类型
        self.environ = environ

    @property
    def cookie(self):
        """ 得到易于用户读取的cookie字典 """
        cookie = {}
        http_cookie = self.environ.get("HTTP_COOKIE")
        if http_cookie is not None:
            cl = http_cookie.split(" ")
            for kv in cl:
                k, v = tuple(kv.split("="))
                cookie[k] = v
        return cookie

    @property
    def form(self):
        """ 得到易于用户读取的form字典 """
        from urllib.parse import parse_qs
        if self.environ.get("CONTENT_LENGTH", "") == "":
            rb_size = 0
        else:
            rb_size = int(self.environ.get("CONTENT_LENGTH", 0))
        rb = self.environ["wsgi.input"].read(rb_size)
        rb_form = parse_qs(rb)
        # 需要将rb_form中bytes的key和value解码成字符串
        sb_form = {bk.decode(): [bv[0].decode()][0] for bk, bv in rb_form.items()}
        return sb_form

    @property
    def protocol(self):
        """ HTTP协议类型及版本 """
        return self.environ.get("SERVER_PROTOCOL")

    @property
    def method(self):
        """ HTTP请求方法 """
        return self.environ.get("REQUEST_METHOD")

    @property
    def url_scheme(self):
        """ WSGI支持的http协议 """
        return self.environ.get("wsgi.url_scheme")

    @property
    def url(self):
        """ 得到易于用户使用的完整url """
        url, header = None, None
        request_uri = self.environ.get("REQUEST_URI")
        http_host = self.environ.get("HTTP_HOST")
        if self.url_scheme:
            header = self.url_scheme + "://"
        if self.url_scheme and request_uri and http_host:
            url = header + http_host + request_uri
        return url

    @property
    def referer(self):
        """ 当前请求来源网页 """
        return self.environ.get("HTTP_REFERER", "")

    @property
    def path(self):
        """ HTTP请求路径(资源路径) """
        return self.environ.get("PATH_INFO")

    @property
    def url_args(self):
        """ url中的查询参数 """
        return self.environ.get("QUERY_STRING")

    @property
    def connection(self):
        """ HTTP请求是keep-alive还是close """
        return self.environ.get("HTTP_CONNECTION")

    @property
    def platform(self):
        """ HTTP请求来自什么系统平台 """
        return self.environ.get("HTTP_SEC_CH_UA_PLATFORM")

    @property
    def user_agent(self):
        """ 其中包含了请求客户端的诸多身份信息 """
        return self.environ.get("HTTP_USER_AGENT")

    def __repr__(self):
        return f"<{type(self).__name__} {self.method} {self.protocol} {self.path}>"


class Response(threading.local):
    """ Response为响应类, 基于WSGI的包装返回
      支持bytes以及非bytes的包装返回 """

    reason_phrase = {
        100: "CONTINUE",
        101: "SWITCHING PROTOCOLS",
        200: "OK",
        201: "CREATED",
        202: "ACCEPTED",
        203: "NON-AUTHORITATIVE INFORMATION",
        204: "NO CONTENT",
        205: "RESET CONTENT",
        206: "PARTIAL CONTENT",
        300: "MULTIPLE CHOICES",
        301: "MOVED PERMANENTLY",
        302: "FOUND",
        303: "SEE OTHER",
        304: "NOT MODIFIED",
        305: "USE PROXY",
        306: "RESERVED",
        307: "TEMPORARY REDIRECT",
        400: "BAD REQUEST",
        401: "UNAUTHORIZED",
        402: "PAYMENT REQUIRED",
        403: "FORBIDDEN",
        404: "NOT FOUND",
        405: "METHOD NOT ALLOWED",
        406: "NOT ACCEPTABLE",
        407: "PROXY AUTHENTICATION REQUIRED",
        408: "REQUEST TIMEOUT",
        409: "CONFLICT",
        410: "GONE",
        411: "LENGTH REQUIRED",
        412: "PRECONDITION FAILED",
        413: "REQUEST ENTITY TOO LARGE",
        414: "REQUEST-URI TOO LONG",
        415: "UNSUPPORTED MEDIA TYPE",
        416: "REQUESTED RANGE NOT SATISFIABLE",
        417: "EXPECTATION FAILED",
        500: "INTERNAL SERVER ERROR",
        501: "NOT IMPLEMENTED",
        502: "BAD GATEWAY",
        503: "SERVICE UNAVAILABLE",
        504: "GATEWAY TIMEOUT",
        505: "HTTP VERSION NOT SUPPORTED",
    }

    def __init__(self, body, mimetype, status=200):
        # 响应体(响应正文)
        self.body = body

        # 响应的状态码
        self.status = status

        # 响应的文本类型
        self.mimetype = mimetype

        # 响应头, 可以动态添加多个字段
        self.headers = {
            "Content-Type": f"{self.mimetype}; charset=utf-8",
        }

        # 供用户设置set-cookie
        self.session = {}

    def __call__(self, environ, start_response):
        """ 返回包装后的响应, 以传递给客户端 """

        if len(self.session) > 0:
            cookie_str = ""
            for k, v in self.session.items():
                cookie_str = cookie_str + f"{k}={v} "
            self.headers.update({"Set-Cookie": f"{cookie_str}"})
        # 设置完后清空session: 之前是将session重新赋值{}, 这样并不能清空session
        self.session.clear()

        start_response(
            f"{self.status} {self.reason_phrase[self.status]}",
            [(k, v) for k, v in self.headers.items()]
        )

        if isinstance(self.body, bytes):
            return [self.body]
        return [self.body.encode("utf-8")]

    def __repr__(self):
        return f"<{type(self).__name__} {self.mimetype}" \
               f" {self.status} {self.reason_phrase[self.status]}>"


class Method:
    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"
    PUT = "PUT"
    HEAD = "HEAD"
    CONNECT = "CONNECT"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"


class FeaspError:
    """ FeaspError规定了所有状态码对应的响应信息 """

    http_100 = ("<h1>CONTINUE</h1>", "text/html", 101)
    http_101 = ("<h1>SWITCHING PROTOCOLS</h1>", "text/html", 101)
    http_200 = ("<h1>OK</h1>", "text/html", 200)
    http_201 = ("<h1>CREATED</h1>", "text/html", 201)
    http_202 = ("<h1>ACCEPTED</h1>", "text/html", 202)
    http_203 = ("<h1>NON-AUTHORITATIVE INFORMATION</h1>", "text/html", 203)
    http_204 = ("<h1>NO CONTENT</h1>", "text/html", 204)
    http_205 = ("<h1>RESET CONTENT</h1>", "text/html", 205)
    http_206 = ("<h1>PARTIAL CONTENT</h1>", "text/html", 206)
    http_300 = ("<h1>MULTIPLE CHOICES</h1>", "text/html", 300)
    http_301 = ("<h1>MOVED PERMANENTLY</h1>", "text/html", 301)
    http_302 = ("<h1>FOUND</h1>", "text/html", 302)
    http_303 = ("<h1>SEE OTHER</h1>", "text/html", 303)
    http_304 = ("<h1>NOT MODIFIED</h1>", "text/html", 304)
    http_305 = ("<h1>USE PROXY</h1>", "text/html", 305)
    http_306 = ("<h1>RESERVED</h1>", "text/html", 306)
    http_307 = ("<h1>TEMPORARY REDIRECT</h1>", "text/html", 307)
    http_400 = ("<h1>BAD REQUEST</h1>", "text/html", 400)
    http_401 = ("<h1>UNAUTHORIZED</h1>", "text/html", 401)
    http_402 = ("<h1>PAYMENT REQUIRED</h1>", "text/html", 402)
    http_403 = ("<h1>FORBIDDEN</h1>", "text/html", 403)
    http_404 = ("<h1>NOT FOUND</h1>", "text/html", 404)
    http_405 = ("<h1>METHOD NOT ALLOWED</h1>", "text/html", 405)
    http_406 = ("<h1>NOT ACCEPTABLE</h1>", "text/html", 406)
    http_407 = ("<h1>PROXY AUTHENTICATION REQUIRED</h1>", "text/html", 407)
    http_408 = ("<h1>REQUEST TIMEOUT</h1>", "text/html", 408)
    http_409 = ("<h1>CONFLICT</h1>", "text/html", 409)
    http_410 = ("<h1>GONE</h1>", "text/html", 410)
    http_411 = ("<h1>LENGTH REQUIRED</h1>", "text/html", 411)
    http_412 = ("<h1>PRECONDITION FAILED</h1>", "text/html", 412)
    http_413 = ("<h1>REQUEST ENTITY TOO LARGE</h1>", "text/html", 413)
    http_414 = ("<h1>REQUEST-URI TOO LONG</h1>", "text/html", 414)
    http_415 = ("<h1>UNSUPPORTED MEDIA TYPE</h1>", "text/html", 415)
    http_416 = ("<h1>REQUESTED RANGE NOT SATISFIABLE</h1>", "text/html", 416)
    http_417 = ("<h1>EXPECTATION FAILED</h1>", "text/html", 417)
    http_500 = ("<h1>INTERNAL SERVER ERROR</h1>", "text/html", 500)
    http_501 = ("<h1>NOT IMPLEMENTED</h1>", "text/html", 501)
    http_502 = ("<h1>BAD GATEWAY</h1>", "text/html", 502)
    http_503 = ("<h1>SERVICE UNAVAILABLE</h1>", "text/html", 503)
    http_504 = ("<h1>GATEWAY TIMEOUT</h1>", "text/html", 504)
    http_505 = ("<h1>HTTP VERSION NOT SUPPORTED</h1>", "text/html", 505)


class FeaspServer:
    """ FeaspServer, 遵守WSGI规范,
      基于wsgiref的make_server, WSGIRequestHandler, WSGIServer实现的Server """

    def __init__(self, host="127.0.0.1", port=8080):
        self.host = host
        self.port = int(port)

    def run(self, app):
        from wsgiref.simple_server import make_server
        from wsgiref.simple_server import WSGIRequestHandler, WSGIServer

        f_srv = make_server(self.host, self.port, app, WSGIServer,
                            WSGIRequestHandler)
        self.port = f_srv.server_port
        try:
            print(f"{self.__class__.__name__} working on {self.port}...")
            print(f"Please click `http://{self.host}:{self.port}`...")
            f_srv.serve_forever()
        except KeyboardInterrupt:
            f_srv.server_close()
            raise

    def __repr__(self):
        return f"{type(self).__class__.__name__} {self.host}:{self.port}"


class Feasp:
    """ Feasp: 一个简易的Web框架, 基于WSGI规范, 仅用来学习交流
      实现了路由注册(支持GET、POST),
        实现WSGI Application, 请求的分发,

      内置各种资源自动处理, 支持在视图路径中定义变量,
        在视图函数中用app.response.session设置cookie

      支持返回字符串、HTML、dict以及Response作为返回值
        可利用make_response、render_template、Response返回

      提供self.request供进入上下文时读取请求信息
        提供self.response供在返回返回值前设置Response的属性

      使用示例:
        from feasp import Feasp

        app = Feasp(__name__)

        @app.route("/", methods=["GET"])
        def index():
            return "Hello Feasp !" """

    # 指向Request类
    request_class = Request

    # 指向Response类
    response_class = Response

    def __init__(self, filename):
        # url与view_func的映射
        self.__url_func_map = {"path_have_var": {}}

        # self.__url_func_map 传入全局字典
        _global_var["url_func_map"] = self.__url_func_map

        # 用户的包文件路径
        self.__user_pkg_abspath = os.path.abspath(os.path.dirname(filename))
        _global_var["user_pkg_abspath"] = self.__user_pkg_abspath

        # 指向当前请求对象, 可使用户访问
        self.request = None

        # 指向当前响应对象, 可供用户设置
        self.response = None

    @staticmethod
    def _deal_static_request(path):
        """ 处理图片、css、js文件相关请求 """

        for bq in (".ico", ".jpg", ".png"):
            if bq in path:
                mimetype = "image/x-icon"
                content = _deal_images(path)
                return content, mimetype, 200

        for bq in (".css", ".js"):
            if bq in path and bq == ".css":
                mimetype = "text/css"
                content = _deal_static(path)
                return content, mimetype, 200
            if bq in path and bq == ".js":
                mimetype = "application/javascript"
                content = _deal_static(path)
                return content, mimetype, 200

    def _deal_view_path(self, func, path, methods):
        """ 处理视图函数中定义的路径 """
        endpoint = func.__name__  # 此处端点为视图函数的名称
        format_mark = re.findall("<string:.*?>", path)
        if format_mark and format_mark[0] in path:
            new_path = "/".join(path.split("/")[:-1])
            self.__url_func_map["path_have_var"][new_path] = (endpoint, func, methods)
        else:
            self.__url_func_map[path] = (endpoint, func, methods)

    def dispatch(self, path, method):
        """ 处理请求并返回对应视图函数的响应 """
        # 处理文件相关的请求
        deal_return = self._deal_static_request(path)
        if deal_return is not None:
            return deal_return

        # 处理视图函数相关请求
        values = self.__url_func_map.get(path, None)
        variable = None
        if values is None:  # 判断path是否携带变量
            for_path, variable = path.split("/")[:-1], path.split("/")[-1]
            path = "/".join(for_path)
            values = self.__url_func_map["path_have_var"].get(path, None)
        if values is None:  # 如果还是None, 抛出错误
            return FeaspError.http_404

        endpoint, view_func, methods = values
        if variable:  # 如果有variable, 则传入视图函数
            view_func_return = view_func(variable)
        else:
            view_func_return = view_func()
        if method not in methods:
            return FeaspError.http_405

        if isinstance(view_func_return, str):
            mimetype = "text/html"
            return view_func_return, mimetype, 200
        elif isinstance(view_func_return, dict):
            view_func_return = json.dumps(view_func_return)
            mimetype = "Application/json"
            return view_func_return, mimetype, 200
        elif isinstance(view_func_return, Response):
            return view_func_return.body, \
                   view_func_return.mimetype, view_func_return.status
        else:
            return FeaspError.http_500

    def route(self, path, methods):
        """ 将路径与视图函数进行绑定 """
        if methods is None:
            methods = [Method.GET]

        def decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            # 处理视图函数的路径
            self._deal_view_path(func, path, methods)
            return wrapper

        return decorator

    def wsgi_apl(self, environ, start_response):
        """ WSGI规定的调用Application
          规定参数为environ, start_response
          environ: 包含全部请求信息的字典, start_response: 可调用对象 """
        self.request = self.request_class(environ)
        self.response = self.response_class("", mimetype="text/html")
        # 进入上下文-----------------------------------------------------------------------
        content, mimetype, status = self.dispatch(self.request.path, self.request.method)
        # 退出上下文-----------------------------------------------------------------------
        self.response.body = content
        self.response.mimetype, self.response.status = mimetype, status
        return self.response(environ, start_response)

    def run(self, host, port):
        """ 入口方法, 调用基于wsgiref实现多线程Server """
        simple_server = FeaspServer(host, port)
        simple_server.run(self.wsgi_apl)


_global_var = {}  # 存一些需要全局使用的变量
_http_local = threading.local()
