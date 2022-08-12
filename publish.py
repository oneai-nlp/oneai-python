from distutils.command.upload import upload
import os
import shutil
import subprocess
from setuptools import setup
import credentials

PATH_DIST = "./dist"
PREFIX = "\33[34m●\33[36m▲\33[35m▮\33[0m"

if os.path.exists(PATH_DIST):
    shutil.rmtree(PATH_DIST)
    print(PREFIX, "deleted dist folder")
else:
    print(PREFIX, "dist folder not found")

print(PREFIX, "running build")
try:
    code = subprocess.run(
        ["python3", "-m", "build"], stderr=subprocess.DEVNULL
    ).returncode
    if code:
        setup()
except Exception as e:
    print(PREFIX, f"build failed:\n{repr(e)}")
else:
    print(PREFIX, "build successful")
    print(PREFIX, f"publishing package")
    try:
        upload(credentials.settings, ["dist/*"])
    except Exception as e:
        print(PREFIX, "publishing failed:")
        raise e

    print(PREFIX, f"package published successfuly")
