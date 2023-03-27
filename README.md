## Feasp

feasp：一个简易的Web框架，仅供学习交流


### 使用如下
```python
from feasp import Application

app = Application(__name__)

@app.route("/", methods=["GET"])
def index():
    return "Hello World !"

if __name__ == "__main__":
    app.run()
```
