# How to develop

#### 20260930
I have finished the suggest regions class. We have to decide wether the windows are settable or not. Also if this has to 
work as an standalone functionality or not. 
The algorithm does the following:
- For each position do a gmm for three different k: 1, no clusters, 2, no hibrids, 3, three groups. 
- Test which model fits better and if k == 2|3 then assign a class to each sample/positon k=2;0|2 and k=3;0|1|2
- then calculate for each possible window defined by a the fixed_w parameter:
    - Get all the positions with k == 2|3 
    - Make all the pairwise comparisons to check for consistency in the classification and weight each comparison by the BIC gap between the best k and the second and the confidence of the assignment.
    - Get the average (weighted) of all pairwise comparisons.
    - Multiply it by the proportion of k == 2|3 in the window and this is the score
    - score == 1 max consistency with k != 1 ; score == 0 no clustering 
- for each position check the difference between the right and left window. Thus there is a gap and the start and end of length == fixed_w
- check for peaks of maximum differences between left and right windows. This peaks define the boundaries
- Calculate the score for each window enclosed between windows and give the same score value to all the intermediate positions in between the boundaries. This is the final result.

The plot has been disabled until optimisation and it will probably be made in R.

#### 20260929

up to date I have created the suggest_regions.py and I need to integrate it into the workflow.

### Functionality
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




