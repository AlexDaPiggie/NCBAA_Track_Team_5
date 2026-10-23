"""Windows desktop entry point; owns its local server and native window."""
import ctypes
import os
from pathlib import Path
import socket
import sys
import threading
import time
import traceback

def main():
    import uvicorn
    import webview
    from fastapi.staticfiles import StaticFiles
    import backend.main as api

    webview.settings['ALLOW_DOWNLOADS'] = True

    root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
    assets = root / 'frontend' / 'dist'
    if not (assets / 'index.html').exists():
        raise RuntimeError('Dashboard build missing. Run build-desktop.ps1 first.')
    # Writable user data must stay outside a packaged application's bundle.
    api.DATA = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'ApronStaffingLab'
    api.DATA.mkdir(parents=True, exist_ok=True)
    api.app.mount('/', StaticFiles(directory=assets, html=True), name='desktop')
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(('127.0.0.1', 0))
    listener.listen(128)
    port = listener.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(api.app, host='127.0.0.1', port=port,
                                         log_config=None, access_log=False))
    thread = threading.Thread(target=server.run, kwargs={'sockets':[listener]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 20
        while not server.started:
            if not thread.is_alive() or time.monotonic() > deadline:
                raise RuntimeError('Local simulation engine could not start.')
            time.sleep(.05)
        webview.create_window('Apron | FBO Staffing Lab', f'http://127.0.0.1:{port}',
                              width=1440, height=940, min_size=(900, 650))
        webview.start(gui='edgechromium')
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        listener.close()

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        folder = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'ApronStaffingLab'
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'startup-error.log').write_text(traceback.format_exc(), encoding='utf-8')
        ctypes.windll.user32.MessageBoxW(0, f'{exc}\n\nDetails: {folder / "startup-error.log"}',
                                         'Apron could not start', 0x10)
        raise
