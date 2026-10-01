# How to develop

### iglg.py
This script is the main one, always has to be called. This will distribute the main functionalities. 

### Functionality
#### idlg.py
idlg.py calls a subparser 

```from manager.subparser_manager import SubParserManager```

Three functionalities have been debeloped to date
- [Explore](#explore)
    - [```explore_positions```](#explore-by-position)
    - [```explore_snps```](#explore-by-snps)
- [```export_parquet_to_csv```](#export)
- [```gui```](#app)

#### Manager
The different funcitonalities are managed by the ```src/manager/subparser_manager.py```

### Explore 
This functionality has two branches, by pos and by snps.
They both inherits from a Explorer class and it is handled in the explorer folder

##### src/explorer/explore_parser.py
In this script the two explorers and their parsers are created.

##### src/explorer/explorer.py
This script unifies the two methodologies because each scanner retrieves the same data structure

#### Explore by Positions
The explore by positions shifts each window by positions. The number of SNPs in each window is variable

#### Explore by SNPs
The explore by SNPs shifts each window by number of SNP. The number of SNPs is the same for all windows but the recovery is variable. The x axis is not equivalent to the chromosome length.

#### Scanner
The main scanner algorithm is in ```scanner_template.py``` and each method inherits from it.

### Export
It simply export the parquets to csv format.

### App


