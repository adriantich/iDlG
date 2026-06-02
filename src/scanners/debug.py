from zipfile import Path
import sys
import os
# debug only
sys.path.insert(0, os.path.dirname('src/.'))

from explorer.loader import VCFLoader
import os
from scanners.scanner_template import ScannerTemplate

test_file = os.path.join("test_data/small.vcf")
loader = VCFLoader(test_file)

self = ScannerTemplate(vcf_object=loader, chrom=["OV121081.1"])
chrom = None
window = None
step = None