import flask
import pandas as pd
app = flask.Flask(__name__)

@app.route('/api/health')
def health():
    return flask.jsonify({"status": "OK"})

@app.route ('/api/observations')
def observations():
    return flask.jsonify(df.to_dict('records'))