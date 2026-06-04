import os
import sys
import subprocess
import platform

VENV_DIR = ".venv"
REQ_FILE = "requirements.txt"


def run(cmd):
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)


def main():
    # 1. Tạo virtual environment nếu chưa có
    if not os.path.exists(VENV_DIR):
        run([sys.executable, "-m", "venv", VENV_DIR])
    else:
        print(".venv already exists")

    # 2. Xác định pip trong venv
    if platform.system() == "Windows":
        pip_path = os.path.join(VENV_DIR, "Scripts", "pip.exe")
        python_path = os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        pip_path = os.path.join(VENV_DIR, "bin", "pip")
        python_path = os.path.join(VENV_DIR, "bin", "python")

    # 3. Upgrade pip
    run([python_path, "-m", "pip", "install", "--upgrade", "pip"])

    # 4. Cài requirements
    if os.path.exists(REQ_FILE):
        run([pip_path, "install", "-r", REQ_FILE])
    else:
        print("requirements.txt not found")


if __name__ == "__main__":
    main()