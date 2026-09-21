import subprocess
import os
from pathlib import Path
import time

target_dir = os.path.expanduser("~/programming")
path = Path("~/programming").expanduser()

for i in range(10):
    time.sleep(1.5)
    try:
        subprocess.run(["termux-vibrate", "-d", "500", "-f"])
    except FileNotFoundError:
        print("Это не телефон. Действие - вибрирую")


