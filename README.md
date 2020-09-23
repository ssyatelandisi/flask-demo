# m3u8_parse

python环境：Python 3.7.7

创建虚拟环境：

`python -m venv .venv`

切换至虚拟环境：

`source .venv/Scripts/activate` #Linux

`.venv\Scripts\activate` #Windows

安装依赖包：

`pip install -r requirements.txt`

编译：

`pyinstaller -Fc run.py -i icon.ico --version-file=version_info.txt -n=m3u8parse
`