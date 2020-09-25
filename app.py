import threading, sys
from base64 import b64decode, b64encode
from flask import (
    Flask,
    make_response,
    send_from_directory,
    request,
    redirect,
    render_template,
)
from werkzeug.utils import secure_filename
from requests import get
from urllib.parse import urljoin, urlparse
from os import getenv, path, makedirs
from re import search
from colorama import init, Fore, Back, Style

init(autoreset=True)

CONSOLE_RESOURCE = None
HOME_FILE_NAME = None


def console_input():
    global CONSOLE_RESOURCE
    global HOME_FILE_NAME
    while True:
        print(Fore.MAGENTA + Style.BRIGHT + "控制台输入视频源>")
        CONSOLE_RESOURCE = input().strip()
        CONSOLE_RESOURCE = CONSOLE_RESOURCE if CONSOLE_RESOURCE else None
        print(
            Back.YELLOW
            + Style.BRIGHT
            + "{:^7}".format("INFO")
            + Back.RESET
            + Style.BRIGHT
            + " 输入完成"
        )
        consolePlay = Player(CONSOLE_RESOURCE)
        consolePlay.run()
        HOME_FILE_NAME = consolePlay.fileName


class Player:
    def __init__(self, inputResource):
        self.url = inputResource
        self.uri = urljoin(self.url, "./")
        self.parseResult = urlparse(inputResource)
        _, self.extension = path.splitext(self.parseResult.path)
        self.fileName = path.split(self.parseResult.path)[-1]
        print(
            Fore.WHITE
            + Back.YELLOW
            + Style.BRIGHT
            + "{:^7}".format("INFO")
            + Style.RESET_ALL
            + " 播放源 "
            + Back.MAGENTA
            + Style.BRIGHT
            + self.fileName
            + Style.RESET_ALL
        )

    def download_m3u8(self):
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36",
            "origin": self.parseResult.scheme + "://" + self.parseResult.netloc,
            "referer": self.uri,
            "host": self.parseResult.netloc,
        }
        response = get(url=self.url, headers=headers, stream=True)
        with open(path.join(getenv("TEMP"), self.fileName), "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
        with open(
            path.join(getenv("TEMP"), self.fileName), "r", encoding="utf-8"
        ) as fr:
            with open(self.fileName, "w", encoding="utf-8", newline="") as fw:
                for line in fr:
                    if (
                        search(r"^[^#]", line)
                        and search(".ts", line)
                        and "" == urlparse(line).scheme
                    ):
                        fw.write(urljoin(self.uri, line))
                    else:
                        fw.write(line)

    def run(self):
        if "" == self.parseResult.scheme:
            self.video_src = f"/{self.fileName}"
        else:
            if ".m3u8" == self.extension.lower():
                self.download_m3u8()
                self.video_src = f"/{self.fileName}"
            else:
                self.video_src = self.url


import sys

TEMP_FOLDER = path.join(sys._MEIPASS, "templates")
app = Flask(__name__, template_folder=TEMP_FOLDER)
# app = Flask(__name__)


@app.route("/")
def home():
    if CONSOLE_RESOURCE:
        template_dict = {
            "playPage": "/play/?url={}".format(
                b64encode(CONSOLE_RESOURCE.encode()).decode()
            ),
            "file_name": f"播放 {HOME_FILE_NAME}",
        }
    else:
        template_dict = {
            "playPage": "",
            "file_name": "",
        }
    return render_template("home.html", **template_dict)


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        TEMP_FOLDER, "favicon.ico", mimetype="image/vnd.microsoft.icon",
    )


# 播放页面
@app.route("/play/")
def play():
    if request.args.get("url"):
        player = Player(
            b64decode(request.args.get("url").replace(" ", "+").encode()).decode()
        )
        player.run()
        template_dict = {"file_name": player.fileName, "video_src": player.video_src}
        return render_template("play.html", **template_dict)
    else:
        return redirect("/")


