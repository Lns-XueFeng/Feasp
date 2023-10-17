from feasp import Feasp
from feasp import render_template, url_for, redirect, make_response, connect, request, session


"""
用于验证 Feasp 实现的功能，
一般来说，要实现一个函数，这里写一个视图函数来验证函数，
或者先写一个视图函数，然后在框架中实现支持
"""


# 提供Feasp类来构建应用程序实例，
# 然后你可以使用这个程序实例来做一些事情，
# 例如在进入上下文时可使用session, request.method/cookies,...
# app.response提供了: status, mimetype, headers, set_cookie()
# request 提供了: url, method, cookies, ...
app = Feasp(__name__)


@app.route("/string", methods=["GET"])
def string():
    # 你可以返回一个字符串来验证应用是否可以成功运行
    return "Hello String"


@app.route("/dict", methods=["GET"])
def dict_():
    # 支持向客户端返回字典类型，
    # feasp会将字典转换为JSON类型并满足HTTP协议
    return {"H": "L", "P": "D"}


@app.route("/", methods=["GET"])
def index():
    # 为你提供了工具函数，使用它可用渲染一个在templates目录中的HTML文件
    return render_template("index.html")


@app.route("/image", methods=["GET"])
def image():
    # feasp会自动处理你定义在HTML文件中的图片元素，
    # 它还内置了css、js文件的自动处理，方便了你的开发，
    # 因此你只需要在HTML文件中正确的定义静态资源的路径即可
    return render_template("image.html")


@app.route("/redirect", methods=["GET"])
def redirect_():
    # 为你提供了工具函数，使用它可用去重定向到一个网页页面
    return redirect(url_for("index"))


@app.route("/set_cookies", methods="GET")
def set_cookies():
    # 使用session来设置浏览器的cookie
    session["Name"] = "XueFeng"
    # session会忽略空格，因此会被设置为WriteCode字符串
    session["Hobby"] = "Write Code"
    return "Set Cookies"


@app.route("/show_cookies", methods=["GET"])
def show_cookies():
    # 使用request.cookie获取浏览器传递来的cookie
    if len(request.cookies) > 0:
        cookies = ""
        for k, v in request.cookies.items():
            cookies += f"{k}={v};"
        return f"Show Cookies: {cookies}"
    return "No Cookies"


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        form = request.form
        if len(form) == 0:
            return "Please Input user and password !"

        username = form["username"]
        password = form["password"]
        if username == "Lns-XueFeng" and password == "123456789":
            # 使用session让浏览器设置并存储cookie
            # 如果你需要读取cookie，你可以这样做：request.cookie
            session["username"] = username
            session["password"] = password
            # 此时，可以考虑实现@login_required装饰器
            return "Your login message correctly !"
        else:
            return "Your login message incorrectly !"

    return render_template("login.html")


@app.route("/variable/<string:name>", methods=["GET"])
def show_variable(name):
    # 您可以在路由路径中定义变量，但变量必须与模板中的定义匹配
    # 并像这样输入：key=value，传入你想要渲染的变量和值
    return render_template("variable.html", name=name, love="you")


@app.route("/for_list", methods=["GET"])
def for_list():
    # 可以传入列表或可迭代对象，去完成重复性工作
    name_list = ["XueLian", "XueXue", "XueFeng"]
    return render_template("For_list.html", name_list=name_list)


@app.route("/make_resp", methods=["GET"])
def make_resp():
    # 为你提供了工具函数，并可使用它返回一个可自定义的响应
    return make_response(
        "<h1>Hello MakeResponse</h1>", status=202, mimetype="text/html")


@app.route("/see_my_func", methods=["GET"])
def see_funcs():
    # 可以查看app.py定义的所有的相对路径与函数的映射 <url: func>
    return app.url_func_map


@app.route("/if_control", methods=["GET"])
def if_control():
    name = "Lns-XueFeng"
    return render_template("If_control.html", name=name)


@app.route("/if_and_for", methods=["GET"])
def if_and_for():
    name_list = ["XueLian", "XueXue", "XueFeng"]
    return render_template("If_For.html", name_list=name_list)


@app.route("/save_to_db", methods=["GET", "POST"])
def save_to_db():
    with connect("feasp.db") as handler:
        first_user_tuple = handler.fetch_all("UserLogin")[0]

    if request.method == "POST":
        form = request.form
        if len(form) == 0:
            return "Please Input user and password !"

        username = form["username"]
        password = form["password"]
        if username == first_user_tuple[0] and password == str(first_user_tuple[1]):
            session["username"] = username
            session["password"] = password
            return "Your login message correctly !"
        else:
            return "Your login message incorrectly !"

    return render_template("save_to_db.html")


if __name__ == "__main__":
    app.run("127.0.0.1", 8000)
