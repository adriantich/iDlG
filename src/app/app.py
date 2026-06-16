
from shiny import App

from .server.server import app_server
from .ui.layout import app_ui



def main():
    app = App(app_ui(), app_server)
    app.run()


if __name__ == "__main__":
    main()