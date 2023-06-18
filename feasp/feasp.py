"""
Author: Lns-XueFeng
Create Time: 2023.03.27

目的: 通过实现一个简单的Web框架来增强我对Web开发的理解
"""


__author__ = "Lns-XueFeng"
__version__ = "0.7"
__license__ = "MIT"


import os
import json
import re
import typing as t
import wsgiref


METHOD: dict[str, str] = {
    "GET": "GET",
    "POST": "POST",
    "DELETE": "DELETE",
    "PUT": "PUT",
    "HEAD": "HEAD",
    "CONNECT": "CONNECT",
    "OPTIONS": "OPTIONS",
    "TRACE": "TRACE",
}


FEASP_ERROR: dict[str, tuple[str, str, int]] = {
    "HTTP_100": ("<h1>CONTINUE</h1>", "text/html", 101),
    "HTTP_101": ("<h1>SWITCHING PROTOCOLS</h1>", "text/html", 101),
    "HTTP_200": ("<h1>OK</h1>", "text/html", 200),
    "HTTP_201": ("<h1>CREATED</h1>", "text/html", 201),
    "HTTP_202": ("<h1>ACCEPTED</h1>", "text/html", 202),
    "HTTP_203": ("<h1>NON-AUTHORITATIVE INFORMATION</h1>", "text/html", 203),
    "HTTP_204": ("<h1>NO CONTENT</h1>", "text/html", 204),
    "HTTP_205": ("<h1>RESET CONTENT</h1>", "text/html", 205),
    "HTTP_206": ("<h1>PARTIAL CONTENT</h1>", "text/html", 206),
    "HTTP_300": ("<h1>MULTIPLE CHOICES</h1>", "text/html", 300),
    "HTTP_301": ("<h1>MOVED PERMANENTLY</h1>", "text/html", 301),
    "HTTP_302": ("<h1>FOUND</h1>", "text/html", 302),
    "HTTP_303": ("<h1>SEE OTHER</h1>", "text/html", 303),
    "HTTP_304": ("<h1>NOT MODIFIED</h1>", "text/html", 304),
    "HTTP_305": ("<h1>USE PROXY</h1>", "text/html", 305),
    "HTTP_306": ("<h1>RESERVED</h1>", "text/html", 306),
    "HTTP_307": ("<h1>TEMPORARY REDIRECT</h1>", "text/html", 307),
    "HTTP_400": ("<h1>BAD REQUEST</h1>", "text/html", 400),
    "HTTP_401": ("<h1>UNAUTHORIZED</h1>", "text/html", 401),
    "HTTP_402": ("<h1>PAYMENT REQUIRED</h1>", "text/html", 402),
    "HTTP_403": ("<h1>FORBIDDEN</h1>", "text/html", 403),
    "HTTP_404": ("<h1>NOT FOUND</h1>", "text/html", 404),
    "HTTP_405": ("<h1>METHOD NOT ALLOWED</h1>", "text/html", 405),
    "HTTP_406": ("<h1>NOT ACCEPTABLE</h1>", "text/html", 406),
    "HTTP_407": ("<h1>PROXY AUTHENTICATION REQUIRED</h1>", "text/html", 407),
    "HTTP_408": ("<h1>REQUEST TIMEOUT</h1>", "text/html", 408),
    "HTTP_409": ("<h1>CONFLICT</h1>", "text/html", 409),
    "HTTP_410": ("<h1>GONE</h1>", "text/html", 410),
    "HTTP_411": ("<h1>LENGTH REQUIRED</h1>", "text/html", 411),
    "HTTP_412": ("<h1>PRECONDITION FAILED</h1>", "text/html", 412),
    "HTTP_413": ("<h1>REQUEST ENTITY TOO LARGE</h1>", "text/html", 413),
    "HTTP_414": ("<h1>REQUEST-URI TOO LONG</h1>", "text/html", 414),
    "HTTP_415": ("<h1>UNSUPPORTED MEDIA TYPE</h1>", "text/html", 415),
    "HTTP_416": ("<h1>REQUESTED RANGE NOT SATISFIABLE</h1>", "text/html", 416),
    "HTTP_417": ("<h1>EXPECTATION FAILED</h1>", "text/html", 417),
    "HTTP_500": ("<h1>INTERNAL SERVER ERROR</h1>", "text/html", 500),
    "HTTP_501": ("<h1>NOT IMPLEMENTED</h1>", "text/html", 501),
    "HTTP_502": ("<h1>BAD GATEWAY</h1>", "text/html", 502),
    "HTTP_503": ("<h1>SERVICE UNAVAILABLE</h1>", "text/html", 503),
    "HTTP_504": ("<h1>GATEWAY TIMEOUT</h1>", "text/html", 504),
    "HTTP_505": ("<h1>HTTP VERSION NOT SUPPORTED</h1>", "text/html", 505),
}


