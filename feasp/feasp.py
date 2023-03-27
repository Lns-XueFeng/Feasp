import os

from werkzeug.wrappers import Request, Response


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


def render_template(filename, base_dir):
    filepath = os.path.join(base_dir, "template", filename)
    with open(filepath, 'r') as fp:
        content = fp.read()
    return content


class Application:

    def __init__(self, filename):
        self.url_func_map = {}
        self.base_dir = os.path.abspath(os.path.dirname(filename))

    def dispatch(self, path, method):
        values = self.url_func_map.get(path, None)
        if values is None:
            return http_404

        view_func, methods = values
        view_func_return = view_func()
        if method not in methods:
            return http_405

        mimetype = "text/html"
        if isinstance(view_func_return, str):
            pass
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
            return http_500

        return Response(view_func_return, mimetype=mimetype)

    def route(self, path, methods):
        if methods is None:
            methods = [Method.GET]

        def decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            self.url_func_map[path] = (func, methods)
            return wrapper
        return decorator

    def wsgi_apl(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch(request.path, request.method)
        return response(environ, start_response)

    def run(self):
        from werkzeug.serving import run_simple
        run_simple("127.0.0.1", 8000, self.wsgi_apl)
