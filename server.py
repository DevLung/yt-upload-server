from flask import Flask, send_from_directory, stream_with_context, json
from werkzeug.exceptions import NotFound
from werkzeug.wrappers.response import Response
from typing import Generator
from waitress import serve
from os import path
from sys import argv, exit
from time import sleep
import scripts.uploader as uploader



PORT = 3001
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


@app.route("/upload-progress")
def upload_progress() -> Response:
    return send_from_directory(
        *path.split(uploader.PROGRESS_FILE),
        conditional=True
    )


@app.route("/upload-log")
def upload_log() -> Response:
    return send_from_directory(
        *path.split(uploader.LOG_FILE),
        mimetype="text/plain"
    )


@app.route("/upload-log/stream") # stream new log entries continuously
def upload_log_stream() -> Response:
    def generate_lines() -> Generator:
        with open(uploader.LOG_FILE, "r") as file:
            file.seek(0, 2) # jump to end of file
            while True:
                last_line: str = file.readline()
                if not last_line:
                    yield ": keep-alive\n\n" # necessary so connection doesn't die
                    sleep(2)
                    continue
                yield f"data: {last_line.rstrip()}\n\n"

    return Response(
        stream_with_context(generate_lines()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    ) # TODO add this to nginx config to prevent buffering: `location /upload-log/stream {proxy_buffering off;}`


if __name__ == "__main__":
    if len(argv) > 1 and argv[1] == "--debug":
        app.run(host="0.0.0.0", port=PORT, debug=True)
        exit()
    print(f"Waitress WSGI server listening on port {PORT}")
    serve(app, port=PORT)