class FeaspNotFound(Exception):
    pass


def _fetch_images(image_path: str) -> bytes:
    """
      处理图片相关的请求，支持jpg、png、ico格式的图片
      image_path: 相对于static目录的路径
      例如: 在`example/static`之中的`favicon。ico`
      你应该在html中这样写: /static/favicon.ico 或者 使用 url_for 函数
      :raise FeaspNotFound
    """

    if image_path == "/favicon.ico":
        image_path = image_path[1:]
        filepath = os.path.join(_global_var["user_pkg_abspath"], 'static', image_path)

    elif image_path[0] == "/":
        image_path = image_path[1:]
        filepath = os.path.join(_global_var["user_pkg_abspath"], image_path)

    if os.path.exists(filepath):
        with open(filepath, "rb") as fp:
            content = fp.read()
        return content
    raise FeaspNotFound(f"not found {image_path}")


def _fetch_files(link_path: str) -> str:
    """
      处理css、js相关文件的请求
      link_path: 相对于static目录的路径
      例如: 在`example/static`之中的`style.css`
      你应该在html中这样写: /static/style.css 或者 使用 url_for 函数
      :raise FeaspNotFound
    """

    if link_path[0] == "/":
        link_path = link_path[1:]

    filepath = os.path.join(_global_var["user_pkg_abspath"], link_path)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as fp:
            content = fp.read()
        return content
    raise FeaspNotFound(f"not found {link_path}")


class Request:
    """
      Request类是一个解析类，解析由WSGI传来的environ字典，
      然后我们可以从该字典中得到HTTP的字段, 以提供给用户使用
    """

    def __init__(self, environ: dict):
        self.__environ: dict = environ
        self.__url: str = self.__get_url()
        self.__form: dict = self.__get_form()
        self.__cookies: dict = self.__get_cookies()

    @property
    def environ(self) -> dict:
        """ HTTP请求相关信息，字典类型 """
        return self.__environ

    @property
    def url(self) -> str:
        """ 获取用户易于使用的完整网址 """
        return wsgiref.util.request_uri(self.__environ)

    @property
    def form(self) -> dict:
        """ 获取易于用户阅读的表单字典 """
        return self.__form

    @property
    def cookies(self) -> dict:
        """ 获取易于用户阅读的cookie字典 """
        return self.__cookies

    @property
    def protocol(self) -> str:
        """ HTTP协议类型和版本 """
        return self.environ.get("SERVER_PROTOCOL", "")

    @property
    def method(self) -> str:
        """ HTTP请求方法 """
        return self.environ.get("REQUEST_METHOD", "GET")

    @property
    def url_scheme(self) -> str:
        """ WSGI支持的HTTP协议 """
        # self.environ.get("wsgi.url_scheme", "")
        return wsgiref.util.guess_scheme(self.__environ)

    @property
    def referer(self) -> str:
        """ 当前网页的来源页面 """
        return self.environ.get("HTTP_REFERER", "")

    @property
    def path(self) -> str:
        """ HTTP请求路径（资源路径） """
        return self.environ.get("PATH_INFO", "")

    @property
    def url_args(self) -> str:
        """ 网址中的查询参数 """
        return self.environ.get("QUERY_STRING", "")

    @property
    def connection(self) -> str:
        """ HTTP 连接状态码 """
        return self.environ.get("HTTP_CONNECTION", "")

    @property
    def platform(self) -> str:
        """ HTTP请求来自哪个系统平台 """
        return self.environ.get("HTTP_SEC_CH_UA_PLATFORM", "")

    @property
    def user_agent(self) -> str:
        """ 它包含请求客户端的大量身份相关的信息 """
        return self.environ.get("HTTP_USER_AGENT", "")

    def __get_form(self) -> dict:
        if self.environ.get("CONTENT_LENGTH", "") == "":
            rb_size = 0
        else:
            rb_size = int(self.environ.get("CONTENT_LENGTH", 0))
        wsgi_input = self.environ.get("wsgi.input", "")
        if not wsgi_input == "":
            rb = wsgi_input.read(rb_size)
            from urllib.parse import parse_qs
            rb_form = parse_qs(rb)
            # 将rb_form中字节的键和值解码为字符串
            sb_form = {bk.decode(): [bv[0].decode()][0] for bk, bv in rb_form.items()}
            return sb_form
        return {}

    def __get_cookies(self) -> dict:
        cookies = {}
        http_cookie = self.environ.get("HTTP_COOKIE")
        if http_cookie is not None:
            cl = http_cookie.split(" ")
            for kv in cl:
                k, v = tuple(kv.split("="))
                cookies[k] = v
        return cookies

    def __get_url(self) -> str:
        url, header = "", ""
        http_host = self.environ.get("HTTP_HOST")
        if self.url_scheme:
            header = self.url_scheme + "://"
        if self.url_scheme and http_host:
            url = header + http_host + self.path + self.url_args
        return url

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.method} {self.protocol} {self.path}>"


