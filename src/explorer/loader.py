import vcfpy
from tqdm import tqdm
from pathlib import Path
import pandas as pd

class VCFLoader:
    def __init__(self, vcf_file):
        self.vcf_file = vcf_file
        self.records = self.load()
        self.records = self.to_dataframe()
        print(f"Loaded {self.records.shape[0]} records from VCF file.")
        print(f"Numer of chromosomes: {len(set(self.records['CHROM']))}")
        print(f"Number of positions per chromosome: { {chrom: len(self.records[self.records['CHROM'] == chrom]["POS"]) for chrom in set(self.records['CHROM'])} }")
        # print(self.records.head())
        
    @staticmethod
    def transform_gt(gt):
        if gt == '0/0':
            return 0
        elif gt == '0/1':
            return 1
        elif gt == '1/1':
            return 2
        else:
            return None
    
    def to_dataframe(self):
        if self.records is not None:
            df = pd.DataFrame(self.records)
            # Reorder columns to have CHROM, POS, ID at the beginning
            cols = ['CHROM', 'POS', 'ID'] + [col for col in df.columns if col not in ['CHROM', 'POS', 'ID']]
            df = df[cols]
            return df
        else:
            print("No records to convert to DataFrame.")
            return None

    def load(self):
        try:
            with vcfpy.Reader.from_path(self.vcf_file) as reader:
                records = []
                for record in tqdm(reader):
                    results = {x.sample: VCFLoader.transform_gt(gt = x.data['GT']) for x in record.calls}
                    results['CHROM'] = record.CHROM
                    results['POS'] = record.POS
                    results['ID'] = record.ID[0]
                    records.append(results)
            return records
        except Exception as e:
            print(f"Error loading VCF file: {e}")
            return None
