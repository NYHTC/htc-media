"""
Flask app for getting info about a file.

This microservice has a function that can run some arbitrary shell code,
and should ONLY run locally on a dev server. This is a VERY VERY bad idea,
but we need to do this because FileMaker/FM-plugins blow up the shell
after 5000-6000 calls.
"""

from flask import Flask, jsonify, request
import exifread
import subprocess


app = Flask(__name__)


@app.route("/ping")
def ping():
    """Ping app."""
    return "pong!"


@app.route("/info", methods=["POST"])
def info():
    """Get file info."""
    if request.method == "POST":
        req_data = request.get_json()
        if req_data:
            f_path = req_data["file_path"].replace("%20", " ")
            f_name = exec_shell(["basename", f_path])
            try:
                f_type = exec_shell(["file", "-b", f_path])
                f_size = exec_shell(["stat", "-f", "'%z'", f_path]).strip("'")
                checksum = exec_shell(["md5", "-q", f_path])
                mdls = exec_shell(["mdls", f_path])
                exif = get_exif_data(f_path)
            except OSError as e:
                # FileNotFoundError is a subclass of OSError
                print(e)
                return "invalid file path: {}".format(f_path)
            print(f_path)
            return jsonify(
                file_name=f_name,
                file_size=f_size,
                file_type=f_type,
                checksum=checksum,
                mdls=mdls,
                exif=exif,
            )
    return "nothing specified"


@app.route("/get-folder-list", methods=["POST"])
def get_folders():
    """Get a list of folders for the specified folder."""
    if request.method == "POST":
        req_data = request.get_json()
        if req_data:
            f_path = req_data["file_path"].replace("%20", " ")
            folder_list = exec_shell(
                ["find", f_path, "-type", "d", "-maxdepth", "1"]
            ).split("\n")
            folder_list = [i[len(f_path) :] for i in folder_list][1:]
            return jsonify(folder_list=folder_list)
    return "nothing specified"


@app.route("/get-file-list", methods=["POST"])
def get_files():
    """Get a list of files for the specified folder."""
    if request.method == "POST":
        req_data = request.get_json()
        if req_data:
            f_path = req_data["file_path"].replace("%20", " ")
            file_list = exec_shell(
                [
                    "find",
                    f_path,
                    "-type",
                    "f",
                    "-maxdepth",
                    "1",
                    "-exec",
                    "basename",
                    "{}",
                    ";",
                ]
            ).split("\n")
            return jsonify(file_list=file_list)
    return "nothing specified"


def exec_shell(cmd):
    """Run shell command and return the result - this is NOT secure."""
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
    )
    out, err = p.communicate()
    return out.decode("utf-8").rstrip()


def get_exif_data(file_path=None):
    """Get EXIF data for the specified file."""
    ignore_list = ["JPEGThumbnail"]
    f = open(file_path, "rb")
    tags = exifread.process_file(f)
    d = {}
    for k, v in tags.items():
        if k not in ignore_list and "MakerNote Tag 0x" not in k:
            d[k] = str(v)
    return d
