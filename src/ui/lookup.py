import webbrowser

def open_onelook(word: str) -> None:
    url = f"https://www.onelook.com/?w={word}"
    webbrowser.open(url, new=2)