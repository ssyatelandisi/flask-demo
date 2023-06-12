pyinstaller -Fc app.py -i icon.ico --version-file=version_info.txt -n="Flask App" --add-data="templates;templates" --clean -y
