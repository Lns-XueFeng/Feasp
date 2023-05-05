## Feasp

A simple web framework, based on WSGI standards，only to learning and talking


### Use examples: 
#### an easy app to run
```python
from feasp import Feasp

app = Feasp(__name__)

@app.route("/", methods=["GET"])
def index():
    return "Hello Feasp !"

if __name__ == "__main__":
    app.run("127.0.0.1", 8000)
```
#### make a data interface
```python
from feasp import Feasp

app = Feasp(__name__)

@app.route("/api", methods=["GET"])
def index():
    return {"data": "just return a dict"}
```
#### return a render html file
```python
from feasp import Feasp, render_template

app = Feasp(__name__)

@app.route("/index", methods=["GET"])
def index():
    return render_template("index.html")
```

See the 'example' directory for more usage
