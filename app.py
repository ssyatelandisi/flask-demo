from flask import (
    Flask,
    request,
    make_response,
    render_template,
    send_file,
    redirect,
    send_from_directory,
)
from flask_compress import Compress  # type: ignore
from werkzeug.routing import BaseConverter
import os
import logging
import json
import sys

logging.basicConfig(level=logging.INFO)

try:
    TEMP_FOLDER = os.path.join(sys._MEIPASS, "templates")  # type: ignore
except Exception:
    TEMP_FOLDER = "templates"

app = Flask(
    __name__,
    template_folder=TEMP_FOLDER,
    static_folder=TEMP_FOLDER,
    static_url_path="/",
)
Compress(app)


class Logger:
    DEBUG = 37
    INFO = 36
    WARNING = 33
    ERROR = 31
    CRITICAL = 41
    PREFIX = "\033["
    SUFFIX = "\033[0m"

    @staticmethod
    def debug(msg):
        logging.debug(
            "{0}{1}m{2}{3}".format(
                __class__.PREFIX, __class__.DEBUG, msg, __class__.SUFFIX
            )
        )

    @staticmethod
    def info(msg):
        logging.info(
            "{0}{1}m{2}{3}".format(
                __class__.PREFIX, __class__.INFO, msg, __class__.SUFFIX
            )
        )

    @staticmethod
    def warning(msg):
        logging.warning(
            "{0}{1}m{2}{3}".format(
                __class__.PREFIX, __class__.WARNING, msg, __class__.SUFFIX
            )
        )

    @staticmethod
    def error(msg):
        logging.error(
            "{0}{1}m{2}{3}".format(
                __class__.PREFIX, __class__.ERROR, msg, __class__.SUFFIX
            )
        )

    @staticmethod
    def critical(msg):
        logging.critical(
            "{0}{1}m{2}{3}".format(
                __class__.PREFIX, __class__.CRITICAL, msg, __class__.SUFFIX
            )
        )


# 自定义正则路由规则
class ResourceConverter(BaseConverter):
    def __init__(self, url_map, *args):
        super(ResourceConverter, self).__init__(url_map)
        self.regex = args[0]


# 添加到自定义的路由规则
app.url_map.converters["re"] = ResourceConverter


# favicon.ico图标
@app.route("/favicon.ico")
def favicon():
    response = make_response(
        send_from_directory(
            "templates",
            "favicon.ico",
            mimetype="image/vnd.microsoft.icon",
        )
    )
    response.headers["Cache-Control"] = "public"
    return response


@app.before_request
def before():
    if request.method == "OPTIONS":
        return make_response()


@app.after_request
def after_request(res):
    res.headers["Access-Control-Allow-Origin"] = "*"
    res.headers["Access-Control-Allow-Methods"] = "*"
    res.headers["Access-Control-Allow-Headers"] = "*"
    return res


@app.route("/")
def index():
    return render_template("index.html")


def filename_check(filename: str):
    return (
        filename.replace("\\", "")
        .replace("/", "")
        .replace("*", "")
        .replace("?", "")
        .replace(":", "")
        .replace('"', "")
        .replace("<", "")
        .replace(">", "")
        .replace("|", "")
    )


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "GET":
        return redirect("/api")
    else:
        res = make_response()
        try:
            uploadedFile = request.files.get("file")
            if uploadedFile.filename == "":
                pass
            else:
                if os.path.exists("upload"):
                    pass
                else:
                    os.makedirs("upload")
                uploadedFile.save(f"upload/{filename_check(uploadedFile.filename)}")
                res.status = 200
                res.data = "success"
                Logger.info("{0}上传成功".format(uploadedFile.filename))
        except Exception:
            res.status = 200
            res.data = "fail"
        return res


@app.route("/api", methods=["GET", "POST", "OPTIONS"])
def api():
    res = make_response()
    res.headers["Content-Type"] = "application/json; charset=utf-8"
    res.data = json.dumps(dict(request.headers), ensure_ascii=False)
    return res


@app.route("/ca")
def ca():
    return send_file(
        os.path.join(os.path.dirname(sys.argv[0]), "rootCA.crt"),
        download_name="WareyumeCA.crt",
    )


# 请求本地资源
@app.route("/<re('.*\.mp4|.*\.flv|.*\.m3u8'):resource>")
def local_resource(resource):
    response = make_response(
        send_from_directory(os.path.dirname(sys.argv[0]), resource, as_attachment=True)
    )
    response.headers["Access-Control-Allow-Credentials"] = "false"
    response.headers["Accept-Ranges"] = "bytes"
    return response


@app.errorhandler(404)
def page_no_found(e):
    return redirect("/#/error", 302)


if __name__ == "__main__":
    if "ssl" in sys.argv or "https" in sys.argv:
        app.run(
            host="0.0.0.0",
            port=443,
            ssl_context=("server.pem", "server.key"),
            debug=False,
        )
    else:
        app.run(host="0.0.0.0", port=80, debug=False)
