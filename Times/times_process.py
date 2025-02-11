## Times of Malta Routine Procedure ##

# Imports
import pandas as pd
from datetime import datetime
import time
import schedule
from times_utils import scraper, data_cleaning, epu_data
import warnings
warnings.filterwarnings('ignore')

# Function to Outline the Process to collect Data from the Times of Malta
def times_process():
    # Scrape New Articles Posted on the Website
    scraped_df = scraper()
    # Clean Scraped Data
    clean_df = data_cleaning(scraped_df)
    # Flag Articles as EPU Relevant
    articles_df, month_counts_df = epu_data(clean_df)
    # Print the Latest Observation for Checks
    print(month_counts_df.tail())
    
# Function to Regularly Execute Times of Malta Process on the First Day of Every Month
def schedule_monthly():
    if datetime.now().day == 1:
        times_process()

# Schedule Process
schedule.every().day.at("14:00").do(schedule_monthly) 

# Keep the script running to execute the scheduled tasks
while True:
    schedule.run_pending()
    time.sleep(60)