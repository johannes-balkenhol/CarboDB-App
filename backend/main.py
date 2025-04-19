"""Main module for handling web server operations.

This module sets up a Flask application to handle various web requests, including file uploads and data processing.
CORS is enabled for all origins to allow cross-origin requests.

"""

from backend.app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