class Response:
    """
      Response是响应类，它是基于WSGI将返回数据包装为符合规范的响应，
      支持字节和非字节的数据进行包装并返回
    """

    reason_phrase: dict[int, str] = {
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

    def __init__(
            self,
            body: str = None,
            mimetype: str = None,
            status: int = None
    ) -> None:
        # 响应正文
        self.body: str = body

        # 响应的状态代码
        self.status: int = status

        # 设置响应的类型
        self.mimetype: str = mimetype

        # 响应头，可动态添加多个字段
        self.headers: dict[str, str] = {
            "Content-Type": f"{self.mimetype}; charset=utf-8",
        }

    def set_cookie(self, key: str, value: str) -> None:
        """
          添加一个cookie字段进响应，
          并且返回给客户端浏览器，客户端将会存储它
        """
        key = "".join(key.split(" "))
        value = "".join(value.split(" "))
        add_cookie = f"{key}={value} "
        old_cookie = self.headers.get("Set-Cookie", "")
        new_cookie = old_cookie + add_cookie
        self.headers["Set-Cookie"] = new_cookie

    def __call__(self, environ: dict, start_response: t.Callable) -> list[bytes]:
        """
          返回要传递给客户端的包装响应
        """
        start_response(
            f"{self.status} {self.reason_phrase[self.status]}",
            [(k, v) for k, v in self.headers.items()]
        )

        if isinstance(self.body, bytes):
            return [self.body]
        return [self.body.encode("utf-8")]

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.mimetype}" \
               f" {self.status} {self.reason_phrase[self.status]}>"


