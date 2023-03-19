from .utils import render_template


def index():
    return render_template("index.html")


# routes查询相应的函数
routes = {
    '/': (index, ['GET', ]),
    '/index': (index, ['GET', ]),
}
