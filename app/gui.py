import threading
import webbrowser


def open_in_browser(url: str) -> None:
    def _open():
        webbrowser.open(url)

    # Small delay so Flask is ready before browser request starts.
    threading.Timer(1.0, _open).start()
