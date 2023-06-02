## Feasp

一个简单的单线程的Web框架，基于WSGI标准，仅用于学习与交流。
<hr>

#### 1.返回渲染的网页
```python
from feasp import Feasp, render_template

app = Feasp(__name__)

@app.route("/index", methods=["GET"])
def index():
    return render_template("index.html")
```

#### 2.定义一个数据接口
```python
from feasp import Feasp

app = Feasp(__name__)

@app.route("/api", methods=["GET"])
def index():
    return {"data": "just return a dict"}
```
更多用法见example目录...
