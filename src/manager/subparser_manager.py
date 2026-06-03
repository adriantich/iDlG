import os
import sys
import argparse

# Add the src directory to the Python path for standalone execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from explorer.explore_parser import ExplorerByPosParser, ExplorerBySNPParser
from export.exporter import ExporterParser



class SubParserManager:
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

        parser = self.subparsers.add_parser(
            'export_parquet_to_csv', 
            help='Export scan results from parquet to csv format',
            parents=[ExporterParser().parser()]
        )
        parser.set_defaults(func=ExporterParser().main)