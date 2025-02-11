## TVM Routine Procedure Functions ##

# Imports
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import datetime as dt
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
import re
import time
import math
import csv
import nltk
from nltk.stem import SnowballStemmer   
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords
import warnings
warnings.filterwarnings('ignore')

# Funtion for Random Waiting Time
def wait_time(init_sec = 0):
    time.sleep(init_sec + np.random.choice([x/10 for x in range(7,22)]))

# Function to Move to and Click Elements in realistic manner
def move_and_click_element(elem_path, driver, finder=By.XPATH):
    # Set chain of actions
    action =  ActionChains(driver)
    # Find element
    startElement = driver.find_element(finder, elem_path)
    # Simulate shock to mouse movement caused by first touch to mouse
    x_shock = np.random.choice(range(1,12))
    y_shock = np.random.choice(range(1,12))
    action.move_by_offset(x_shock,y_shock)
    # Move to element
    action.pause(np.random.choice([x/10 for x in range(17,32)]))
    action.move_to_element(startElement)
    # Click element
    action.pause(np.random.choice([x/10 for x in range(7,22)]))
    action.click()
    # Execute actions chain
    action.perform()

# Define Primary Functions for Main Page Scraping
def scrape_category(category, base_url, stop_date, driver):
    page_number = 1
    all_data = []
    while True:
        url = base_url + str(page_number)  # Create URL with page number
        print(url, end="\r")  # Display Progress
        # Open Times page
        try:
            driver.get(url)
        except TimeoutException:
            driver.quit()
            driver = webdriver.Chrome(service=service_driver, options=options)
            driver.get(url)
        wait_time(1)
        try:
            move_and_click_element('/html/body/div[3]/div[1]/div/span/a[2]', driver)
            wait_time(1)
        except:
            pass
        # Get Page Contents
        content = driver.page_source
        soup = BeautifulSoup(content, features='html.parser')
        # Get Article Details
        articles = soup.find_all('article')
        if not articles:
            break
        # Extract Information from Articles
        stop_scraping = False
        for article in articles:
            # Date
            date_str = article.find('time', {'class': 'entry-date published'})['datetime']
            article_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
            # Stop if the article date is older than the stop date
            if article_date < stop_date:
                stop_scraping = True
                break
            # Link
            link = article.find('a')['href']
            # Title
            title = article.find('a').get('title', 'MISSING')
            # Append data to all_data list
            all_data.append([title, link, category])
        # Stop Scraping when reaching end date
        if stop_scraping:
            break
        # Update counter
        page_number += 1
    return all_data
        
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

