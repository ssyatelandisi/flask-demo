# m3u8_parse

主要功能

* 下载m3u8文件解析播放

* 播放网络视频源MP4、FLV视频

* 播放本地视频

* 文件上传服务器功能

python环境：Python 3.7.7

创建虚拟环境：

`python -m venv .venv`

切换至虚拟环境：

`source .venv/Scripts/activate` #Linux

`.venv\Scripts\activate` #Windows

安装依赖包：

`pip install -r requirements.txt`

Windows编译：

`pyinstaller -Fc app.py -i icon.ico --version-file=version_info.txt -n=m3u8parse --add-data="templates;templates" --clean -y`
