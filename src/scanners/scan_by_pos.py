
from zipfile import Path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from explorer.loader import VCFLoader
from tqdm import tqdm
import os
import pandas as pd
import json


DEFAULT_WINDOW_SIZE = [100_000, 500_000]
DEFAULT_STEP = [100_000, 500_000]
DEFAULT_OUTPUT_DIR = "scan_results"

class ScannerByPos:
    def __init__(self, vcf_object: VCFLoader = None, window_size: list = None, step: list = None, chrom: list = None):
        print("Initializing ScannerByPos...")
        if vcf_object is None or vcf_object.records is None:
            print('No records provided')
            self.records = None
        else:
            self.records = vcf_object.records
        self.window_size = window_size if window_size is not None else DEFAULT_WINDOW_SIZE
        self.step = step if step is not None else DEFAULT_STEP
        self.chrom = chrom if chrom is not None else None
        self.results_mean = None
        self.results_sd = None
        self.result_index = None
        self.scanned = False


    def run_scan(self):
        self.results_mean, self.results_sd, self.result_index = self.scan_by_pos()
        self.scanned = True
        
    def scan_by_pos(self, chrom: list = None, window: list = None, step: list = None):
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
            min_pos = chr_records['POS'].min()
            max_pos = chr_records['POS'].max()
            print(f"Scanning chromosome {chr} from position {min_pos} to {max_pos}")

            for w in window:
                for s in step:
                    res_index = f"{chr}_{w}_{s}"
                    result_index.append((res_index, chr, w, s))
                    case_results_mean = []
                    case_results_sd = []
                    print(f"Scanning {chr} with window size {w} and step {s}")
                    for start in tqdm(range(min_pos, max_pos, s)):
                        end = start + w
                        # break
                        window_records = chr_records[(chr_records['POS'] >= start) & (chr_records['POS'] < end)]
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
    
    def save_to_parquet(self, output_dir: str):

        if output_dir is None:
            print("Output directory to default value 'scan_results'")
            output_dir = DEFAULT_OUTPUT_DIR
        
        os.makedirs(output_dir, exist_ok=True)
        
        for key, mean_data in self.results_mean.items():
            df_mean = pd.DataFrame(mean_data)
            df_mean.to_parquet(os.path.join(output_dir, f"{key}_mean.parquet"), compression="gzip")
        
        for key, sd_data in self.results_sd.items():
            df_sd = pd.DataFrame(sd_data)
            df_sd.to_parquet(os.path.join(output_dir, f"{key}_sd.parquet"), compression="gzip")
        
        # save in a json file the class parameters and the result index
        params = {
            "window_size": self.window_size,
            "step": self.step,
            "chrom": self.chrom,
            "result_index": self.result_index,
        }
        with open(os.path.join(output_dir, "scan_params.json"), "w") as f:
            json.dump(params, f, indent=4)

class ScannerByPosFromParquet(ScannerByPos):
    def __init__(self, input_dir: str = None):
        if input_dir is None:
            input_dir = DEFAULT_OUTPUT_DIR
        if not os.path.isdir(input_dir):
            print(f"Input directory '{input_dir}' does not exist. Please provide a valid directory.")
            return None
        self.results_mean = None
        self.results_sd = None
        self.result_index = None
        self.scanned = False
        self.load_from_parquet(input_dir)
    
    def load_from_json(self, json_file: str):
        if not os.path.isfile(json_file):
            print(f"JSON file '{json_file}' does not exist.")
            return None
        
        with open(json_file, "r") as f:
            params = json.load(f)
        
        self.window_size = params.get("window_size", DEFAULT_WINDOW_SIZE)
        self.step = params.get("step", DEFAULT_STEP)
        self.chrom = params.get("chrom", [])
        self.result_index = params.get("result_index", [])

    def load_from_parquet(self, input_dir: str):
        results_mean = {}
        results_sd = {}
        result_index = []
        if not Path(input_dir).is_dir():
            print(f"Input directory '{input_dir}' does not exist or is not a directory.")
            return None, None, None
        
        for file in os.listdir(input_dir):
            if file.endswith("_mean.parquet"):
                key = file.replace("_mean.parquet", "")
                df_mean = pd.read_parquet(os.path.join(input_dir, file))
                results_mean[key] = df_mean.to_dict(orient='records')
                result_index.append((key, *key.split('_')[1:]))  # Assuming key format is "chr_window_step"
            elif file.endswith("_sd.parquet"):
                key = file.replace("_sd.parquet", "")
                df_sd = pd.read_parquet(os.path.join(input_dir, file))
                results_sd[key] = df_sd.to_dict(orient='records')

        self.results_mean = results_mean
        self.results_sd = results_sd
        self.result_index = result_index
        self.scanned = True



