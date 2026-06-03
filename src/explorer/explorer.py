import os
import sys
import argparse

# Add the src directory to the Python path for standalone execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from explorer.interactive_plot import InteractivePlot
from loader import VCFLoader
from scanners.defaults import DEFAULT_OUTPUT_DIR
from abc import ABC, abstractmethod


class Explorer(ABC):
    def __init__(self, 
                 plot=False, 
                 input_file=None, 
                 from_parquet=False, 
                 output_dir=None,
                 chrom=None,
                 window_sizes=None,
                 steps=None,
                 force_windowstep=False):
        self.plot = plot
        self.input_file = input_file
        self.from_parquet = from_parquet
        self.output_dir = output_dir
        self.chrom = chrom
        self.window_sizes = window_sizes
        self.steps = steps
        self.force_windowstep = force_windowstep
        self.scanner = None
        self.main()

    Scanner = None
    ScannerFromParquet = None
    test_window_sizes = None
    test_steps = None
    
    def load_data(self):
        loader = VCFLoader(self.input_file)
        print('Running scan...')
        self.scanner = self.Scanner(
            vcf_object = loader,
            chrom=self.chrom,
            window_size=self.window_sizes,
            step=self.steps,
            force_windowstep=self.force_windowstep
        )
        self.scanner.run_scan()
        print('Saving results to parquet...')
        self.scanner.save_to_parquet(self.output_dir)
    
    def load_results(self):
        if self.from_parquet and self.input_file is not None:
            self.scanner = self.ScannerFromParquet(self.input_file)

    
    def main(self):
        if self.from_parquet:
            self.load_results()
        else:
            self.load_data()
        
        if self.plot:
            plotter = InteractivePlot(self.scanner)
            plotter = plotter.build_figure()
            plotter.show()

    @classmethod
    def test(cls):
        test_file = os.path.join(os.path.dirname(__file__), "../../test_data/small.vcf")
        # test_file = "/home/aantich/Nextcloud/2_PROJECTES/iDlG_paper/iDlG/test_data/file_test.vcf"

        loader = VCFLoader(test_file)

        scaner = cls.Scanner(vcf_object = loader, chrom= ["OV121081.1"], window_size=cls.test_window_sizes, step=cls.test_steps)
        # scaner = cls.Scanner(vcf_object = loader, chrom= ["OV121097.1", "OV121081.1"])
        scaner.run_scan()
        scaner.save_to_parquet("test_scan_results")

        plotter = InteractivePlot(scaner)
        fig = plotter.build_figure()
        fig.show()


DESCRIPTION = """
Explore scan results with interactive plots.
"""
class ExplorerParser(ABC):

    CLASS_DEFAULT_WINDOW_SIZE = None
    CLASS_DEFAULT_STEP = None

    def __init__(self):
        pass

    @classmethod
    def parser(cls):
        parser = argparse.ArgumentParser(
            description=DESCRIPTION,
            add_help=False
        )
        parser.add_argument(
            '-t', '--test',
            action='store_true',
            help='Run test plot'
        )
        parser.add_argument(
            '-p', '--plot',
            action='store_true',
            default=False,
            help='Generate interactive plot from scan results'
        )
        parser.add_argument(
            '-i', '--input',
            type=str,
            help='Input vcf file or directory containing scan results in parquet format'
        )
        parser.add_argument(
            '-q', '--from_parquet',
            action='store_true',
            default=False,
            help='Indicates that the input is a directory containing parquet files'
        )
        parser.add_argument(
            '-o', '--output_dir',
            type=str,
            help=f'Directory to save the parquets (default: {DEFAULT_OUTPUT_DIR})'
        )
        parser.add_argument(
            '-c', '--chrom',
            nargs='+',
            help='List of chromosomes to explore (e.g. -c chr1 chr2)'
        )
        parser.add_argument(
            '-w', '--window_sizes',
            nargs='+',
            type=str,
            help=f'List of window sizes to explore (default: {" ".join(str(x) for x in cls.CLASS_DEFAULT_WINDOW_SIZE)})'
        )
        parser.add_argument(
            '-s', '--steps',
            nargs='+',
            type=str,
            help=f'List of step sizes to explore (default: {" ".join(str(x) for x in cls.CLASS_DEFAULT_STEP)})'
        )
        parser.add_argument(
            '-f', '--force_windowstep',
            action='store_true',
            default=False,
            help='Forces the evaluation of every possible window size x step size combination.'\
                 'If not set, combinations where the step size exceeds the window size are' \
                 'skipped (e.g., window size 100 with step size 1000).'\
        )
        return parser
    
    def parser_main(self):
        parser_main = argparse.ArgumentParser(
            description=DESCRIPTION,
            parents=[self.parser()]
        )
        args = parser_main.parse_args()
        return args
    
    @abstractmethod
    def test():
        pass

    @abstractmethod
    def explorer():
        pass
    
    def main(self, args=None):
        if args is None:
            args = self.parser_main()
        print(args)
        
        # if windows have commas separate values
        if args.window_sizes:
            args.window_sizes = [int(x) for x in ",".join(args.window_sizes).split(",")]
        if args.steps:
            args.steps = [int(x) for x in ",".join(args.steps).split(",")]


        if args.test:
            self.test()
        else:
            explorer = self.explorer(
                plot=args.plot,
                input_file=args.input,
                from_parquet=args.from_parquet,
                output_dir=args.output_dir,
                chrom=args.chrom,
                window_sizes=args.window_sizes,
                steps=args.steps,
                force_windowstep=args.force_windowstep
            )
        
        

