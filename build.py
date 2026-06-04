import sys
import subprocess
import platform
import shutil
from pathlib import Path

VENV_DIR = Path(".venv")
REQ_FILE = Path("requirements.txt")


def run(cmd):
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)


def venv_python_path():
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def venv_pip_path():
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"


def python_venv_package():
    return f"python{sys.version_info.major}.{sys.version_info.minor}-venv"


def check_venv_support():
    result = subprocess.run(
        [sys.executable, "-c", "import ensurepip"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode == 0:
        return

    package = python_venv_package()
    print(
        "\nPython venv support is not installed for this interpreter.\n"
        "Install the matching Ubuntu/Debian package, then run this script again:\n\n"
        f"    sudo apt update\n"
        f"    sudo apt install -y {package}\n\n"
        f"Current Python: {sys.executable} "
        f"({sys.version_info.major}.{sys.version_info.minor})"
    )
    raise SystemExit(1)


def ensure_venv():
    python_path = venv_python_path()
    if VENV_DIR.exists() and python_path.exists():
        print(".venv already exists")
        return

    if VENV_DIR.exists():
        print("Removing incomplete .venv")
        shutil.rmtree(VENV_DIR)

    check_venv_support()
    run([sys.executable, "-m", "venv", str(VENV_DIR)])


def main():
    # 1. Tạo virtual environment nếu chưa có
    ensure_venv()

    # 2. Xác định pip trong venv
    pip_path = venv_pip_path()
    python_path = venv_python_path()

    # 3. Upgrade pip
    run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"])

    # 4. Cài requirements
    if REQ_FILE.exists():
        run([str(pip_path), "install", "-r", str(REQ_FILE)])
    else:
        print("requirements.txt not found")


if __name__ == "__main__":
    main()
