import argparse
from .app import main



class App:
    def __init__(self):
        self.main()
    
    def main(self):
        main()

class AppParser:
    def __init__(self):
        pass
    def parser(self):
        parser = argparse.ArgumentParser(
            description='Run the Graphical User Interface for IDLG',
            add_help=False
        )
        return parser
    
    def parser_main(self):
        parser_main = argparse.ArgumentParser(
            description="Run the Graphical User Interface for IDLG",
            parents=[self.parser()]
        )
        args = parser_main.parse_args()
        return args

    def main(self, args=None):
        if args is None:
            args = self.parser_main()
        App()
        