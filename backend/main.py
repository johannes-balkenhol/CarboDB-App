"""Main module for handling web server operations.

This module sets up a Flask application to handle various web requests, including file uploads and data processing.
CORS is enabled for all origins to allow cross-origin requests.

"""

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)


def create_app():
    """
        necessary for tests.
    """
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    CORS(app, resources={r"/*": {"origins": "*"}})
    return app


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/validate-fasta", methods=['POST'])
def validate_fasta():
    is_valid = True
    return jsonify(is_valid)


@app.route("/hmmer-search", methods=['POST'])
def hmmer_search():
    return jsonify(hmmer_search())


if __name__ == '__main__':
    create_app()
    app.run(debug=True)
