import argparse
from explorer.explore_parser import ExplorerSubParser


def main():
    # Main parser
    parser = argparse.ArgumentParser(
        description="IDLG: A versatile tool for data management and analysis. \nUse the subcommands to access specific functionalities."
    )
    
    # Create subparsers
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Initialize subparsers
    ExplorerSubParser(subparsers)
    
    # Parse arguments
    args = parser.parse_args()

    # Route to appropriate function
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()