"""
Author: Lns-XueFeng
Create Time: 2023.03.27

Why write: Enhance my knowledge of web by implementing a simple web framework
"""

__author__ = "Lns-XueFeng"
__version__ = "0.6"
__license__ = "MIT"

import os
import json
import re
import threading
from urllib.parse import parse_qs
from typing import Optional, Union, Callable, Any


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
      Handling image requests, support jpg, png, ico
      image_path: The file path in the static directory
      For example: `favicon。ico` in `example/static`
      You should write in html: /favicon.ico or favicon.ico
      :raise FeaspNotFound
    """

    if image_path[0] == "/":
        image_path = image_path[1:]

    filepath = os.path.join(_global_var["user_pkg_abspath"], "static", image_path)
    if os.path.exists(filepath):
        with open(filepath, "rb") as fp:
            content = fp.read()
        return content
    raise FeaspNotFound(f"not found {image_path}")


def _fetch_files(link_path: str) -> str:
    """
      Handling requests of css, js file
      link_path: The file path in static directory
      For example: `style.css` in `example/static`
      You should write in html: /style.css or style.css
      :raise FeaspNotFound
    """

    if link_path[0] == "/":
        link_path = link_path[1:]

    filepath = os.path.join(_global_var["user_pkg_abspath"], "static", link_path)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as fp:
            content = fp.read()
        return content
    raise FeaspNotFound(f"not found {link_path}")


class Request(threading.local):
    """ Request is a parse class, WSGI has provided environ,
       then we can get HTTP field from environ, finally give to the user for use """

    def __init__(self, environ: dict):
        self.__environ: dict = environ
        self.__url: str = self.__get_url()
        self.__form: dict = self.__get_form()
        self.__cookies: dict = self.__get_cookies()

    @property
    def environ(self) -> dict:
        """ HTTP request related information, dictionary type """
        return self.__environ

    @property
    def url(self) -> str:
        """ Get a full URL that is easy for users to use """
        return self.__url

    @property
    def form(self) -> dict:
        """ Get a form dictionary that is easy for users to read """
        return self.__form

    @property
    def cookies(self) -> dict:
        """ Get a cookie dictionary that is easy for users to read """
        return self.__cookies

    @property
    def protocol(self) -> str:
        """ HTTP protocol type and version """
        return self.environ.get("SERVER_PROTOCOL", "")

    @property
    def method(self) -> str:
        """ HTTP request method """
        return self.environ.get("REQUEST_METHOD", "GET")

    @property
    def url_scheme(self) -> str:
        """ The HTTP protocol supported by WSGI """
        return self.environ.get("wsgi.url_scheme", "")

    @property
    def referer(self) -> str:
        """ The current web page from where """
        return self.environ.get("HTTP_REFERER", "")

    @property
    def path(self) -> str:
        """ HTTP request path (resource path) """
        return self.environ.get("PATH_INFO", "")

    @property
    def url_args(self) -> str:
        """ Query parameters in url """
        return self.environ.get("QUERY_STRING", "")

    @property
    def connection(self) -> str:
        """ HTTP connection status """
        return self.environ.get("HTTP_CONNECTION", "")

    @property
    def platform(self) -> str:
        """ What system platform the HTTP request came from """
        return self.environ.get("HTTP_SEC_CH_UA_PLATFORM", "")

    @property
    def user_agent(self) -> str:
        """ It contains a lot of identity information for the requesting client """
        return self.environ.get("HTTP_USER_AGENT", "")

    def __get_form(self) -> dict:
        if self.environ.get("CONTENT_LENGTH", "") == "":
            rb_size = 0
        else:
            rb_size = int(self.environ.get("CONTENT_LENGTH", 0))
        rb = self.environ["wsgi.input"].read(rb_size)
        rb_form = parse_qs(rb)
        # You need to decode the key and value of bytes in the rb_form into strings
        sb_form = {bk.decode(): [bv[0].decode()][0] for bk, bv in rb_form.items()}
        return sb_form

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
            url = header + http_host + self.path
        return url

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.method} {self.protocol} {self.path}>"


class Response(threading.local):
    """ Response is response class, it based wrapped of WSGI to return,
      supports wrapped returns for bytes and non-bytes """

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

    def __init__(self,
            body: str, mimetype: str, status: int=200):
        # Response body (response body)
        self.body: str = body

        # The status code of the response
        self.status: int = status

        # Set the type of the response
        self.mimetype: str = mimetype

        # Response headers, multiple fields can be added dynamically
        self.headers: dict[str, str] = {
            "Content-Type": f"{self.mimetype}; charset=utf-8",
        }

    def set_cookie(self, key: str, value: str) -> None:
        """ Set a cookie into Response and return to browser
          and browser will store it """
        key = "".join(key.split(" "))
        value = "".join(value.split(" "))
        add_cookie = f"{key}={value} "
        old_cookie = self.headers.get("Set-Cookie", "")
        new_cookie = old_cookie + add_cookie
        self.headers["Set-Cookie"] = new_cookie

    def __call__(self, environ: dict,
                 start_response: Callable) -> list[bytes]:
        """ Returns the wrapped response to pass to the client """
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


class FeaspSqlite:
    pass


class FeaspTemplate:
    """ Template is a rendering class that parses HTML templates
      Currently, defining variables and loops and rendering them is supported:
        1.defining variables: placeholder is {{}},
        Variables are defined inside curly braces, such as {{ name }}
        2.Define the loop(Currently, only one for loop can be defined):
            {% for name in name_list %}
                {{ name }}
            {% endfor %}
      Note: The variable passed in must match the variable defined in the template,
      and then passed in the form of key=value to the rendering function """

    def __init__(self, text: str, context: dict):
        # text is the HTML code for the template
        self.text: str = text

        # context is the context variable passed in by the user
        self.context: dict = context

        # Matches all template variables, for statements
        self.snippet_list: list[str] = re.split("({{.*?}}|{%.*?%})", self.text, flags=re.DOTALL)

        # Save the for statement snippet parsed from the HTML
        self.for_snippet: list[str] = []

        # Save the final rendered result
        self.finally_result: list[str] = []

        # Handle snippets in self.snippet_list
        self._deal_code_segment()

    def _get_var_value(self, var_name: str) -> str:
        """ Gets the value of the variable based on the variable name """
        if "." not in var_name:
            value = self.context.get(var_name)
        else:  # 处理obj.attr
            obj, attr = var_name.split(".")
            value = getattr(self.context.get(obj), attr)

        if not isinstance(value, str):
            value = str(value)
        return value

    def _deal_code_segment(self) -> None:
        """ Process all matching snippets"""
        is_for_snippet = False  # Mark whether it is a for statement snippet

        for snippet in self.snippet_list:
            # Parse template variables
            if snippet.startswith("{{"):
                if not is_for_snippet:
                    var_name = snippet[2:-2].strip()
                    snippet = self._get_var_value(var_name)
            # Parse template statement
            elif snippet.startswith("{%"):
                if "in" in snippet:
                    is_for_snippet = True
                    self.finally_result.append("{}")
                else:
                    is_for_snippet = False
                    snippet = ""

            if is_for_snippet:
                # If it is a for statement snippet,
                # it needs to be processed twice and temporarily saved to the for statement fragment list
                self.for_snippet.append(snippet)
            else:
                # If is the template variables, append the variable values directly to the result list
                self.finally_result.append(snippet)

    def _parse_for_snippet(self) -> list[str]:
        """ Parse the code of the for statement fragment """
        result = []  # Save the parse result of the for statement fragment
        if self.for_snippet:
            # Parse the for statement to start the code snippet
            words = self.for_snippet[0][2:-2].strip().split()
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

    def render(self) -> str:
        """ Combine the native HTML snippet with the rendered statement snippet """
        for_result = self._parse_for_snippet()  # Get the parse result of the for statement fragment
        return "".join(self.finally_result).format("".join(for_result))

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.context}>"


class FeaspServer:
    """ FeaspServer, obey the WSGI standards,
      based on the wsgiref make_server, WSGIRequestHandler, WSGIServer implemented server """

    def __init__(self, host: str="127.0.0.1", port: int=8080):
        self.host: str = host
        self.port: int = int(port)

    def run(self, app: Callable) -> None:
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

    def __repr__(self) -> str:
        return f"{type(self).__class__.__name__} {self.host}:{self.port}"


class Feasp:
    """ Feasp: a simple web framework, base on WSGI standards, only for learning communication
      Implemented route registration (GET, POST supported),
        Implement WSGI Application, the distribution of requests,

      Built-in automatic processing of various resources, support for defining variables in the view path,
        Set a cookie in the view function with app.response.session

      Support for returning strings, HTML, dict, and Response as return values
        Can use make_response, render_template to return

      Provide self.request to read the request information when entering the context
        Provide self.response to set the Response property before returning the return value

      Use examples:
        from feasp import Feasp

        app = Feasp(__name__)

        @app.route("/", methods=["GET"])
        def index():
            return "Hello Feasp !" """

    # Point to the Request class
    request_class: Any = Request

    # Point to the Response class
    response_class: Any = Response

    def __init__(self, filename: str):
        # The mapping of URLs to view_func
        self.__url_func_map: dict = {"path_have_var": {}}

        # self.__url_func_map: Pass in the global dictionary
        _global_var["url_func_map"] = self.__url_func_map

        # The path to the user's package file
        self.__user_pkg_abspath: str = os.path.abspath(os.path.dirname(filename))
        _global_var["user_pkg_abspath"] = self.__user_pkg_abspath

        # Points to the current request object that can be accessed by the user
        self.request: Any = None

        # Points to the current response object, which is available for user settings
        self.response: Any = None

    @staticmethod
    def _deal_static_request(
            path: str
        ) -> Optional[tuple[Union[str, bytes], str, int]]:
        """ Handle requests for images, css, and js files """
        for bq in (".ico", ".jpg", ".png"):
            if bq in path:
                mimetype = "image/x-icon"
                content = _fetch_images(path)
                return content, mimetype, 200

        for bq in (".css", ".js"):
            if bq in path and bq == ".css":
                mimetype = "text/css"
                content = _fetch_files(path)
                return content, mimetype, 200
            if bq in path and bq == ".js":
                mimetype = "application/javascript"
                content = _fetch_files(path)
                return content, mimetype, 200
        return None

    def _deal_view_func(self,
            func: Callable,
            path: str,
            methods: list[str]) -> None:
        """ Handles paths defined in view functions """
        endpoint = func.__name__  # Here the endpoint is the name of the view function
        format_mark = re.findall("<string:.*?>", path)
        if format_mark and format_mark[0] in path:
            new_path = "/".join(path.split("/")[:-1])
            self.__url_func_map["path_have_var"][new_path] = (endpoint, func, methods)
        else:
            self.__url_func_map[path] = (endpoint, func, methods)

    def dispatch(self,
            path: str,
            method: str
        ) -> tuple[Union[str, bytes], str, int]:
        """ Processes the request
          and returns a response to the corresponding view function """
        # Process file-related requests
        deal_return = self._deal_static_request(path)
        if deal_return is not None:
            return deal_return

        # Handles requests related to view functions
        values = self.__url_func_map.get(path, None)
        variable = None
        if values is None:  # Determine whether path carries variables
            for_path, variable = path.split("/")[:-1], path.split("/")[-1]
            path = "/".join(for_path)
            values = self.__url_func_map["path_have_var"].get(path, None)
        if values is None:  # If it is still None, throw an error
            return FEASP_ERROR["HTTP_404"]

        # Enter the context----------------------------------
        endpoint, view_func, methods = values
        if variable:  # 如果有variable, 则传入视图函数
            view_func_return = view_func(variable)
        else:
            view_func_return = view_func()
        # Exit the context-----------------------------------

        if method not in methods:
            return FEASP_ERROR["HTTP_405"]

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
            return FEASP_ERROR["HTTP_500"]

    def route(self,
            path: str,
            methods: list[str]) -> Callable:
        """ Bind the path to the view function """
        if methods is None:
            methods = [METHOD["GET"]]

        def decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            self._deal_view_func(func, path, methods)   # Handle the path of the view function
            return wrapper
        return decorator

    def wsgi_apl(self,
            environ: dict,
            start_response: Callable) -> list[bytes]:
        """ WSGI prescribes the call Application,
          The parameters defined are environ, start_response
          environ: 包含全部请求信息的字典, start_response: 可调用对象 """
        self.request = self.request_class(environ)
        self.response = self.response_class("", mimetype="text/html")
        # *******************************************************************************
        content, mimetype, status = self.dispatch(self.request.path, self.request.method)
        # *******************************************************************************
        self.response.body = content
        self.response.mimetype, self.response.status = mimetype, status
        return self.response(environ, start_response)

    def run(self, host: str, port: int) -> None:
        """ Entry method, which calls the server based on the wsgiref implementation """
        simple_server = FeaspServer(host, port)
        simple_server.run(self.wsgi_apl)


def make_response(
        body: Union[str, bytes],
        mimetype: str="text/html",
        status: int=200) -> Response:
    """
      Provides a function that customizes the response with the following three parameters,
      body: response content, mimetype: response type, status: response status code
    """

    if isinstance(body, str) or isinstance(body, bytes):
        return Response(body, mimetype, status)
    return Response(*FEASP_ERROR["HTTP_500"])


def render_template(
        filename: str,
        **context: dict) -> str:
    """
      Render the HTML file under templates,
      So you need to put all the html files in the templates directory
      filename is a html filename and is relation path under the templates
      **context are context variable from user, it contains the key-value structure
      You should write it like here, filename: /index.html or index.html
      see example: example/app.py -> index and show_variable
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
      Provides a function that facilitates redirection
      Pass in a path that needs to be jumped, and this function generates a corresponding response
      see example: example/app.py -> redirect_
      :raise FeaspNotFound
    """

    url_func_map = _global_var["url_func_map"]
    if request_url in url_func_map:
        view_func = url_func_map[request_url][1]
        return view_func()
    raise FeaspNotFound("not found view function")


def url_for(endpoint: str) -> str:
    """
      Provide a function that makes it easier to build file paths
      It is only supported in view functions, passing in the view_func_name that needs to be url_for
      see example: example/app.py -> redirect_
      :raise FeaspNotFound
    """

    # Find the request path to the view function to url_for
    url_func_map = _global_var["url_func_map"]
    for path, values in url_func_map.items():
        if endpoint in values:
            return path
    raise FeaspNotFound("not found view function")


_global_var: dict[Any, Any] = {}  # Save some variables that need to be used globally
_http_local = threading.local()
