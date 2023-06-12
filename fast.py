from fastapi import FastAPI, Request, Path, Response, Header, UploadFile
from fastapi.responses import (
    HTMLResponse,
    FileResponse,
    StreamingResponse,
    RedirectResponse,
)
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn
import os
import subprocess

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)  # 允许跨越
app.add_middleware(HTTPSRedirectMiddleware)  # http重定向到https
app.add_middleware(GZipMiddleware, minimum_size=1000)  # 开启gzip压缩
app.mount(
    "/static", StaticFiles(directory="templates/static"), name="static"
)  # 静态文件路
templates = Jinja2Templates(directory="templates")  # 模版文件路径


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/favicon.ico")
async def favicon():
    return FileResponse(
        "templates/favicon.ico",
        headers={"Content-Type": "image/x-icon", "Cache-Control": "max-age=3600"},
    )


@app.api_route(path="/api", methods=["GET"])
async def api(request: Request):
    return request.headers


@app.get("/upload")
async def get_upload():
    return RedirectResponse("/api", 307)


@app.post("/upload")
async def upload_file(request: Request, file: UploadFile):
    if not file:
        return Response("fail", 200)
    elif not file.filename:
        return Response("fail", 200)
    else:
        if not os.path.exists("upload"):
            os.mkdir("upload")
        with open(os.path.join("upload", file.filename), "wb") as f:
            for i in iter(lambda: file.file.read(1024 * 1024 * 256), b""):
                f.write(i)
        return Response("success", 200)


def iterfile(resource, s, e):
    with open(resource, mode="rb") as file:
        file.seek(s)
        data = file.read(e - s)
        yield data


@app.get("/{resource}")
def video_resource(
    resource: str = Path(
        regex=".+\.mp4.*|.+\.flv.*|.+\.m3u8.*",
        min_length=5,
        max_length=2048,
    ),
    range: str = Header(default=None),
):
    if not os.path.isfile(resource):
        return Response(None, status_code=404)
    else:
        start_str, end_str = (
            range.replace("bytes=", "").split("-") if range else ["0", ""]
        )
        start = int(start_str)
        end = int(end_str) if end_str else start + 1024 * 1024 * 16
        fileSize = os.path.getsize(resource)
        end = end if end < fileSize - 1 else fileSize
        headers = {
            "Content-Range": f"bytes {start}-{fileSize - 1}/{fileSize}",
            "Accept-Ranges": "bytes",
        }
        return StreamingResponse(
            iterfile(resource, start, end), status_code=206, headers=headers
        )


if __name__ == "__main__":
    subprocess.Popen(
        [
            "uvicorn",
            f"{os.path.split(os.path.splitext(__file__)[0])[1]}:app",
            "--host",
            "0.0.0.0",
            "--port",
            "443",
            "--ssl-keyfile",
            "server.key",
            "--ssl-certfile",
            "server.pem",
        ]
    )
    uvicorn.run(
        f"{os.path.split(os.path.splitext(__file__)[0])[1]}:app",
        host="0.0.0.0",
        port=80,
        reload=False,
    )
