import os

from flask import Flask, jsonify, request, Response, render_template
import yaml

from muds import storage
from muds import tree

app = Flask(__name__)

root = None
store = None


def _get_root():
    global root
    if root is None:
        opts_file = os.path.join(os.path.dirname(__file__), 'opts.yml')
        data = yaml.load(open(opts_file))
        root = tree.RootNode(data)
    return root


def _get_store():
    global store
    if store is None:
        store = storage.Store()
    return store


@app.route('/')
def index():
    root = _get_root()
    return render_template('form.html', form=root.get_tree_form())


@app.route('/api/v1/keys', methods=['GET'])
def keys():
    root = _get_root()
    return jsonify(root.get_keys())


@app.route('/api/v1/configs', methods=['POST'])
def post_config():
    data = {k: v for k, v in request.values.items()}
    root = _get_root()
    return Response(root.get_local_conf(data), mimetype='text/plain')


@app.route('/api/v1/configs/<uuid>', methods=['GET'])
def get_config(uuid):
    store = _get_store()
    return Response(store.load(uuid), mimetype='text/plain')


@app.route('/go', methods=['POST'])
def go():
    data = {k: v for k, v in request.values.items()}
    root = _get_root()
    store = _get_store()
    local_conf = root.get_local_conf(data)
    uuid = store.save(local_conf)
    return render_template('output.html', local_conf=local_conf, uuid=uuid)


if __name__ == "__main__":
    app.run()
