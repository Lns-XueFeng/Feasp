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


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


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
    # 通过app.request.cookie来拿到浏览器传递的cookie
    if len(app.request.cookie) > 0:
        cookies = ""
        for k, v in app.request.cookie.items():
            cookies += f"{k}={v};"
        return f"Show Cookies: {cookies}"
    return "No Cookies"


@app.route("/login", methods=["GET", "POST"])
def login():
    if app.request.method == "POST":
        if app.request.form["username"] == "xuefeng" \
                and app.request.form["password"] == "123456789":
            session["username"] = "xuefeng"
            session["password"] = "123456789"
            # 至此可以考虑实现@login_required装饰器了
            return "Your login correctly !"
    return render_template("login.html")


if __name__ == "__main__":
    app.run("127.0.0.1", 8000, multithread=True)