# js
@app.route("/<string:jsName>.js")
def js(jsName):
    response = make_response(
        send_from_directory(TEMP_FOLDER, jsName + ".js", as_attachment=True)
    )
    response.headers["Content-Type"] = "application/javascript"
    return response


# 请求本地资源
@app.route("/<string:resource>")
def local(resource):
    response = make_response(
        send_from_directory(app.root_path, resource, as_attachment=True)
    )
    response.headers["Access-Control-Allow-Credentials"] = "false"
    response.headers[
        "Access-Control-Allow-Headers"
    ] = "Date,Server,x-oss-request-id,x-oss-cdn-auth,Last-Modified,x-oss-object-type,x-oss-hash-crc64ecma,x-oss-storage-class,x-oss-server-time,Ali-Swift-Global-Savetime,X-Cache,X-Swift-SaveTime,X-Swift-CacheTime,Access-Control-Allow-Origin,Access-Control-Expose-Headers,cloud_type,Timing-Allow-Origin,EagleId,x-hcs-proxy-type,nginx-hit,Age,Content-Type,Content-Length,ETag,Content-MD5,Accept-Ranges"
    response.headers["Access-Control-Allow-Methods"] = "GET"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers[
        "Access-Control-Expose-Headers"
    ] = "Date, Server, x-oss-request-id, x-oss-cdn-auth, Last-Modified, x-oss-object-type, x-oss-hash-crc64ecma, x-oss-storage-class, x-oss-server-time, Ali-Swift-Global-Savetime, X-Cache, X-Swift-SaveTime, X-Swift-CacheTime, Access-Control-Allow-Origin, Access-Control-Expose-Headers, cloud_type, Timing-Allow-Origin, EagleId, x-hcs-proxy-type, nginx-hit, Age, Content-Type, Content-Length, ETag, Content-MD5, Accept-Ranges"
    response.headers["Accept-Ranges"] = "bytes"
    return response


# 文件上传
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if not path.exists("upload_files"):
            makedirs("upload_files")
        for file in request.files.getlist("files"):
            filename = secure_filename(file.filename)
            file.save(path.join("upload_files", filename))
            print(
                Back.YELLOW
                + Style.BRIGHT
                + "{:^7}".format("INFO")
                + Back.RESET
                + " 文件 "
                + Fore.CYAN
                + f"{filename}"
                + Fore.RESET
                + " 上传成功"
            )
        return """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>上传成功</title></head><body><script>alert('上传成功，即将返回上传页面'); location.href='/upload'; </script></body></html>"""
    else:
        return render_template("upload.html")


@app.errorhandler(404)
def page_no_found(e):
    return redirect("/")


@app.errorhandler(500)
def handle_500(e):
    return redirect("/")


import socket


class LAN_IP:
    ip = "127.0.0.1"
    length = len(ip)

    def __init__(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("10.0.0.1", 80))
            self.ip = s.getsockname()[0]
            self.length = len(self.ip)
        finally:
            s.close()


if __name__ == "__main__":
    LOCAL_IP = LAN_IP()
    print(
        Style.BRIGHT
        + " * 本地浏览　 "
        + Back.GREEN
        + Style.BRIGHT
        + "http://127.0.0.1".ljust(LOCAL_IP.length + 7)
        + Style.RESET_ALL
        + Style.BRIGHT
        + " 访问"
        + Style.RESET_ALL
    )
    print(
        Style.BRIGHT
        + " * 局域网浏览 "
        + Back.GREEN
        + Style.BRIGHT
        + f"http://{LOCAL_IP.ip}".ljust(LOCAL_IP.length + 7)
        + Style.RESET_ALL
        + Style.BRIGHT
        + " 访问"
    )
    print(" * " + Back.RED + Style.BRIGHT + "按 CTRL + C 退出" + Style.RESET_ALL)
    threading.Thread(target=console_input).start()
    app.run(host="0.0.0.0", port=80)

