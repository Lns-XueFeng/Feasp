import os

from feasp import Feasp, render_template


app = Feasp(__name__)

base_dir = os.path.abspath(os.path.dirname(__name__))


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


if __name__ == "__main__":
    app.run("127.0.0.1", 8000)
