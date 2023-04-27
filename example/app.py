from feasp import Feasp
from feasp import render_template, url_for, redirect, make_response


"""
Used to verify the functionality implemented by Feasp,
Generally, to implement a function, here a view function is written to verify the function,
Or write a view function first, and then implement support in the framework
"""


app = Feasp(__name__)


@app.route("/string", methods=["GET"])
def string():
    return "Hello World !"


@app.route("/dict", methods=["GET"])
def dict_():
    return {"H": "L", "P": "D"}


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
    # Use app.response.set_cookies () to let the browser set cookies
    app.response.set_cookie("Name", "XueFeng")
    app.response.set_cookie("Hobby", "Write Code")
    return "Set Cookies"


@app.route("/show_cookies", methods=["GET"])
def show_cookies():
    # Use the app.request.cookie to get the cookie passed by the browser
    if len(app.request.cookies) > 0:
        cookies = ""
        for k, v in app.request.cookies.items():
            cookies += f"{k}={v};"
        return f"Show Cookies: {cookies}"
    return "No Cookies"


@app.route("/login", methods=["GET", "POST"])
def login():
    if app.request.method == "POST":
        form = app.request.form
        username = form["username"]
        password = form["password"]
        if username == "xuefeng" and password == "123456789":
            # Use app.response.set_cookies () to let the browser set the cookie and store it
            # If you need to read cookies, you can do this: app.request.cookie
            app.response.set_cookie("username", username)
            app.response.set_cookie("password", password)
            # At this point, you can consider implementing @login_required decorators
            return "Your login correctly !"
    return render_template("login.html")


@app.route("/variable/<string:name>", methods=["GET"])
def show_variable(name):
    """ The variables must match what define in the template,
      and input like this: key=value, pass in the variables and values you want to render """
    return render_template("variable.html", name=name, love="you")


@app.route("/for_list", methods=["GET"])
def for_list():
    name_list = ["XueLian", "XueXue", "XueFeng"]
    return render_template("for_list.html", name_list=name_list)


@app.route("/make_resp", methods=["GET"])
def make_resp():
    return make_response(
        "<h1>Hello MakeResponse</h1>", mimetype="text/html", status=202)


if __name__ == "__main__":
    app.run("127.0.0.1", 8000)
