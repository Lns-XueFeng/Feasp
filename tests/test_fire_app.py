import unittest
import requests

# Base of 'example' to test
# So, you should fire the app in example firstly
# Warning: Before you fire this test file, please fire app.py


class TestActualApp(unittest.TestCase):

    def test_index(self):
        res = requests.get("http://127.0.0.1:8000")
        self.assertIn("Hello World", res.text)

    def test_string(self):
        res = requests.get("http://127.0.0.1:8000/string")
        self.assertIn("Hello String", res.text)

    def test_dict_(self):
        res = requests.get("http://127.0.0.1:8000/dict")
        self.assertEqual({"H": "L", "P": "D"}, res.json())

    def test_image(self):
        res = requests.get("http://127.0.0.1:8000/image")
        self.assertEqual(200, res.status_code)

    def test_file(self):
        res = requests.get("http://127.0.0.1:8000/favicon.ico")
        self.assertEqual(200, res.status_code)
        res = requests.get("http://127.0.0.1:8000/static/head.jpg")
        self.assertEqual(200, res.status_code)
        res = requests.get("http://127.0.0.1:8000/static/my_js.js")
        self.assertEqual(200, res.status_code)
        res = requests.get("http://127.0.0.1:8000/static/style.css")
        self.assertEqual(200, res.status_code)

    def test_redirect_(self):
        res = requests.get("http://127.0.0.1:8000/redirect")
        self.assertIn("Hello World", res.text)

    def test_cookies(self):
        session = requests.session()
        res = session.get("http://127.0.0.1:8000/show_cookies")
        self.assertIn("No Cookies", res.text)
        res = session.get("http://127.0.0.1:8000/set_cookies")
        self.assertIn("Set Cookies", res.text)
        res = session.get("http://127.0.0.1:8000/show_cookies")
        self.assertIn("Name=XueFeng;Hobby=WriteCode", res.text)

    def test_login(self):
        res = requests.get("http://127.0.0.1:8000/login")
        self.assertEqual(200, res.status_code)
        form = {"username": "", "password": ""}
        res = requests.post("http://127.0.0.1:8000/login", data=form)
        self.assertIn("Please Input user and password !", res.text)
        form = {"username": "Lns-XueFeng", "password": "123456789"}
        res = requests.post("http://127.0.0.1:8000/login", data=form)
        self.assertIn("Your login message correctly !", res.text)
        form = {"username": "Lns-XueFeng", "password": "111111111"}
        res = requests.post("http://127.0.0.1:8000/login", data=form)
        self.assertIn("Your login message incorrectly !", res.text)

    def test_variable(self):
        res = requests.get("http://127.0.0.1:8000/variable/XueFeng")
        self.assertIn("Hello XueFeng, I love you", res.text)

    def test_for_list(self):
        res = requests.get("http://127.0.0.1:8000/for_list")
        self.assertIn("Hello XueLian", res.text)
        self.assertIn("Hello XueXue", res.text)
        self.assertIn("Hello XueFeng", res.text)

    def test_make_resp(self):
        res = requests.get("http://127.0.0.1:8000/make_resp")
        self.assertIn("Hello MakeResponse", res.text)

    def test_see_my_func(self):
        res = requests.get("http://127.0.0.1:8000/see_my_func")
        self.assertIn("see_funcs", res.text)

    def test_if_control(self):
        res = requests.get("http://127.0.0.1:8000/if_control")
        self.assertIn("Hello Lns-XueFeng", res.text)

    def test_if_and_for(self):
        res = requests.get("http://127.0.0.1:8000/if_and_for")
        self.assertIn("Hello XueFeng", res.text)
