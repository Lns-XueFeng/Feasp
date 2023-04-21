from feasp import Feasp
from feasp import render_template, url_for, redirect, session

"""
用来验证Feasp实现的功能
一般是实现一个功能, 这里就编写一个视图函数来进行验证功能
或者是先编写一个视图函数, 然后去框架中实现支持
"""

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
    session["name"] = "xuefeng"
    session["hobby"] = "code"
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
            # session只能设置: 让浏览器设置cookie并存储
            # 如果需要读取cookie, 可以这样: app.request.cookie
            session["username"] = "xuefeng"
            session["password"] = "123456789"
            # 至此可以考虑实现@login_required装饰器了
            return "Your login correctly !"
    return render_template("login.html")


@app.route("/variable/<variable:value>", methods=["GET"])
def show_variable(name):
    """ 传入的变量必须与在模板中的一致
      且只能以key=value形式传入所需渲染的变量与值"""
    return render_template("variable.html", name=name, love="you")


if __name__ == "__main__":
    app.run("127.0.0.1", 8000, multithread=True)
