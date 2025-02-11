# Malta's EPU Index

This repository displays the procedure developed to calculate the Economic Policy Uncertainty (EPU) Index for Malta on a monthly basis. 

The repository only includes the code files that are used by the Economic Research Office at the Central Bank of Malta to regularly scrape, clean and flag articles from the four identified outlets, as identified in [Sant and Spiteri (2024)](https://www.centralbankmalta.org/site/Publications/Economic%20Research/2024/WP-07-2024.pdf?revcount=2398). No data files are provided in fairness to the terms and conditions of the listed platforms.

Within the local repository every outlet folder includes two further folders, one containing the raw scraped data and the files with the cleaned datasets. Moreover, each outlet folder would contain a "_monthly.csv" file (containing the number of total and flagged articles, per month) and "_working.csv" file (containing shortlisted articles for analysis). The "_process.py" files are deployed on the terminal of an inhouse workhorse for automated use.

The calculated index is made available on the [website of the Central Bank of Malta](https://www.centralbankmalta.org/epu-index) within the first week of every month.
