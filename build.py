import os
import sys
import subprocess
import platform
import shutil
import tempfile
from pathlib import Path

VENV_DIR = Path(".venv")
REQ_FILE = Path("requirements.txt")
BUILD_MARKER = VENV_DIR / ".build_complete"


def run(cmd):
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)


def is_windows():
    return platform.system() == "Windows"


def is_linux():
    return platform.system() == "Linux"


def linux_id_like():
    os_release = Path("/etc/os-release")
    if not os_release.exists():
        return set()

    values = set()
    for line in os_release.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in {"ID", "ID_LIKE"}:
            values.update(value.strip().strip('"').lower().split())
    return values


def is_ubuntu_or_debian():
    values = linux_id_like()
    return bool(values & {"ubuntu", "debian"})


def venv_python_path():
    if is_windows():
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def venv_pip_path():
    if is_windows():
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"


def venv_activate_path():
    if is_windows():
        return VENV_DIR / "Scripts" / "activate.bat"
    return VENV_DIR / "bin" / "activate"


def python_venv_package():
    return f"python{sys.version_info.major}.{sys.version_info.minor}-venv"


def system_package_cmd(*args):
    if not is_linux() or not is_ubuntu_or_debian():
        raise RuntimeError(
            "Automatic venv package installation is only supported on Ubuntu/Debian"
        )

    if shutil.which("apt") is None:
        raise RuntimeError("apt is required to install the missing python venv package")

    if os.geteuid() == 0:
        return ["apt", *args]

    if shutil.which("sudo") is None:
        raise RuntimeError("sudo is required to install the missing python venv package")

    return ["sudo", "apt", *args]


def restart_script():
    script_path = Path(__file__).resolve()
    print("Running:", sys.executable, str(script_path))
    os.execv(sys.executable, [sys.executable, str(script_path), *sys.argv[1:]])


def install_venv_support():
    if is_windows():
        raise RuntimeError(
            "Windows should include venv with Python. Reinstall Python and enable pip/venv."
        )

    package = python_venv_package()
    run(system_package_cmd("update"))
    run(system_package_cmd("install", "-y", package))

    result = subprocess.run(
        [sys.executable, "-c", "import ensurepip"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Installed {package}, but ensurepip is still unavailable")

    restart_script()


def check_venv_support():
    result = subprocess.run(
        [sys.executable, "-c", "import ensurepip"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode == 0:
        return

    print(
        "\nPython venv support is not installed for this interpreter.\n"
        "Installing the matching Ubuntu/Debian package automatically.\n"
        f"Current Python: {sys.executable} "
        f"({sys.version_info.major}.{sys.version_info.minor})"
    )
    install_venv_support()


def ensure_venv():
    python_path = venv_python_path()
    if VENV_DIR.exists() and python_path.exists():
        print(".venv already exists")
        return False

    if VENV_DIR.exists():
        print("Removing incomplete .venv")
        shutil.rmtree(VENV_DIR)

    check_venv_support()
    run([sys.executable, "-m", "venv", str(VENV_DIR)])
    return True


def install_dependencies(force=False):
    pip_path = venv_pip_path()
    python_path = venv_python_path()

    if BUILD_MARKER.exists() and not force:
        print("Dependencies already installed")
        return

    run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"])

    if REQ_FILE.exists():
        run([str(pip_path), "install", "-r", str(REQ_FILE)])
    else:
        print("requirements.txt not found")

    BUILD_MARKER.write_text("ok\n", encoding="utf-8")


def activate_venv_shell():
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print(f"Virtual environment ready: {VENV_DIR}")
        return

    activate_path = venv_activate_path()
    if not activate_path.exists():
        print(f"Activate script not found: {activate_path}")
        return

    print("\nVirtual environment is ready.")

    if is_windows():
        print(f"Opening activated Windows cmd: {activate_path}")
        subprocess.call(["cmd.exe", "/k", str(activate_path)])
        return

    shell = shutil.which("bash") or "/bin/bash"

    rc_file = None
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
            rc_file = Path(tmp.name)
            user_rc = Path.home() / ".bashrc"
            if user_rc.exists():
                tmp.write(f'source "{user_rc}"\n')
            tmp.write(f'source "{activate_path.resolve()}"\n')
            tmp.write('echo "Activated virtual environment. Type exit to return."\n')

        print(f"Opening activated shell: {shell}")
        subprocess.call([shell, "--rcfile", str(rc_file), "-i"])
    finally:
        if rc_file and rc_file.exists():
            rc_file.unlink()


def main():
    # 1. Tạo virtual environment nếu chưa có
    venv_created = ensure_venv()

    # 2. Cài dependencies một lần cho máy mới
    install_dependencies(force=venv_created)

    # 3. Mở shell đã activate venv nếu đang chạy từ terminal
    activate_venv_shell()


if __name__ == "__main__":
    main()
