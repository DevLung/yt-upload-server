from flask import Flask, send_from_directory, send_file, json
from werkzeug.exceptions import NotFound
from os import path

from werkzeug.wrappers.response import Response



UPLOAD_PROGRESS_FILE = "./progress.json"
LOG_FILE = "./uploads.log"
app = Flask(__name__)



@app.errorhandler(NotFound)
def handle_file_not_found(ex: NotFound) -> Response:
    response: Response = ex.get_response()
    response.data = json.dumps({
        "title": ex.name,
        "status": ex.code,
        "detail": ex.description
    })
    response.content_type = "application/problem+json"
    return response


# serve Svelte app
@app.route("/")
def base() -> Response:
    return send_from_directory("client/public", "index.html")
@app.route("/<path:path>")
def home(path) -> Response:
    return send_from_directory("client/public", path)


@app.route("/progress")
def progress() -> Response:
    return send_from_directory(*path.split(UPLOAD_PROGRESS_FILE))


@app.route("/log")
def log() -> Response:
    return send_from_directory(*path.split(LOG_FILE), mimetype="text/plain")


if __name__ == "__main__":
    app.run(debug=True)