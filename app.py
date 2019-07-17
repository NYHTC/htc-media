"""
Flask app for getting info about a file.

This microservice has a function that can run some arbitrary shell code,
and should ONLY run locally on a dev server. This is a VERY VERY bad idea,
but we need to do this because FileMaker/FM-plugins blow up the shell
after 5000-6000 calls.
"""

import subprocess

from flask import Flask, jsonify, request
from PIL import Image
from dhash import dhash_row_col, format_hex
import exifread


app = Flask(__name__)


@app.route("/ping")
def ping():
    """Ping app."""
    return "pong!"


@app.route("/info", methods=["POST"])
def info():
    """Get file info."""
    if request.method != "POST":
        return default_response()
    f_path = file_path_from_request(request.get_json())
    if not f_path:
        return default_response()
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
    phash = get_phash(f_path)
    print(f_path)
    return jsonify(
        file_name=f_name,
        file_size=f_size,
        file_type=f_type,
        checksum=checksum,
        mdls=mdls,
        exif=exif,
        phash=phash,
    )


@app.route("/get-folder-list", methods=["POST"])
def get_folders():
    """Get a list of folders for the specified folder."""
    if request.method != "POST":
        return default_response()
    f_path = file_path_from_request(request.get_json())
    if not f_path:
        return default_response()
    folder_list = exec_shell(
        ["find", f_path, "-type", "d", "-maxdepth", "1"]
    ).split("\n")
    folder_list = [i[len(f_path) :] for i in folder_list][1:]
    return jsonify(folder_list=folder_list)


@app.route("/get-file-list", methods=["POST"])
def get_files():
    """Get a list of files for the specified folder."""
    if request.method != "POST":
        return default_response()
    f_path = file_path_from_request(request.get_json())
    if not f_path:
        return default_response()
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


@app.route("/get-file-list-with-type", methods=["POST"])
def get_file_list_with_types():
    """Get a list of files for the specified folder."""
    if request.method != "POST":
        return default_response()
    f_path = file_path_from_request(request.get_json())
    if not f_path:
        return default_response()
    file_list = exec_shell(
        [
            "find",
            f_path,
            "-type",
            "f",
            "-maxdepth",
            "1",
            "-exec",
            "file",
            "{}",
            ";",
        ]
    ).split("\n")
    return jsonify(file_list=file_list)


@app.route("/get-phash", methods=["POST"])
def get_phash_request():
    """Endpoint wrapper for getting phash for specified file path."""
    if request.method != "POST":
        return default_response()
    f_path = file_path_from_request(request.get_json())
    if not f_path:
        return default_response()
    phash = get_phash(f_path)
    return jsonify(phash=phash)


def default_response():
    """Default reply message for endpoints."""
    return "nothing specified"


def file_path_from_request(request_obj):
    """Extract the file path from the incoming request object."""
    if request_obj:
        # return request_obj["file_path"].replace("%20", " ")
        return request_obj["file_path"].replace("%20", " ").rstrip("/")
    return None


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
            try:
                d[k] = str(v)
            except TypeError:
                pass
    return d


def get_phash(file_path=None):
    """Get the perceptual hash of the specified file."""
    if not file_path:
        return None
    # print(file_path)
    try:
        img_1 = Image.open(file_path)
        row_1, col_1 = dhash_row_col(img_1)
        return format_hex(row_1, col_1)
    except (OSError, AttributeError) as e:
        print(e)
        return None
