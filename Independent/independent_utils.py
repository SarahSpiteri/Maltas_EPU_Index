## Malta Today Routine Procedure Functions ##

# Imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import pandas as pd
import numpy as np
from datetime import datetime
import datetime as dt
from dateutil.relativedelta import relativedelta
import re
import time
import math
import nltk
from nltk.stem import SnowballStemmer   
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords
import warnings
warnings.filterwarnings('ignore')

# Funtion for Random Waiting Time
def wait_time(init_sec = 0):
    time.sleep(init_sec + np.random.choice([x/10 for x in range(7,22)]))
        
# Function to get text in selective lowercase form
def abbr_or_lower(word):
    if re.match('([A-Z]+[a-z]*){2,}', word):
        return word
    else:
        return word.lower()
    
# Create Function to Pre-Process Text
def tokenize(words, modulation, lowercase='basic'):
    tokens = re.split(r'\W+', words)
    stems = []
    # Get comprehensive set of stopwords
    stop_words = set(stopwords.words('english'))
    for token in tokens:
        # filter out any tokens not containing letters (e.g., numeric tokens, raw punctuation)
        if lowercase == 'custom':
            # Custom lowercase to allow for case emphasis
            lowers = abbr_or_lower(token)
        if lowercase == 'basic':
            # Impose lowercase to all text
            lowers = abbr_or_lower(token).lower()
        if lowers not in stop_words:
            if re.search('[a-zA-Z]', lowers):
                # Lowercase (based on lowercase chosen option)
                if modulation == 0:
                    stems.append(lowers)
                # Stemming
                if modulation == 1:
                    porter = SnowballStemmer("english")
                    stems.append(porter.stem(lowers)) 
                # Lemmatizing
                if modulation == 2:
                    lmtzr = WordNetLemmatizer()
                    stems.append(lmtzr.lemmatize(lowers))
    return stems

# Function to Flag Articles Containing EPU Terms
def get_article_epu_flag(articles, economic_terms, policy_terms, uncertainty_terms, policy_category_terms='NA', pre_processing_modulation=0, pre_processing_lowercase='basic'):
    EPU_flag = []
    E = []
    P = []
    U = []
    P_CAT = []
    # Text pre-processing of Terms lists
    for term in economic_terms:
        E.append(' '.join(tokenize(term, pre_processing_modulation, pre_processing_lowercase)))
    for term in policy_terms:
        P.append(' '.join(tokenize(term, pre_processing_modulation, pre_processing_lowercase)))
    for term in uncertainty_terms:
        U.append(' '.join(tokenize(term, pre_processing_modulation, pre_processing_lowercase)))
    if policy_category_terms != 'NA':
        for term in policy_category_terms:
            P_CAT.append(' '.join(tokenize(term, pre_processing_modulation, pre_processing_lowercase))) 
    # Loop through Articles
    for article in articles:  
        # Turn list of pre-processed article text to string
        text = ' '.join(article)
        # Loop through article text for EPU terms
        flag = []
        for eco_term in E:
            if eco_term in text:
                for pol_term in P:
                    if pol_term in text:
                        for unc_term in U:
                            if unc_term in text:
                                if policy_category_terms == 'NA':
                                    flag.append(1)
                                else:
                                    for cat_term in P_CAT:
                                        if cat_term in text:
                                            flag.append(1)                           
        # Add Observation for final variable
        if len(flag) != 0:
            EPU_flag.append(1)
        else:
            EPU_flag.append(0)
    return EPU_flag

# Function for Malta Today Scraper
def scraper():
    # Specify Web Driver with Battery of Options
    options = webdriver.ChromeOptions()
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("start-maximized") 
    options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--incognito") 
    options.add_argument("--disable-gpu")
    service_driver = Service('chromedriver.exe')
    driver = webdriver.Chrome(service=service_driver, options=options)
    # Main Page Scraper
    # Settings
    base_url = 'https://www.independent.com.mt/'
    stop_date = datetime.today() - relativedelta(months=1)
    top_date = stop_date.replace(day=1)
    stop_date = stop_date.strftime('%Y-%m-%d')
    stop_date = datetime.strptime(stop_date, '%Y-%m-%d')
    # Data Placeholders
    links = []
    titles = []
    summaries = []
    dates = []
    categories = []
    # Loop Over Sections
    for section in ['local', 'business']:
        pg = 1
        section_dates = []
        #Loop Over Pages Until Date Condition is Met
        while True:
            # Set Link
            url = base_url + section + '?pg=' + str(pg)
            # Open Webpage
            try:
                driver.get(url)
                wait_time(9)
            except TimeoutException:
                driver.refresh()
                wait_time(13)
            # Obtain Page Contents
            page_contents = driver.find_elements(By.CLASS_NAME, "snippet-container")
            # Assign Article Details to Placeholders
            for article in page_contents:
                # Links
                links.append(article.find_element(By.TAG_NAME, 'a').get_attribute('href'))
                # Text Content
                info_list = article.text.split('\n')
                # Titles
                titles.append(info_list[0])
                # Summaries
                summaries.append(info_list[-1])
                # Dates
                # Parse the string to a datetime object
                article_date = datetime.strptime(info_list[1], '%A, %d %B %Y, %H:%M')
                # Format the datetime object to the desired output format
                dates.append(article_date.strftime('%Y-%m-%d'))
                section_dates.append(article_date.strftime('%Y-%m-%d'))
                # Categories
                categories.append(section)
            wait_time(3)
            # Stop When Reaching Already Scraped articles
            if sum(1 for date in section_dates if datetime.strptime(date,'%Y-%m-%d') < stop_date) > 5:
                break
            # Move to Next Page
            pg += 1
    print('Main Page Scraping Completed.')
    # Get scraped data into dataframe format
    independent = pd.DataFrame()
    independent['Link'] = links
    independent['Date'] = dates
    independent['Title'] = titles
    independent['Summary'] = summaries
    independent['Category'] = categories
    # Drop Duplicates
    independent = independent.drop_duplicates(subset=['Link'])
    # Individual Pages Scraper
    # Get List of Article Links
    article_links = set(independent['Link'].tolist())
    # Scrape Articles
    articles_lst = []
    counter = 1
    # Loop Over Articles
    for link in article_links:
        # Open Webpage
        try:
            driver.get(link)
        except TimeoutException:
            driver.quit()
            driver = webdriver.Chrome(service=service_driver, options=options)
            driver.get(link)
        wait_time(9)
        # Get Article Text
        article_text = []
        # Avoid Links of Videos and Adverts
        for i in driver.find_element(By.CLASS_NAME, "text-container").find_elements(By.TAG_NAME, 'p'):
            article_text.append(i.text)
        articles_lst.append(' '.join(article_text))
        # Update Counter
        counter += 1
    print('Detailed Pages Scraping Completed.')
    # Close Driver
    driver.quit()
    # Get scraped data into dataframe format
    articles = pd.DataFrame()
    articles['Link'] = list(article_links)
    articles['Text'] = articles_lst
    # Join Main Page and Articles Dataframes
    independent_full = pd.merge(independent, articles, on='Link')
    # Save Dataframe
    today_date = datetime.now().strftime('%Y%m%d')
    independent_full.to_csv(f'Scraped Data/independent_{today_date}.csv', index=False)
    return independent_full

