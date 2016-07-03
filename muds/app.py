import os

from flask import Flask, request, Response, render_template
import yaml

from muds import tree

app = Flask(__name__)

root = None


def _get_root():
    global root
    if root is None:
        opts_file = os.path.join(os.path.dirname(__file__), 'opts.yml')
        data = yaml.load(open(opts_file))
        root = tree.RootNode(data)
    return root


@app.route('/')
def index():
    root = _get_root()
    return render_template('form.html', form=root.get_tree_form())


@app.route('/go', methods=['POST'])
def go():
    root = _get_root()

    form_data = {k: v for k, v in request.values.items()}
    root.set_children_values(form_data)
    lines = root.get_local_conf_lines()
    local_conf = '[[local|localrc]]\n'
    for line in lines:
        local_conf += line + '\n'

    return Response(local_conf, mimetype='text/plain')


if __name__ == "__main__":
    app.run()