class FeaspTemplate:
    """
      Template是一个渲染类，用于解析HTML并重新拼接的模板，
      当前，支持定义变量、定义url_for函数、单个If语句、单层For循环：
        1.定义变量的占位符为: {{}},
        变量在花括号内定义，例如 {{ name }}
        2.定义url_for函数: {{ url_for('static', filename='head.jpg') }}
        3.定义判断语句（目前仅能定义单个If判断）:
            {% If name_list: %}
                {{ name_list[0] }}
            {% Endif %}
        4.定义循环语句（目前仅能定义单个且单层For循环）:
            {% For name in name_list %}
                {{ name }}
            {% Endfor %}
        5.定义注释:
            {# 这是一个注释 #}
        注意：支持一个HTML文件内同时定义多个For与If语句但不支持其之间的相互嵌套
      注意：传入的变量必须与模板中定义的变量匹配，并且以key=value的形式传递给渲染函数
    """

    def __init__(self, text: str, context: dict) -> None:
        # self.text指向内存中的HTML字符串
        self.text: str = text

        # self.context指向内存中用户传入的上下文变量
        self.context: dict = context

        # 保存从self.text中匹配的所有的模板变量、语句
        self.snippet_list: list[str] = re.split("({{.*?}}|{%.*?%}|{#.*?#})", self.text, flags=re.DOTALL)

        # 保存从HTML解析的语句代码段
        self.grammar_snippet: list[str] = []

        # 保存从HTML解析的if语句代码段
        self.if_snippet: list[str] = []

        # 保存从HTML解析的for语句代码段
        self.for_snippet: list[str] = []

        # 保存从HTML解析的注释语句代码段
        self.comments_snippet: list[str] = []

        # 保存最终渲染拼接完的HTML字符串
        self.finally_result: list[str] = []

        # 处理self.snippet_list中的代码段
        self._deal_code_segment()

    def _get_var_value(self, var_name: str) -> str:
        """
          根据变量名称获取变量的值
        """
        if "." not in var_name:
            value = self.context.get(var_name)
        elif "url_for" in var_name:   # 支持在template中定义url_for函数
            value = eval(var_name)
        else:  # 处理obj.attr
            obj, attr = var_name.split(".")
            value = getattr(self.context.get(obj), attr)

        if not isinstance(value, str):
            value = str(value)
        return value

    def _deal_code_segment(self) -> None:
        """
          处理所有匹配的代码段
        """
        is_grammar_snippet = False   # 标记它是否是控制语句代码段
        is_if_snippet = False   # 标记它是否为if语句代码段
        is_for_snippet = False   # 标记它是否为for语句代码段
        is_comments_snippet = False   # 标记它是否是注释代码段

        for snippet in self.snippet_list:
            # 解析模板变量
            if snippet.startswith("{{"):
                if not is_for_snippet:
                    var_name = snippet[2:-2].strip()
                    snippet = self._get_var_value(var_name)
            elif snippet.startswith("{#"):
                is_comments_snippet = True   # 标记
            # 给for语句在最终HTML字符串中占位
            elif snippet.startswith("{%"):
                if "in" in snippet:
                    is_for_snippet = True   # 标记
                elif "If" in snippet:
                    is_if_snippet = True   # 标记
                else:
                    snippet = ""
                    is_if_snippet = False
                    is_for_snippet = False
                is_grammar_snippet = True   # 标记
            else:
                is_grammar_snippet = False
                is_comments_snippet = False

            if is_for_snippet:
                # 如果是for语句代码段，它需要添加至self.for_snippet以待处理
                self.for_snippet.append(snippet)
                self.grammar_snippet.append(snippet)
            elif is_if_snippet:
                # 如果是if语句代码段，它需要添加至self.if_snippet以待处理
                self.if_snippet.append(snippet)
                self.grammar_snippet.append(snippet)
            elif is_comments_snippet:
                # 如果是注释语句代码段，将它添加至self.comments_snippet什么也不干
                self.comments_snippet.append(snippet)
            else:
                # 如果是模板变量，则将变量值直接附加到结果列表
                self.finally_result.append(snippet)

        for snippet in self.snippet_list:
            # 将语法语句作为整体进行处理，预留一个空位即可
            if snippet.startswith("{%"):
                self.finally_result.append("{}")
                break

    def _parse_for_snippet(self, words: list) -> list[str]:
        """
          解析for语句片段的代码
        """
        result = []   # 保存for语句片段的解析结果
        iter_obj_from_context = self.context.get(words[-1])
        for value in iter_obj_from_context:
            for snippet in self.for_snippet[1:]:
                if snippet.startswith("{{"):
                    var = snippet[2:-2].strip()
                    if "." not in var:
                        snippet = value
                    else:
                        obj, attr = var.split(".")
                        snippet = getattr(value, attr)
                if not isinstance(snippet, str):
                    snippet = str(snippet)
                result.append(snippet)
        return result

    def _parse_if_snippet(self, words: list) -> list[str]:
        """
          解析if语句片段的代码
        """
        result = []   # 保存if语句片段的解析结果
        if_obj_from_context = self.context.get(words[-1])
        if if_obj_from_context:
            for snippet in self.if_snippet[1:]:
                if snippet.startswith("{{"):
                    var = snippet[2:-2].strip()
                    if "." not in var:
                        snippet = value
                    else:
                        obj, attr = var.split(".")
                        snippet = getattr(value, attr)
                if not isinstance(snippet, str):
                    snippet = str(snippet)
                result.append(snippet)
        return result

    def _parse_grammar_snippet(self) -> list[str]:
        """
          处理语法语句代码片段，
          支持在同一HTML文件内定义多个控制语句但不支持其之间的嵌套关系
        """
        result = []
        if self.grammar_snippet:
            for snippet in self.grammar_snippet:
                words = snippet[2:-2].strip().split()
                if words[0] == "If":
                    if_result = self._parse_if_snippet(words)
                    result.extend(if_result)
                if words[0] == "For":
                    for_result = self._parse_for_snippet(words)
                    result.extend(for_result)
        return result

    def render(self) -> str:
        """
          将self.finally_result与result合并，
          self.finally_result为还未结合类似于for语句这样的执行结果的字符串列表
        """
        result = self._parse_grammar_snippet()
        return "".join(self.finally_result).format("".join(result))

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.context}>"