# Function to Clean Scraped Data
def data_cleaning(independent_data):
    # Combine Main Text Features
    independent_data['Composite Text'] = independent_data['Title']+' '+independent_data['Summary']+' '+independent_data['Text']
    # Rename Category Column
    independent_data.rename(columns={'Category': 'News Category'}, inplace=True)
    # Drop Missing Values
    independent_data = independent_data.dropna(subset=['Composite Text','Date'])
    # Get Year and Month Columns
    independent_data['Date'] = pd.to_datetime(independent_data['Date'])
    independent_data['Year'] = independent_data['Date'].dt.year
    independent_data['Month'] = independent_data['Date'].dt.month
    # Get Clean Condensed Data File
    independent_data = independent_data[['Link', 'Date', 'Year', 'Month', 'News Category', 'Composite Text']]
    # Save Clean Condensed Data File for Main Page
    independent_data.to_csv('Cleaned Data/independent_articles_clean.csv', index=False)
    # Combine With Previous Data
    # Load Past Dataset
    independent_prev = pd.read_csv('Cleaned Data/independent_clean.csv')
    # Combine Old and New Datasets
    independent = pd.concat([independent_prev, independent_data])
    independent = independent.drop_duplicates(subset=['Link'])
    # Save Combined Dataset
    independent.to_csv('Cleaned Data/independent_clean.csv', index=False)
    print('Completed Data Cleaning.')
    return independent

# Function to Get EPU Data
def epu_data(independent_data):
    # Drop Unnecessary Categories from Dataset
    drop_cat = ['art', 'arts', 'debate', 'life', 'sports', 'world']
    for i in drop_cat:
        independent_data = independent_data[independent_data['News Category'] != i]
    # Lowercase and stopwords removal only
    independent_data['Composite Text_Clean'] = [tokenize(article, 0) for article in independent_data['Composite Text']]
    # Define Keywords lists 
    economic = ['Economic', 'Economics', 'Economy', 'Economies', 'Industry', 'Industries', 'Industrial', 'Business', 'Businesses', 'Commerce']
    political = ['Political', 'Politics', 'Central Bank', 'ECB', 'Policy', 'Policies', 'Tax', 'Taxation', 'Taxes', 'Spending', 'Regulation', 'Budget', 'Deficit', 'Debt', 'Castille', 'Parliament', 'Government', 'MP', 'Member of Parliament', 'Members of Parliament', 'MEP', 'Member of the European Parliament', 'Members of the European Parliament', 'Minister', 'Ministers', 'Ministry', 'Tariff', 'Tariffs', 'Exchange Rate', 'Exchange Rates', 'Currency', 'Crash', 'Crashes', 'Sovereign Debt', 'Fiscal', 'Monetary', 'Legislation', 'Legislations', 'Reform', 'Reforms', 'Rule', 'Rules', 'Norm', 'Norms', 'Normative', 'Regulation', 'Regulations', 'Law', 'Laws']
    uncertainty = ['Uncertain', 'Uncertainty', 'Uncertainties', 'Unstable', 'Instability', 'Instabilities']
    # Obtain EPU Flag
    independent_data['EPU'] = get_article_epu_flag(articles=independent_data['Composite Text_Clean'], economic_terms=economic, policy_terms=political, uncertainty_terms=uncertainty)
    # Drop Duplicates
    independent_data = independent_data.drop_duplicates(subset = ['Link'])
    # Drop Clean Text Variable
    independent_data = independent_data.drop(['Composite Text_Clean'], axis=1)
    # Save Articles Dataframe
    independent_data.to_csv('independent_working.csv', index=False)
    # Aggregate Data by Time
    independent_monthly = independent_data.groupby(['Year', 'Month']).agg(Articles=('Link', 'count'), EPU=('EPU', 'sum')).reset_index()
    # Save Articles Dataframe
    independent_monthly.to_csv('independent_monthly.csv', index=False)
    print('Data Prepared for Index Calculation.')
    return independent_data, independent_monthly