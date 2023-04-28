## Feasp

A simple web framework, based on WSGI standards，only to learning and talking


### Use examples: 
```python
from feasp import Feasp

app = Feasp(__name__)

@app.route("/", methods=["GET"])
def index():
    return "Hello Feasp !"

if __name__ == "__main__":
    app.run("127.0.0.1", 8000)
```

See the 'example' directory for more
