"""跨平台 WSGI 啟動（Windows 用 Waitress，Linux 用 Gunicorn）"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)


def main():
    host = os.getenv("BIND_HOST", "127.0.0.1")
    port = os.getenv("PORT", os.getenv("RUN_PORT", "9000"))
    bind = f"{host}:{port}"

    if sys.platform == "win32":
        from waitress import serve
        from config.wsgi import application

        threads = int(os.getenv("WAITRESS_THREADS", "8"))
        print(f"Waitress listening on http://{bind} (threads={threads})")
        serve(application, host=host, port=int(port), threads=threads)
    else:
        from gunicorn.app.wsgiapp import run

        workers = os.getenv("GUNICORN_WORKERS", "2")
        timeout = os.getenv("GUNICORN_TIMEOUT", "120")
        sys.argv = [
            "gunicorn",
            "config.wsgi:application",
            "--bind",
            bind,
            "--workers",
            workers,
            "--timeout",
            timeout,
        ]
        run()


if __name__ == "__main__":
    main()
