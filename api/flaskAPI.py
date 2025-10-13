import flask
import pandas as pd
app = flask.Flask(__name__)

@app.route('/api/health')
def health():
    return flask.jsonify({"status": "OK"})
