import os
import sys
import argparse

# Add the src directory to the Python path for standalone execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from explorer.explorer import Explorer
from explorer.explorer import ExplorerParser
from scanners.scan_by_pos import ScannerByPos, ScannerByPosFromParquet
from scanners.scan_by_snps import ScannerBySNP, ScannerBySNPFromParquet

from scanners.defaults import DEFAULT_WINDOW_SIZE_SNPS, DEFAULT_STEP_SNPS


class ExplorerByPos(Explorer):
    Scanner = ScannerByPos
    ScannerFromParquet = ScannerByPosFromParquet

class ExplorerBySNP(Explorer):
    Scanner = ScannerBySNP
    ScannerFromParquet = ScannerBySNPFromParquet
    test_window_sizes = DEFAULT_WINDOW_SIZE_SNPS
    test_steps = DEFAULT_STEP_SNPS

class ExplorerByPosParser(ExplorerParser):
    def explorer(self,*args,**kwargs):
        return ExplorerByPos(*args, **kwargs)
    
    def test(self):
        print("Testing ExplorerByPosParser...")
        ExplorerByPos.test()

class ExplorerBySNPParser(ExplorerParser):
    def explorer(self,*args,**kwargs):
        return ExplorerBySNP(*args, **kwargs)
    
    def test(self):
        print("Testing ExplorerBySNPParser...")
        ExplorerBySNP.test()


class ExplorerSubParser:
    def __init__(self, subparsers):
        self.subparsers = subparsers
        self.explore_parser()
    
    def explore_parser(self):
        parser = self.subparsers.add_parser(
            'explore_positions', 
            help='Explore scan by position results with interactive plots',
            parents=[ExplorerByPosParser().parser()]
        )
        parser.set_defaults(func=ExplorerByPosParser().main)

        parser = self.subparsers.add_parser(
            'explore_snps', 
            help='Explore scan by snps results with interactive plots',
            parents=[ExplorerBySNPParser().parser()]
        )
        parser.set_defaults(func=ExplorerBySNPParser().main)
    

def main():
    # Main parser
    parser = argparse.ArgumentParser(description="Explorer: Explore scan results with interactive plots")
    
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