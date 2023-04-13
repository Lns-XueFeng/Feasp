## Feasp

feasp：一个简易的Web框架，基于Werkzeug，仅供学习交流


### 使用如下
```python
from feasp import Feasp

app = Feasp(__name__)

@app.route("/", methods=["GET"])
def index():
    return "Hello World !"

if __name__ == "__main__":
    app.run("127.0.0.1", 8000)
```

