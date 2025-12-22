from sys import argv, exit, stderr
from os import path
from subprocess import Popen

if len(argv) < 2:
    print("Please supply at least one video path as an argument.", file=stderr)
    exit(1)

for arg in argv[1:]:
    if not path.exists(arg):
        print(f"File path '{arg}' invalid. Skipping file...", file=stderr)
        continue
    Popen(
        f"bash -c 'source {path.realpath(path.join(path.dirname(__file__), '../.venv/bin/activate'))} && " +
        f"python3 {path.realpath(path.join(path.dirname(__file__), './uploader.py'))} --file {arg} --noauth_local_webserver'",
        shell=True,
        start_new_session=True
    )