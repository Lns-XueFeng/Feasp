import unittest

from feasp.feasp import Feasp, Request, Response, FeaspTemplate


class TestBasic(unittest.TestCase):

    def test_route(self):
        app = Feasp(__name__)

        @app.route("/hello", methods=["GET"])
        def hello():
            pass

        @app.route("/say/<string:name>", methods=["GET"])
        def say(name):
            pass

        self.assertIn("/hello", app.url_func_map)
        self.assertIn("/say", app.url_func_map)

    def test_request(self):
        environ = {
            'SERVER_PORT': '8000',
            'REMOTE_HOST': '',
            'CONTENT_LENGTH': '',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/',
            'QUERY_STRING': '',
            'REMOTE_ADDR': '127.0.0.1',
            'CONTENT_TYPE': 'text/plain',
            'HTTP_HOST': '127.0.0.1:8000',
            'HTTP_CONNECTION': 'keep-alive',
            'HTTP_USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                               'Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.64',
            'HTTP_SEC_CH_UA_PLATFORM': 'Windows',
            'HTTP_REFERER': '',
            'wsgi.url_scheme': 'http'
        }
        request = Request(environ)
        self.assertEqual(request.environ, environ)
        self.assertEqual(request.url, "http://127.0.0.1:8000/")
        self.assertEqual(request.form, {})
        self.assertEqual(request.cookies, {})
        self.assertEqual(request.protocol, "HTTP/1.1")
        self.assertEqual(request.method, "GET")
        self.assertEqual(request.url_scheme, "http")
        self.assertEqual(request.referer, "")
        self.assertEqual(request.path, "/")
        self.assertEqual(request.url_args, "")
        self.assertEqual(request.connection, "keep-alive")
        self.assertEqual(request.platform, "Windows")
        self.assertEqual(request.user_agent, environ["HTTP_USER_AGENT"])

    def test_response(self):
        response = Response("<h1>Hello World</h1>", "text/html", 200)
        self.assertIn("Hello World", response.body)
        self.assertEqual(response.mimetype, "text/html")
        self.assertEqual(response.status, 200)
        response.set_cookie("name", "XueFeng")
        self.assertEqual(
            {"Content-Type": f"{response.mimetype}; charset=utf-8",
             "Set-Cookie": "name=XueFeng "},
            response.headers)

    def test_template(self):
        plain_html = """ 
            <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><link rel="icon" href="/favicon.ico">
            <link rel="stylesheet" href="/style.css"><title>Title</title></head><body><h1 id="title">Hello World</h1>
            </body><script src="/my_js.js"></script></html> """
        t = FeaspTemplate(plain_html, None)
        self.assertEqual(plain_html, t.render())

        var_html = """
            <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><link rel="icon" href="/favicon.ico">
            <link rel="stylesheet" href="/style.css"><title>Title</title></head><body>
            <h1 id="title">Hello {{name}}</h1></body><script src="/my_js.js"></script></html> """

        correct_html = """
            <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><link rel="icon" href="/favicon.ico">
            <link rel="stylesheet" href="/style.css"><title>Title</title></head>
            <body><h1 id="title">Hello XueFeng</h1></body><script src="/my_js.js"></script></html> """
        t = FeaspTemplate(var_html, {"name": "XueFeng"})
        self.assertEqual(var_html.replace("{{name}}", "XueFeng"), t.render())

        for_html = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
            <title>Title</title></head><body><ol><h1>Three: </h1>{% for name in name_list %}
            <h2>Hello {{ name }}</h2>{% endfor %}</ol></body></html> """

        correct_html = """
            <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
            <title>Title</title></head><body><ol><h1>Three: </h1><h2>Hello XueLian</h2>
            <h2>Hello XueXue</h2><h2>Hello XueFeng</h2></ol></body></html> """
        t = FeaspTemplate(for_html, {"name_list": ["XueLian", "XueXue", "XueFeng"]})
        self.assertEqual(correct_html, t.render())

        v_f_html = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
        <title>Title</title></head><body><ol><h1>{{name}}: </h1>{% for name in name_list %}
        <h2>Hello {{ name }}</h2>{% endfor %}</ol></body></html> """

        correct_html = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
        <title>Title</title></head><body><ol><h1>Three: </h1><h2>Hello XueLian</h2>
        <h2>Hello XueXue</h2><h2>Hello XueFeng</h2></ol></body></html> """
        t = FeaspTemplate(for_html, {"name": "Three", "name_list": ["XueLian", "XueXue", "XueFeng"]})
        self.assertEqual(correct_html, t.render())
