# 输入完整地址
# 获取路径，文件名
# get请求内容
# 拼接保存
from requests import get
from urllib.parse import urljoin, urlparse
from os import getenv, path
from re import search


class M3U8:
    def input_url(self):
        self.url = input("输入完整的m3u8地址：\n>")

    def register_uri(self):
        self.uri = urljoin(self.url, "./")
        self.parseResult = urlparse(self.url)
        self.fileName = (
            path.split(self.parseResult.path)[-1]
            if path.split(self.parseResult.path)[-1]
            else "index.html"
        )
        print("\n文件名：{}".format(self.fileName))

    def query_get(self):
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

    def modify(self):
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
        self.input_url()
        self.register_uri()
        self.query_get()
        self.modify()
        print("运行结束")


if __name__ == "__main__":
    m3u8 = M3U8()
    m3u8.run()
