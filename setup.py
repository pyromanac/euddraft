import sys
from distutils.core import setup
import py2exe

sys.argv.append('py2exe')

build_exe_options = {
    "packages": ["importlib", "json", "eudplib"],
    "compressed": True,
    "optimize": 2,
}

setup(
    console=["euddraft.py"],
    options={'py2exe': build_exe_options}
)
