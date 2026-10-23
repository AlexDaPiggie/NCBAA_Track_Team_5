"""Exercise the desktop server lifecycle without opening an interactive window."""
import sys
from types import SimpleNamespace
import httpx
import desktop

def test_desktop_serves_dashboard_and_engine(tmp_path, monkeypatch):
    import backend.main as api
    monkeypatch.setattr(api, 'DATA', tmp_path)
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path))
    captured = {}
    def create_window(title, url, **kwargs):
        captured['url'] = url
    def start(**kwargs):
        with httpx.Client(base_url=captured['url'], timeout=30, trust_env=False) as client:
            assert client.get('/').status_code == 200
            response = client.post('/api/simulate', json={'scenario':'Low'})
            assert response.status_code == 200
            assert len(response.json()['options']) == 3
    monkeypatch.setitem(sys.modules, 'webview', SimpleNamespace(settings={},create_window=create_window,start=start))
    desktop.main()
    # The app's local service must stop when its window loop returns.
    try:
        httpx.get(captured['url'], timeout=1, trust_env=False)
    except (httpx.ConnectError, httpx.ConnectTimeout):
        pass
    else:
        raise AssertionError('Desktop server still running after window close')
