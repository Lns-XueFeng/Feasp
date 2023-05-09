## Feasp

A simple web framework, based on WSGI standards，only to learning and talking


### Use examples: 

#### return a render html file
```python
from feasp import Feasp, render_template

app = Feasp(__name__)

@app.route("/index", methods=["GET"])
def index():
    return render_template("index.html")
```

#### make a data interface
```python
from feasp import Feasp

app = Feasp(__name__)

@app.route("/api", methods=["GET"])
def index():
    return {"data": "just return a dict"}
```

See the 'example' directory for more usage
