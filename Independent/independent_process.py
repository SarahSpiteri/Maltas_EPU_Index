## Independent Routine Procedure ##

# Imports
import pandas as pd
from datetime import datetime
import time
import schedule
from independent_utils import scraper, data_cleaning, epu_data
import warnings
warnings.filterwarnings('ignore')

# Function to Outline the Process to collect Data from the Malta Independent
def independent_process():
    # Scrape New Articles Posted on the Website
    scraped_df = scraper()
    # Clean Scraped Data
    clean_df = data_cleaning(scraped_df)
    # Flag Articles as EPU Relevant
    articles_df, month_counts_df = epu_data(clean_df)
    # Print the Latest Observation for Checks
    print(month_counts_df.tail())
    
# Function to Regularly Execute Malta Independent Process on the First Day of Every Month
def schedule_monthly():
    if datetime.now().day == 1:
        independent_process()

# Schedule Process
schedule.every().day.at("10:00").do(schedule_monthly) 

# Keep the script running to execute the scheduled tasks
while True:
    schedule.run_pending()
    time.sleep(60)