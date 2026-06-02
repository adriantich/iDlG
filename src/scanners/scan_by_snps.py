
from zipfile import Path
import sys
import os
# debug only
# sys.path.insert(0, os.path.dirname('src/.'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tqdm import tqdm
import os
from scanners.scanner_template import ScannerTemplate, ScannerFromParquetTemplate
from scanners.defaults import DEFAULT_WINDOW_SIZE_SNPS, DEFAULT_STEP_SNPS



class ScannerBySNP(ScannerTemplate):
    def define_window_step(self, window_size: list = None, step: list = None):
        self.window_size = window_size if window_size is not None else DEFAULT_WINDOW_SIZE_SNPS
        self.step = step if step is not None else DEFAULT_STEP_SNPS

    def scan(self, chrom: list = None, window: list = None, step: list = None):
        if self.records is None:
            print("No records to scan.")
            return None
        if chrom is None:
            chrom = self.chrom
        if chrom is None:
            chrom = set(self.records['CHROM'])
        if window is None:
            window = self.window_size
        if step is None:
            step = self.step
        
        results_mean = {}
        results_sd = {}
        result_index = []
        for chr in chrom:
            chr_records = self.records[self.records['CHROM'] == chr]
            min_pos = 0
            max_pos = chr_records['POS'].size

        ######
        ## ToDo: implement the scan by snp logic here
        ######

            print(f"Scanning chromosome {chr} with {max_pos} SNPs.")

            for w in window:
                for s in step:
                    if not self.force_windowstep and w < s:
                        print(f"Skipping combination of window size {w} and step {s} because window size is smaller than step size and force_windowstep is not set.")
                        continue
                    res_index = f"{chr}_{w}_{s}"
                    result_index.append((res_index, chr, w, s))
                    case_results_mean = []
                    case_results_sd = []
                    print(f"Scanning {chr} with window size {w} and step {s}")
                    for start in tqdm(range(min_pos, max_pos, s)):
                        end = start + w
                        # break
                        window_records = chr_records[start:end]
                        if not window_records.empty:
                            # do the col means for the samples
                            case_records_mean = window_records.drop(columns=['CHROM', 'POS', 'ID']).mean(skipna = True).to_dict()
                            case_records_mean['start'] = start
                            case_records_mean['end'] = end
                            case_results_mean.append(case_records_mean)

                            # do the col std for the samples
                            case_records_sd = window_records.drop(columns=['CHROM', 'POS', 'ID']).std(skipna = True).to_dict()
                            case_records_sd['start'] = start
                            case_records_sd['end'] = end
                            case_results_sd.append(case_records_sd)
                    
                    results_mean[res_index] = case_results_mean
                    results_sd[res_index] = case_results_sd
        return results_mean, results_sd, result_index

class ScannerBySNPFromParquet(ScannerFromParquetTemplate, ScannerBySNP):
    DEFAULT_WINDOW_SIZE = DEFAULT_WINDOW_SIZE_SNPS
    DEFAULT_STEP = DEFAULT_STEP_SNPS
    pass
    # def __init__(self, input_dir: str = None):
    #     if input_dir is None:
    #         input_dir = DEFAULT_OUTPUT_DIR
    #     if not os.path.isdir(input_dir):
    #         print(f"Input directory '{input_dir}' does not exist. Please provide a valid directory.")
    #         return None
    #     self.results_mean = None
    #     self.results_sd = None
    #     self.result_index = None
    #     self.scanned = False
    #     self.load_from_parquet(input_dir)
    



