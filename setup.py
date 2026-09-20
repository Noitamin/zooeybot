"""Install the bot's runtime dependencies using the current Python interpreter."""

from pathlib import Path
import subprocess
import sys


if __name__ == "__main__":
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-r",
        str(Path(__file__).with_name("requirements.txt")),
    ])
