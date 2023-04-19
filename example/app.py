from feasp import Feasp
from feasp import render_template, url_for, redirect, session


app = Feasp(__name__)


@app.route("/string", methods=["GET"])
def string():
    return "Hello World !"


@app.route("/dict", methods=["GET"])
def dict_():
    return {"H": "L", "P": "D"}


@app.route("/list", methods=["GET"])
def list_():
    return ["A", "P", "k", "G"]


@app.route("/image", methods=["GET"])
def image():
    return render_template("image.html")


@app.route("/redirect", methods=["GET"])
def redirect_():
    return redirect(url_for("index"))


@app.route("/set_cookies", methods="GET")
def set_cookies():
    # 通过session来让浏览器设置cookie
    session["name"] = "xue"
    session["ppp"] = "ppp"
    return "Set Cookies"


@app.route("/show_cookies", methods=["GET"])
def show_cookies():
    # 通过app.cookie来拿到浏览器传递的cookie
    if len(app.cookie) > 0:
        cookies = ""
        for k, v in app.cookie.items():
            cookies += f"{k}={v};"
        return f"Show Cookies: {cookies}"
    return "No Cookies"


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run("127.0.0.1", 8000)