# Function to Scrape Articles from Times of Malta Main Page
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
    # List of base URLs for different categories
    categories = {'local': 'https://tvmnews.mt/en/ahbarijiet_category/local/page/'}
    # Specify the stop date
    stop_date = datetime.today() - relativedelta(months=1)
    stop_date = stop_date.replace(day=1)
    stop_date = stop_date.strftime('%Y-%m-%d')
    stop_date = datetime.strptime(stop_date, '%Y-%m-%d')
    # Write all data to a single CSV file
    with open('Scraped Data/tvm_links.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(['Title', 'Link', 'Category'])
        # Scrape each category
        for category, base_url in categories.items():
            all_data = scrape_category(category, base_url, stop_date, driver)
            # Write data
            writer.writerows(all_data)
    print('Main Page Scraping Completed.                                                                                                       ')
    # Individual Pages Scraper
    # Load the existing links CSV if required
    tvm_links_df = pd.read_csv('Scraped Data/tvm_links.csv')
    # Initialize lists to store scraped data
    categories = []
    titles = []
    links = []
    dates = []
    article_texts = []
    # Progress Counter
    pg = 0
    # Loop Over Article Links
    for index, row in tvm_links_df.iterrows():
        link = row['Link']
        title = row['Title']
        category = row['Category']
        # Open TVM page
        try:
            driver.get(link)
        except Exception as e:
            continue
        wait_time(1)
        # Display Progress
        pg += 1
        # Get Page Contents
        content = driver.page_source
        soup = BeautifulSoup(content, features='html.parser')
        # Extract data for each article
        try:
            # Date
            dt = soup.find('time', attrs={'class': 'entry-date'})
            if dt:
                date = dt['datetime']
            else:
                raise ValueError("Date not found")
            # Text
            text = ""
            for p in soup.find('div', attrs={'class': 'entry-content'}).find_all('p'):
                text += p.text
            # Append data to lists
            categories.append(category)
            titles.append(title)
            links.append(link)
            dates.append(date)
            article_texts.append(text)
        except Exception as e:
            # Skip deleted articles and append empty strings to lists
            categories.append(category)
            titles.append(title)
            links.append(link)
            dates.append(np.nan)
            article_texts.append(np.nan)
    # Save the final batch of data
    data = {'Category': categories, 'Title': titles, 'Link': links, 'Date': dates, 'Article_Text': article_texts}
    tvm = pd.DataFrame(data)
    tvm.to_csv('tvm_articles.csv', index=False)
    print('Detailed Pages Scraping Completed.                                                                                                       ')
    # Close driver
    driver.quit()
    # Drop Duplicate Links
    tvm = tvm.drop_duplicates(subset=['Link'])
    # Extract date part before "T"
    tvm['Date'] = tvm['Date'].str.split('T').str[0]
    # Convert the 'Date' column to datetime format
    tvm['Date'] = pd.to_datetime(tvm['Date'], format='%Y-%m-%d', errors='coerce')
    # Extract day, month, and year into separate columns
    tvm['Day'] = tvm['Date'].dt.day
    tvm['Month'] = tvm['Date'].dt.month
    tvm['Year'] = tvm['Date'].dt.year
    # Drop rows with NaT values in the 'Article_Text' column
    tvm = tvm.dropna(subset=['Article_Text'])
    # Remove "Aqra bil-Malti" from each entry in the "Article_Text" column
    tvm['Article_Text'] = tvm['Article_Text'].str.replace('Aqra bil-\nMalti', '', regex=False)
    # Save Dataframe
    today_date = datetime.now().strftime('%Y%m%d')
    tvm.to_csv(f'Scraped Data/tvm_{today_date}.csv', index=False)
    return tvm

# Function to Clean Scraped Data
def data_cleaning(tvm_data):
    # Combine Main Text Features
    tvm_data['Composite Text'] = tvm_data['Title'] + ' ' + tvm_data['Article_Text']
    # Drop Nans in Article_Text
    tvm_data.dropna(subset=['Date', 'Composite Text'], inplace=True)
    # Order Observations by Time
    tvm_data = tvm_data.sort_values(by='Date').reset_index(drop=True)
    # Change Categories to Match Previous Data
    tvm_data.rename(columns={'Category': 'News Category'}, inplace=True)
    tvm_data['News Category'] = np.where(tvm_data['News Category'] == 'local', 'National', tvm_data['News Category'])
    # Get Clean Condensed Data File
    tvm_data = tvm_data[['Link', 'Date', 'Year', 'Month', 'News Category', 'Composite Text']]
    # Save Clean Condensed Data File for Main Page
    tvm_data.to_csv('Cleaned Data/tvm_articles_clean.csv', index=False)
    # Combine With Previous Data
    tvm_prev = pd.read_csv('Cleaned Data/tvm_clean.csv')
    tvm_prev['Date'] = tvm_prev['Date'].astype(str).str.split().str[0]
    tvm = pd.concat([tvm_prev, tvm_data])
    tvm = tvm.drop_duplicates(['Link'], keep='last')
    tvm['Date'] = pd.to_datetime(tvm['Date'], dayfirst=True)
    tvm = tvm.sort_values(by='Date').reset_index(drop=True)
    tvm.dropna(inplace=True)
    # Save Combined Dataset
    tvm.to_csv('Cleaned Data/tvm_clean.csv', index=False)
    print('Completed Data Cleaning.')
    return tvm

# Function to Get EPU Data
def epu_data(tvm_data):
    # Drop Unnecessary Categories 
    tvm_data = tvm_data[tvm_data['News Category'] == 'National']
    # Data Cleaning
    tvm_data['Composite Text'] = tvm_data['Composite Text'].astype(str)
    tvm_data = tvm_data[tvm_data['Composite Text'] != '.']
    tvm_data['Composite Text'] = tvm_data['Composite Text'].str.replace('\n', " ")
    tvm_data = tvm_data[tvm_data['Year'] >= 2015]
    # Lowercase and stopwords removal only
    tvm_data['Composite Text_Clean'] = [tokenize(article, 0) for article in tvm_data['Composite Text']]
    # Define Keywords lists 
    economic = ['Economic', 'Economics', 'Economy', 'Economies', 'Industry', 'Industries', 'Industrial', 'Business', 'Businesses', 'Commerce']
    political = ['Political', 'Politics', 'Central Bank', 'ECB', 'Policy', 'Policies', 'Tax', 'Taxation', 'Taxes', 'Spending', 'Regulation', 'Budget', 'Deficit', 'Debt', 'Castille', 'Parliament', 'Government', 'MP', 'Member of Parliament', 'Members of Parliament', 'MEP', 'Member of the European Parliament', 'Members of the European Parliament', 'Minister', 'Ministers', 'Ministry', 'Tariff', 'Tariffs', 'Exchange Rate', 'Exchange Rates', 'Currency', 'Crash', 'Crashes', 'Sovereign Debt', 'Fiscal', 'Monetary', 'Legislation', 'Legislations', 'Reform', 'Reforms', 'Rule', 'Rules', 'Norm', 'Norms', 'Normative', 'Regulation', 'Regulations', 'Law', 'Laws']
    uncertainty = ['Uncertain', 'Uncertainty', 'Uncertainties', 'Unstable', 'Instability', 'Instabilities']
    # Get Dummy for Expanded EPU Articles
    tvm_data['EPU'] = get_article_epu_flag(articles=tvm_data['Composite Text_Clean'], economic_terms=economic, policy_terms=political, uncertainty_terms=uncertainty)
    # Order Dataframe by Date
    tvm_data = tvm_data.sort_values(by='Date')
    # Drop Clean Text Variable
    tvm_data = tvm_data.drop(['Composite Text_Clean'], axis=1).reset_index(drop=True)
    # Save Articles Dataframe
    tvm_data.to_csv('tvm_working.csv', index=False)
    # Aggregate Data by Time
    tvm_monthly = tvm_data.groupby(['Year', 'Month']).agg(Articles=('Link', 'count'), EPU=('EPU', 'sum')).reset_index()
    # Save Articles Dataframe
    tvm_monthly.to_csv('tvm_monthly.csv', index=False)
    print('Data Prepared for Index Calculation.')
    return tvm_data, tvm_monthly