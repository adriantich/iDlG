

import argparse
import pandas as pd

# input file
input_file = "test_scan_results/OV121081.1_500_100_mean.parquet"

# output file
output_file = "OV121081.1_500_100_mean.csv"


class Exporter:
    def __init__(self, input_file=None, output_file=None):
        self.input_file = input_file
        self.output_file = output_file
        self.main()
    
    def main(self):
        if self.input_file is None or self.output_file is None:
            print("Input file and output file must be provided.")
            return
        df = pd.read_parquet(self.input_file)
        df.to_csv(self.output_file, index=False)

class ExporterParser:
    def __init__(self):
        pass
    def parser(self):
        parser = argparse.ArgumentParser(
            description='Export scan results from parquet to csv format',
            add_help=False
        )
        parser.add_argument(
            '-i', '--input_file',
            type=str,
            required=True,
            help='Path to the input parquet file containing the scan results'
        )
        parser.add_argument(
            '-o', '--output_file',
            type=str,
            required=True,
            help='Path to the output CSV file where the results will be saved'
        )
        return parser
    
    def parser_main(self):
        parser_main = argparse.ArgumentParser(
            description="Exporter: Export scan results from parquet to csv format",
            parents=[self.parser()]
        )
        args = parser_main.parse_args()
        return args

    def main(self, args=None):
        if args is None:
            args = self.parser_main()
        Exporter(input_file=args.input_file, output_file=args.output_file)
        


# class ExporterSubParser:
#     def __init__(self, subparsers):
#         self.subparsers = subparsers
#         self.export_parser()
    
#     def export_parser(self):
#         parser = self.subparsers.add_parser(
#             'export_parquet_to_csv', 
#             help='Export scan results from parquet to csv format',
#             parents=[ExporterParser().parser()]
#         )
#         parser.set_defaults(func=ExporterParser().main)

        