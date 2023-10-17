"""
Author: Lns-XueFeng
Create Time: 2023.03.27
Python Version: 3.9

目的: 通过实现一个简单的Web框架来增强我对Web开发的理解
"""


__author__ = "Lns-XueFeng"
__version__ = "0.8"
__license__ = "MIT"


import os
import json
import re
import warnings
import typing as t
import wsgiref
import sqlite3
from contextlib import contextmanager

from werkzeug.local import LocalStack, LocalProxy

from .config import METHOD, REASON_PHRASE
from .config import FEASP_ERROR, FeaspNotFound, NotSupportType


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

    reason_phrase: dict[int, str] = REASON_PHRASE

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


class _RequestContext:
    """
      _RequestContext是一个请求上下文类（在Feasp中使用）
      通过在利用with语句使用_RequestContext的过程中压入与弹出它本身来实现不同用户的相关隔离
      此类代指了app, request, session等，用于实现全局可用但不会错乱的对象供用户使用
      简单使用的代码示例：
        req_ctx = _RequestContext(self, environ)
        with req_ctx:
            request = req_ctx.request
            ...
        with _RequestContext(self, environ):
            request = req_ctx.request
            ...
    """

    def __init__(self, app, environ: dict):
        # 指向Feasp的实例对象
        self.app = app
        # 指向框架用户的url和func的映射关系
        self.url_func_map: dict = app.url_func_map
        # 指向请求的相关解析信息
        self.request: Request = app.request_class(environ)
        # 会话对象用于设置cookie
        self.session: dict = {}

    def __enter__(self):
        _request_ctx_stack.push(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_tb is None:
            _request_ctx_stack.pop()


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
            warnings.warn("A KeyboardInterrupt was happend...")
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

    @property
    def url_func_map(self) -> dict:
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
    def _deal_static_request(path: str) -> t.Optional[tuple[t.Union[str, bytes], str, int]]:
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

    def _deal_view_func(self, func: t.Callable, path: str, methods: list[str]) -> None:
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

    def dispatch(self, path: str, method: str) -> tuple[t.Union[str, bytes], str, int]:
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

    def request_context(self, environ: dict) -> _RequestContext:
        """
          包装_RequestContext，以提供更清晰的代码逻辑
        """
        return _RequestContext(self, environ)

    def make_response(self, body: str, status: int, mimetype: str) -> Response:
        """
          抽象出处理response的过程，以提供更清晰的代码逻辑
        """
        response = self.response_class()
        response.body = body
        response.status = status
        response.mimetype = mimetype
        if session is not None:
            for k, v in session.items():
                response.set_cookie(k, v)
            session.clear()
        return response

    def wsgi_apl(self, environ: dict, start_response: t.Callable) -> list[bytes]:
        """
          符合WSGI规定的可调用的应用程序，
          定义的参数为environ、start_response，
          environ：包括所有请求，start_response：可调用对象
        """
        req_ctx = self.request_context(environ)
        with req_ctx:
            request = req_ctx.request
            # -------------------------------------------------------------------------------
            body, status, mimetype = self.dispatch(request.path, request.method)
            # -------------------------------------------------------------------------------
            response = self.make_response(body, status, mimetype)
            return response(environ, start_response)

    def run(self, host: str, port: int) -> None:
        """
          入口方法，可运行起基于WSGI实现的Feasp Server
        """
        simple_server = FeaspServer(host, port)
        simple_server.run(self.wsgi_apl)


class SimpleSqlite:
    """
      SimpleSqlite基于Sqlite3提供了更简单便捷的方式来进行数据库的简单的增删改查

      简单使用举例一：
        from feasp import SimpleSqlite

        handler = SimpleSqlite("test.db")
        handler.create_table("Student", ["Name", "Age"])
        handler.insert("Student", ("Lns_XueFeng", 22))
        handler.insert_many("Student", [("XueFeng", 22), ("XueXue", 25), ("XueLian", 28)])
        handler.delete("Student", {"Name": "Lns_XueFeng", "Age": 22})
        handler.update("Student", {"Name": "Lns-XueFeng"}, ("Name", "Lns_XueFeng"))
        res = handler.fetch_all("Student")
        print(res)
        handler.close()

      简单使用举例二：
        from feasp import SimpleSqlite

        with SimpleSqlite("test.db") as handler:
            handler.create_table("Student", ["Name", "Age"])
            handler.insert("Student", ("Lns_XueFeng", 22))
            handler.insert_many("Student", [("XueFeng", 22), ("XueXue", 25), ("XueLian", 28)])
            handler.delete("Student", {"Name": "Lns_XueFeng", "Age": 22})
            handler.update("Student", {"Name": "Lns-XueFeng"}, ("Name", "Lns_XueFeng"))
            res = handler.fetch_all("Student")
            print(res)

      注意：create_table不可重复调用，数据库表不可重复，不要重复的去创建同名表
    """

    def __init__(self, db_name: str):
        self.__db_name = db_name
        self.__conn = sqlite3.connect(f"{self.__db_name}")
        self.__cursor = self.__conn.cursor()

    def __repr__(self):
        return f"<SimpleSqlite Database: {self.__db_name}>"

    def create_table(self, tb_name: str, colum_name: list[str]) -> None:
        """
          :param tb_name: 数据库表的名称
          :param colum_name_and_type: 一个字典，键是列名，值是列的类型
        """
        count = 1
        create_table_sql = f"CREATE TABLE {tb_name}("

        for c_name in colum_name:
            if count == 1:
                create_table_sql += f"{c_name}"
                count = count + 1
            else:
                create_table_sql += f", {c_name}"
        create_table_sql += ')'

        self.__cursor.execute(create_table_sql)
        self.__conn.commit()

    def insert(self, tb_name: str, value: tuple) -> None:
        """
          :param tb_name: 数据库表的名称
          :param values: 需要给每一列添加的值
        """
        insert_column_sql = f"INSERT INTO {tb_name} VALUES {value}"

        self.__cursor.execute(insert_column_sql)
        self.__conn.commit()

    def insert_many(self, tb_name: str, values: list[tuple]) -> None:
        """
          :param tb_name: 数据库表的名称
          :param values: 需要添加的多行数据
        """
        for value in values:
            self.insert(tb_name, value)

    def delete(self, tb_name, column_and_value: dict) -> None:
        """
          :param tb_name: 数据库表的名称
          :param column_and_value: 键为列名，值为列对应多个行值中需要删除的
        """
        count = 1
        delete_column_sql = f"DELETE FROM {tb_name} where"

        for c_name, v_name in column_and_value.items():
            condition = f" {c_name}='{v_name}'"
            if count == 1:
                delete_column_sql += condition
                count = count + 1
            else:
                delete_column_sql += " and" + condition

        self.__cursor.execute(delete_column_sql)
        self.__conn.commit()

    def update(self, tb_name, column_and_value: dict, row: tuple) -> None:
        """
          :param tb_name: 数据库表的名称
          :param column_and_value: 键为需修改的列名，值为要修改的新值
          :param row: 此元组用来确定需修改的行，第一个元素为列名，第二个元素为这一列的元素
        """
        assert len(row) == 2
        count = 1
        update_column_sql = f"UPDATE {tb_name} set"

        for c_name, v_name in column_and_value.items():
            condition = f" {c_name}='{v_name}'"
            if count == 1:
                update_column_sql += condition
                count = count + 1
            else:
                update_column_sql += " and" + condition
        update_column_sql += f" where {row[0]}='{row[1]}'"

        self.__cursor.execute(update_column_sql)
        self.__conn.commit()

    def fetch_all(self, tb_name: str) -> list:
        """
          :param tb_name: 数据库表的名称
        """
        fetch_all_sql = f"SELECT * FROM {tb_name}"

        result = self.__cursor.execute(fetch_all_sql)
        self.__conn.commit()
        return result.fetchall()

    def close(self):
        """ 操作完成时调用此方法关闭游标以及连接 """
        self.__cursor.close()
        self.__conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__cursor.close()
        self.__conn.close()


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


def render_template(filename: str, **context: dict) -> str:
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


def url_for(endpoint: str, filename: t.Optional[str] = None) -> str:
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


@contextmanager
def connect(db_name: str) -> None:
    """
      提供一个更为简洁明了且安全的接口以供对SimpleSqlite的使用
      使用示例（推荐使用此接口，而不是直接使用SimpleSqlite）：
      with connect('test.db') as handler:
          handler.create_table("Student", ["Name", "Age"])
          handler.insert("Student", ("Lns_XueFeng", 22))
          handler.insert_many("Student", [("XueFeng", 22), ("XueXue", 25), ("XueLian", 28)])
          handler.delete("Student", {"Name": "Lns_XueFeng", "Age": 22})
          handler.update("Student", {"Name": "Lns-XueFeng"}, ("Name", "Lns_XueFeng"))
          res = handler.fetch_all("Student")
          print(res)
      注意：create_table不可重复调用，数据库表不可重复，不要重复的去创建同名表
    """
    try:
        handler = SimpleSqlite(db_name)
        yield handler
    finally:
        handler.close()


_global_var: dict[t.Any, t.Any] = {}
_request_ctx_stack: LocalStack = LocalStack()
request: Request = LocalProxy(lambda: _request_ctx_stack.top.request)   # 供用户使用的全局request对象
session: dict = LocalProxy(lambda: _request_ctx_stack.top.session)   # 供用户使用的全局session对象
