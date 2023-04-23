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
        if '.' not in var_name:
            value = self.context.get(var_name)
        else:   # 处理obj.attr
            obj, attr = var_name.split('.')
            value = getattr(self.context.get(obj), attr)

        if not isinstance(value, str):
            value = str(value)
        return value

    def _deal_code_segment(self):
        """ 处理所有匹配出来的代码段 """
        is_for_snippet = False   # 标记是否为for语句代码段

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
                    snippet = ''

            if is_for_snippet:
                # 如果是for语句代码段, 需要进行二次处理, 暂时保存到for语句片段列表中
                self.for_snippet.append(snippet)
            else:
                # 如果是模板变量, 直接将变量值追加到结果列表中
                self.finally_result.append(snippet)

    def _parse_for_snippet(self):
        """ 解析for语句片段代码 """
        result = []   # 保存for语句片段解析结果
        if self.for_snippet:
            # 解析for语句开始代码片段
            words = self.for_snippet[0][2:-2].strip().split()
            iter_obj_from_context = self.context.get(words[-1])
            for value in iter_obj_from_context:
                # 遍历for语句片段的代码块, 将value与循环体内的代码块拼接
                for snippet in self.for_snippet[1:]:
                    if snippet.startswith("{{"):
                        var = snippet[2:-2].strip()
                        if '.' not in var:
                            snippet = value
                        else:
                            obj, attr = var.split('.')
                            snippet = getattr(value, attr)
                    # 将解析出来的循环变量结果追加到for语句片段解析结果列表中
                    if not isinstance(snippet, str):
                        snippet = str(snippet)
                    result.append(snippet)
        return result

    def render(self):
        """ 组合原生html代码段与渲染完的语句代码片段 """
        for_result = self._parse_for_snippet()   # 获取for语句片段解析结果
        return "".join(self.finally_result).format(''.join(for_result))

    def __repr__(self):
        return f"<{type(self).__name__} {self.context}>"


class Request:

    """ Request为解析类, 解析WSGI中的HTTP参数
      self.url_scheme: wsgi支持的http协议
      self.protocol: http协议类型及版本
      self.method: http请求方法
      self.path: http请求路径(资源路径)
      self.url_args: url中的查询参数
      self.request_uri: 请求uri
      self.http_host: 请求ip与port
      self.connection: HTTP请求是keep-alive还是close
      self.platform: 请求来自什么系统平台
      self.user_agent: 其中包含了请求的诸多身份信息
      self.url: 完整的请求url, 包括了协议类型, ip:prot/域名, 资源路径
      self.cookie: 存储已解析的来自浏览器的cookie
      self.form: 如果有POST请求则进行表单数据存储 """

    def __init__(self, environ):
        self.url_scheme = environ.get("wsgi.url_scheme")
        self.protocol = environ.get('SERVER_PROTOCOL')
        self.method = environ.get("REQUEST_METHOD")
        self.path = environ.get("PATH_INFO")
        self.url_args = environ.get("QUERY_STRING")
        self.request_uri = environ.get("REQUEST_URI")
        self.http_host = environ.get("HTTP_HOST")
        self.connection = environ.get("HTTP_CONNECTION")
        self.platform = environ.get("HTTP_SEC_CH_UA_PLATFORM")
        self.user_agent = environ.get("HTTP_USER_AGENT")
        self.url = self.get_url()
        self.cookie = self.get_cookie(environ)
        self.form = self.get_form(environ)

    @staticmethod
    def get_cookie(environ):
        """ 得到易于用户读取的cookie字典 """
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
        """ 得到易于用户读取的form字典 """
        rb_size = int(environ.get('CONTENT_LENGTH', 0))
        rb = environ["wsgi.input"].read(rb_size)
        rb_form = parse_qs(rb)
        # 需要将rb_form中bytes的key和value解码成字符串
        sb_form = {bk.decode(): [bv[0].decode()][0] for bk, bv in rb_form.items()}
        return sb_form

    def get_url(self):
        """ 得到易于用户使用的完整url """
        url, header = None, None
        if self.url_scheme:
            header = self.url_scheme + "://"
        if self.url_scheme and self.request_uri and self.http_host:
            url = header + self.http_host + self.request_uri
        return url

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

    def __call__(self, environ, start_response):
        """ 返回包装后的响应, 以传递给客户端 """
        global session
        if len(session) > 0:
            cookie_str = ""
            for k, v in session.items():
                cookie_str = cookie_str + f"{k}={v} "
            self.headers.update(
                {"Set-Cookie": f"{cookie_str}"}
            )
        # 设置完后清空session: 之前是将session重新赋值{}, 这样并不能清空session
        session.clear()

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
      实现了路由注册(支持GET、POST), WSGI Application,
        请求的分发, 支持多线程及响应安全返回

      各种资源自动处理, 在视图路径中定义变量,
        在视图函数中用session设置cookie, 用app.request读取相关属性

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

    def _deal_static_request(self, path):
        """ 处理图片、css、js文件相关请求 """

        for bq in (".ico", ".jpg", ".png"):
            if bq in path:
                mimetype = "image/x-icon"
                content = _deal_images(path)
                return self.response_class(content, mimetype=mimetype)

        for bq in (".css", ".js"):
            if bq in path and bq == ".css":
                mimetype = "text/css"
                content = _deal_static(path)
                return self.response_class(content, mimetype=mimetype)
            if bq in path and bq == ".js":
                mimetype = "application/javascript"
                content = _deal_static(path)
                return self.response_class(content, mimetype=mimetype)

    def _deal_view_path(self, func, path, methods):
        """ 处理视图函数中定义的路径 """
        endpoint = func.__name__  # 此处端点为视图函数的名称
        format_mark = re.findall("<string:.*?>", path)
        if format_mark and format_mark[0] in path:
            new_path = "/".join(path.split("/")[:-1])
            self.__url_func_map["path_and_var"][new_path] = (endpoint, func, methods)
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

            # 处理视图函数的路径
            self._deal_view_path(func, path, methods)
            return wrapper
        return decorator

    def wsgi_apl(self, environ, start_response):
        """ WSGI规定的调用Application
          规定参数为environ, start_response
          environ: 包含全部请求信息的字典, start_response: 可调用对象 """

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
        """ Feasp启动函数, 提供两种server """
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
