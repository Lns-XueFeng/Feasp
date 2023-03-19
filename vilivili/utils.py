import os

from .config import BASE_DIR


def render_template(template):
    """读取 HTML 内容"""
    template_dir = os.path.join(BASE_DIR, "templates")
    path = os.path.join(template_dir, template)
    with open(path, 'r', encoding="utf-8") as f:
        html = f.read()
    return html