class FeaspServer:
    """
      FeaspServer类，遵守WSGI规范，利用以下组件实现的服务器程序，
      wsgiref，make_server, WSGIRequestHandler, WSGIServer implemented server
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8080) -> None:
        self.host: str = host
        self.port: int = int(port)

    def run(self, app: t.Callable) -> None:
        from wsgiref.simple_server import make_server
        from wsgiref.simple_server import WSGIRequestHandler, WSGIServer

        f_srv = make_server(self.host, self.port, app, WSGIServer, WSGIRequestHandler)
        self.port = f_srv.server_port
        try:
            print(f"{self.__class__.__name__} working on {self.port}...")
            print(f"Please click `http://{self.host}:{self.port}`...")
            f_srv.serve_forever()
        except KeyboardInterrupt:
            f_srv.server_close()
            raise

    def __repr__(self) -> str:
        return f"{type(self).__class__.__name__} {self.host}:{self.port}"


class Feasp:
    """
      Feasp是一个简单的单线程的Web框架，基于WSGI标准，仅用于学习与交流，

      实现了路由注册（支持GET，POST），WSGI应用程序，请求的分发等，

      内置各种资源自动处理，支持在视图路径中定义变量，
      使用app.response.session可在视图函数中设置cookie，

      支持返回字符串、HTML、字典和响应作为返回值，
      亦可使用make_response，render_template函数返回，

      提供self.request以在进入上下文时可以读取请求信息，
      提供self.response以在返回返回值之前可以对Response进行设置

      简单的使用代码示例:
        from feasp import Feasp

        app = Feasp(__name__)

        @app.route("/", methods=["GET"])
        def index():
            return "Hello Feasp !"
    """

    # 指向请求类
    request_class: t.Any = Request

    # 指向响应类
    response_class: t.Any = Response

    def __init__(self, filename: str) -> None:
        # 保存URL与view_func的映射
        self.__url_func_map: dict = {"path_have_var": {}}

        # self.__url_func_map：传入全局字典
        _global_var["url_func_map"] = self.__url_func_map

        # 获取用户程序包的绝对路径，以便于后续构建路径等
        self.__user_pkg_abspath: str = os.path.abspath(os.path.dirname(filename))
        _global_var["user_pkg_abspath"] = self.__user_pkg_abspath

        # 指向用户可以访问的当前请求对象，在进入上下文时可用
        self.request: t.Any = None

        # 指向当前响应对象，该对象可用于用户设置，在进入上下文时可用
        self.response: t.Any = None

    @property
    def url_func_map(self):
        """
          让用户可以查看相对路径与视图函数的映射
        """
        url_and_func = {}
        for k in self.__url_func_map:
            if k == "path_have_var":
                for j in self.__url_func_map[k]:
                    url_and_func[j] = self.__url_func_map[k][j][0]
            else:
                url_and_func[k] = self.__url_func_map[k][0]
        return url_and_func

    @staticmethod
    def _deal_static_request(
            path: str
    ) -> t.Optional[tuple[t.Union[str, bytes], str, int]]:
        """
          处理对图像、CSS和js文件的请求
        """
        for bq in (".ico", ".jpg", ".png"):
            if bq in path:
                mimetype = "image/x-icon"
                content = _fetch_images(path)
                return content, 200, mimetype

        for bq in (".css", ".js"):
            if bq in path and bq == ".css":
                mimetype = "text/css"
                content = _fetch_files(path)
                return content, 200, mimetype
            if bq in path and bq == ".js":
                mimetype = "application/javascript"
                content = _fetch_files(path)
                return content, 200, mimetype

    def _deal_view_func(
            self,
            func: t.Callable,
            path: str,
            methods: list[str]
    ) -> None:
        """
          处理视图函数中定义的路径
        """
        endpoint = func.__name__  # 这里的端点是视图函数的名称
        format_mark = re.findall("<string:.*?>", path)
        if format_mark and format_mark[0] in path:
            new_path = "/".join(path.split("/")[:-1])
            self.__url_func_map["path_have_var"][new_path] = (endpoint, func, methods)
        else:
            self.__url_func_map[path] = (endpoint, func, methods)

    def dispatch(
            self,
            path: str,
            method: str
    ) -> tuple[t.Union[str, bytes], str, int]:
        """
          处理传来的请求并返回对相应视图函数的响应
        """
        # 处理与文件相关的请求
        deal_return = self._deal_static_request(path)
        if deal_return is not None:
            return deal_return

        # 处理与视图函数相关的请求
        values = self.__url_func_map.get(path, None)
        variable = None
        if values is None:  # 确定路径是否携带变量
            for_path, variable = path.split("/")[:-1], path.split("/")[-1]
            path = "/".join(for_path)
            values = self.__url_func_map["path_have_var"].get(path, None)
        if values is None:  # 如果仍为“无”，则引发错误
            return FEASP_ERROR["HTTP_404"]

        # 进入用户上下文----------------------------------
        endpoint, view_func, methods = values
        if variable:  # 如果有变量，则传入视图函数
            view_func_return = view_func(variable)
        else:
            view_func_return = view_func()
        # 退出用户上下文-----------------------------------

        if method not in methods:
            return FEASP_ERROR["HTTP_405"]

        if isinstance(view_func_return, str):
            mimetype = "text/html"
            return view_func_return, 200, mimetype
        elif isinstance(view_func_return, dict):
            view_func_return = json.dumps(view_func_return)
            mimetype = "application/json"
            return view_func_return, 200, mimetype
        elif isinstance(view_func_return, Response):
            return view_func_return.body, \
                   view_func_return.status, view_func_return.mimetype
        else:
            return FEASP_ERROR["HTTP_500"]

    def route(self, path: str, methods: list[str]) -> t.Callable:
        """
          将用户定义的相对路径与视图函数进行绑定
        """
        if methods is None:
            methods = [METHOD["GET"]]

        def decorator(func):
            self._deal_view_func(func, path, methods)   # 处理视图函数的路径
            return func
        return decorator

    def wsgi_apl(
            self,
            environ: dict,
            start_response: t.Callable) -> list[bytes]:
        """
          符合WSGI规定的可调用的应用程序，
          定义的参数为environ、start_response，
          environ：包括所有请求，start_response：可调用对象
        """
        self.request = self.request_class(environ)
        self.response = self.response_class()
        # -------------------------------------------------------------------------------
        body, status, mimetype = self.dispatch(self.request.path, self.request.method)
        # -------------------------------------------------------------------------------
        self.response.mimetype = mimetype
        self.response.body, self.response.status = body, status
        return self.response(environ, start_response)

    def run(self, host: str, port: int) -> None:
        """
          入口方法，可运行起基于WSGI实现的Feasp Server
        """
        simple_server = FeaspServer(host, port)
        simple_server.run(self.wsgi_apl)


def make_response(
        body: t.Union[str, bytes],
        mimetype: str = "text/html",
        status: int = 200) -> Response:
    """
      提供一个函数，该函数使用以下三个参数自定义响应，
      body: 响应正文, mimetype: 响应类型, status: 响应状态码
    """

    if isinstance(body, str) or isinstance(body, bytes):
        return Response(body, mimetype, status)
    return Response(*FEASP_ERROR["HTTP_500"])


def render_template(
        filename: str,
        **context: dict) -> str:
    """
      渲染在templates目录下的HTML文件，
      因此你需要将所有HTML文件放置在templates目录里面，
      filename是HTML文件名，是templates下的相对路径，
      **context是来自用户传入的上下文变量，它包含键值结构，
      你应该像这样写filename: /index.html or index.html
      具体使用见example目录: example/app.py -> index and show_variable
    """

    if filename[0] == "/":
        filename = filename[1:]

    filepath = os.path.join(
        _global_var["user_pkg_abspath"], "templates", filename)
    with open(filepath, "r", encoding="utf-8") as fp:
        text = fp.read()
    return FeaspTemplate(text, context).render()


def redirect(request_url: str) -> str:
    """
      提供一个便于重定向的函数，
      传入需要跳转的路径，此函数生成相应的响应，
      具体使用见example目录: example/app.py -> redirect_
      :raise FeaspNotFound
    """

    url_func_map = _global_var["url_func_map"]
    if request_url in url_func_map:
        view_func = url_func_map[request_url][1]
        return view_func()
    raise FeaspNotFound("not found view function")


def url_for(
        endpoint: str,
        filename: t.Optional[str] = None) -> str:
    """
      提供一个使构建路径更容易的函数，支持在视图或模板中定义，
      具体使用见example目录: example/templates/index.html和example/app.py/redirect_
      :raise FeaspNotFound
    """
    if endpoint and not filename:
        url_func_map = _global_var["url_func_map"]
        for path, values in url_func_map.items():
            if endpoint in values:
                return path
    elif endpoint and filename:
        base_url = "http://127.0.0.1:8000/"   # 暂时硬编码
        request_url = os.path.join(base_url, endpoint, filename)
        return request_url
    raise FeaspNotFound("not found view function")


_global_var: dict[t.Any, t.Any] = {}  # 保存一些需要全局使用的变量
