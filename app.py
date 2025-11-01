import webview

if __name__ == "__main__":
    window = webview.create_window(
        "Speach Teacher", "frontend/index.html", width=900, height=690, resizable=False
    )
    webview.start()