import unittest
import requests

# Base of 'example' to test
# So, you should fire the app in example firstly
# Warning: Before you fire this test file, please fire app.py


class TestActualApp(unittest.TestCase):

    def test_index(self):
        req = requests.get("http://127.0.0.1:8000")
        self.assertIn("Hello World", req.text)

    def test_string(self):
        req = requests.get("http://127.0.0.1:8000/string")
        self.assertIn("Hello String", req.text)

    def test_dict_(self):
        req = requests.get("http://127.0.0.1:8000/dict")
        self.assertEqual({"H": "L", "P": "D"}, req.json())

    def test_image(self):
        req = requests.get("http://127.0.0.1:8000/image")
        self.assertEqual(200, req.status_code)

    def test_file(self):
        req = requests.get("http://127.0.0.1:8000/head.jpg")
        self.assertEqual(200, req.status_code)
        req = requests.get("http://127.0.0.1:8000/my_js.js")
        self.assertEqual(200, req.status_code)
        req = requests.get("http://127.0.0.1:8000/style.css")
        self.assertEqual(200, req.status_code)

    def test_redirect_(self):
        req = requests.get("http://127.0.0.1:8000/redirect")
        self.assertIn("Hello World", req.text)

    def test_cookies(self):
        session = requests.session()
        req = session.get("http://127.0.0.1:8000/show_cookies")
        self.assertIn("No Cookies", req.text)
        req = session.get("http://127.0.0.1:8000/set_cookies")
        self.assertIn("Set Cookies", req.text)
        req = session.get("http://127.0.0.1:8000/show_cookies")
        self.assertIn("Name=XueFeng;Hobby=WriteCode", req.text)

    def test_login(self):
        req = requests.get("http://127.0.0.1:8000/login")
        self.assertEqual(200, req.status_code)
        form = {"username": "XueFeng", "password": "123456789"}
        req = requests.post("http://127.0.0.1:8000/login", data=form)
        self.assertIn("Your login correctly !", req.text)

    def test_variable(self):
        req = requests.get("http://127.0.0.1:8000/variable/XueFeng")
        self.assertIn("Hello XueFeng, I love you", req.text)

    def test_for_list(self):
        req = requests.get("http://127.0.0.1:8000/for_list")
        self.assertIn("Hello XueLian", req.text)
        self.assertIn("Hello XueXue", req.text)
        self.assertIn("Hello XueFeng", req.text)

    def test_make_resp(self):
        req = requests.get("http://127.0.0.1:8000/make_resp")
        self.assertIn("Hello MakeResponse", req.text)
