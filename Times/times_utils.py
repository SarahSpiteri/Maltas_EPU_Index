## Times of Malta Routine Procedure Functions ##

# Imports
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains, ActionBuilder
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

# Function to scroll to element in realistic manner
def scroll_element_menu(elem_path, driver, finder=By.XPATH):
    # Find element
    element = driver.find_element(finder, elem_path)
    # Simulate shock to mouse movement caused by first touch to mouse
    action =  ActionChains(driver)
    x_shock = np.random.choice(range(1,12))
    y_shock = np.random.choice(range(1,12))
    action.move_by_offset(x_shock,y_shock)
    action.perform()
    # Mimic human scrolling behavior and put the element withIN 70 pixels off the center of viewbox
    window_height = driver.execute_script("return window.innerHeight")
    start_dom_top = driver.execute_script("return document.documentElement.scrollTop")
    element_location = element.location['y']
    desired_dom_top = element_location - window_height/2 #Center It!
    to_go = desired_dom_top - start_dom_top
    cur_dom_top = start_dom_top
    while np.abs(cur_dom_top - desired_dom_top) > 70:
        scroll = np.random.uniform(2,69) * np.sign(to_go)
        driver.execute_script("window.scrollBy(0, {})".format(scroll))
        cur_dom_top = driver.execute_script("return document.documentElement.scrollTop")
        time.sleep(np.abs(np.random.normal(0.0472, 0.003)))

# Function to Adjust Dates when Scraping the Website's Main Page
def parse_date(date_string):
    if 'ago' in date_string:  # Handle "ago" dates
        return datetime.now()
    else:
        try:
            return date_parser.parse(date_string)
        except ValueError:
            return datetime.now() # If parsing fails, return current date

# Function for Main Page Scraping
def scrape_article_links(driver, url, end_date_text, output_filename, category_name):
    with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Title', 'Link', 'Category'])
        driver.get(url)
        wait_time(3)
        try:
            driver.find_element(By.XPATH, '/html/body/div[3]/div[2]/div[2]/div[2]/div[2]/button[1]').click()
        except:
            pass
        end_date = datetime.strptime(end_date_text, '%B %d, %Y')
        while True:
            # Extract article details
            articles = driver.find_elements(By.CLASS_NAME, 'wi-WidgetSubCompType_12-info')
            for article in articles:
                title = article.find_element(By.TAG_NAME, 'h3').text
                link = article.find_element(By.TAG_NAME, 'a').get_attribute('href')
                date_element = article.find_element(By.CLASS_NAME, 'wi-WidgetMeta-time')
                date_text = date_element.text.strip()
                if date_text:
                    article_date = parse_date(date_text)
                    if isinstance(article_date, datetime) and article_date < end_date:
                        return
                writer.writerow([title, link, category_name])
            # Find and click on the next page link
            try:
                wait_time(3)
                scroll_element_menu('/html/body/div[2]/main/div/div[2]/nav/ul/li[2]/a', driver)
                driver.find_element(By.XPATH, '/html/body/div[2]/main/div/div[2]/nav/ul/li[2]/a').click()
            except TimeoutException:
                break #Next page button not found or timeout exceeded

# Function for Individual Articles Scraping
def scrape_article_details(driver, service_driver, options, links, categories):
    # Progress Counter
    pg = 1
    # Items Lists
    title = []
    date = []
    article_text = []
    categories_list = []
    links_list = []
    # Loop Over Article Links
    for i in range(len(links)):
        link = links[i]
        category = categories[i]
        # Open Times page
        try:
            driver.get(link)
        except:
            driver = webdriver.Chrome(service=service_driver, options=options)
            wait_time(3)
            driver.get(link)
        wait_time(1)
        # Get Page Contents
        content = driver.page_source
        soup = BeautifulSoup(content, features='html.parser')
        # Initial Data
        categories_list.append(category)
        links_list.append(link)
        # Extract data for each article
        try:
            # Title 
            tit = soup.find('h1', attrs={'class': 'wi-WidgetSubCompType_13-title'})
            if tit:
                title.append(tit.text)
            else:
                raise ValueError("Title not found")
            # Date
            dt = soup.find('span', attrs={'class': 'wi-WidgetMeta-time'})
            if dt:
                date.append(dt.text)
            else:
                raise ValueError("Date not found")
            # Text
            txt = soup.findAll('div', attrs={'class': 'ar-Article_Main'})
            article_text.append('')
            for p in txt:
                article_text[-1] += p.text
        except:
            # Skip deleted articles and append empty strings to lists
            title.append(np.nan)
            date.append(np.nan)
            article_text.append(np.nan)
        # List of all lists to check
        lists = [title, date, article_text, categories_list, links_list]
        first_length = len(lists[0])
        if not all(len(lst) == first_length for lst in lists):
            raise ValueError(f"Not all lists have the same length. Check the data - {len(title)}, {len(date)}, {len(article_text)}, {len(categories_list)}, {len(links_list)}.")
        # Update Counter
        pg += 1
    # Save data
    data = {'Category': categories_list, 'Title': title, 'Date': date, 'Article_Text': article_text, 'Link': links_list}
    data = pd.DataFrame(data)
    return data

# Function to Adjust Dates when Scraping Individual Articles
def extract_date(date):
    try:
        # Attempt to parse as a datetime object
        parsed_date = datetime.strptime(date, '%d %b %Y')
        return parsed_date.day, parsed_date.month, parsed_date.year
    except ValueError:
        # If it's not in the expected date format, return None
        return None, None, None
        
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
    # Define end date text
    end_date_text = datetime.today() - relativedelta(months=1)
    end_date_text = end_date_text.replace(day=1)
    end_date_text = end_date_text.strftime('%B %d, %Y')
    # Define categories, corresponding URLs 
    categories = {'National': 'https://timesofmalta.com/news/national', 
                  'Fact Check': 'https://timesofmalta.com/news/fact-check',
                  'Business': 'https://timesofmalta.com/news/business',
                  'Tech': 'https://timesofmalta.com/news/tech'}
    # Scrape links for each category
    for category, url in categories.items():
        output_filename = f"Scraped Data/{category.lower().replace(' ', '_')}_links.csv"
        scrape_article_links(driver, url, end_date_text, output_filename, category)
    print('Main Page Scraping Completed.                                                                                                            ')
    # Load links and categories from CSV files
    csv_files = ['national_links.csv', 'fact_check_links.csv', 'business_links.csv', 'tech_links.csv'] 
    all_links = []
    all_categories = []
    for csv_file in csv_files:
        df = pd.read_csv(f'Scraped Data/{csv_file}')
        all_links.extend(df['Link'])
        category = csv_file.split('_')[0].capitalize()
        all_categories.extend([category] * len(df))
    # Scrape article details
    times = scrape_article_details(driver, service_driver, options, all_links, all_categories)
    print('Detailed Pages Scraping Completed.                                                                                                            ')
    # Close Tabs
    driver.quit()
    # Remove "\n\n" before every text in the "Article_Text" column
    times['Article_Text'] = times['Article_Text'].str.replace('\n\n', '')
    # Remove everything from "Sign up to our free newsletters" onwards
    times['Article_Text'] = times['Article_Text'].str.split('Sign up to our free newsletters').str[0]
    # Apply the function to the "Date" column
    times['Date'] = times['Date'].astype(str)
    times['Day'], times['Month'], times['Year'] = zip(*times['Date'].apply(extract_date))
    # Save Dataframe
    today_date = datetime.now().strftime('%Y%m%d')
    times.to_csv(f'Scraped Data/times_of_malta_{today_date}.csv', index=False)
    return times

# Function to Clean Scraped Data
def data_cleaning(times_data):
    # Adjust Date Formats
    times_data = times_data.drop(['Day', 'Month', 'Year'], axis=1)
    times_data['Date'] = pd.to_datetime(times_data['Date'], format='%d %B %Y', errors='coerce')
    times_data['Date'] = times_data['Date'].dt.strftime('%Y-%m-%d')
    times_data.loc[times_data['Date'].isna(), 'Date'] = datetime.today().strftime('%Y-%m-%d')
    # Get Year and Month Variables
    times_data['Date'] = pd.to_datetime(times_data['Date'])
    times_data = times_data.sort_values(by='Date').reset_index(drop=True)
    times_data['Year'] = times_data['Date'].dt.year
    times_data['Month'] = times_data['Date'].dt.month
    # Combine Main Text Features
    times_data['Composite Text'] = times_data['Title']+' '+times_data['Article_Text']
    # Rename Category Column to Match
    times_data.rename(columns={'Category': 'News Category'}, inplace=True)
    # Get Clean Condensed Data File
    times_data = times_data[['Link', 'Date', 'Year', 'Month', 'News Category', 'Composite Text']]
    # Drop Nulls
    times_data.dropna(subset=['Composite Text'], inplace=True)
    # Save Clean Condensed Data File for Main Page
    times_data.to_csv('Cleaned Data/times_of_malta_articles_clean.csv', index=False)
    # Combine With Previous Data
    times_prev = pd.read_csv('Cleaned Data/times_clean.csv')
    times = pd.concat([times_prev, times_data])
    times['Date'] = times['Date'].astype(str).str.split().str[0]
    times = times.drop_duplicates(['Link'], keep='last')
    # Save Combined Dataset
    times.to_csv('Cleaned Data/times_clean.csv', index=False)
    print('Completed Data Cleaning.')
    return times

# Function to Get EPU Data
def epu_data(times_data):
    # Drop Unnecessary Categories 
    drop_cats = ['Community', 'Entertainment', 'Motoring', 'Opinion', 'Sport', 'World']
    for i in drop_cats:
        times_data = times_data[times_data['News Category'] != i]
    # Lowercase and stopwords removal only
    times_data.dropna(subset=['Composite Text'], inplace=True)
    times_data['Composite Text_Clean'] = [tokenize(article, 0) for article in times_data['Composite Text']]
    # Define Keywords lists - Additions from Different Papers by Sarah (Red terms in Keywords Excel)
    economic = ['Economic', 'Economics', 'Economy', 'Economies', 'Industry', 'Industries', 'Industrial', 'Business', 'Businesses', 'Commerce']
    political = ['Political', 'Politics', 'Central Bank', 'ECB', 'Policy', 'Policies', 'Tax', 'Taxation', 'Taxes', 'Spending', 'Regulation', 'Budget', 'Deficit', 'Debt', 'Castille', 'Parliament', 'Government', 'MP', 'Member of Parliament', 'Members of Parliament', 'MEP', 'Member of the European Parliament', 'Members of the European Parliament', 'Minister', 'Ministers', 'Ministry', 'Tariff', 'Tariffs', 'Exchange Rate', 'Exchange Rates', 'Currency', 'Crash', 'Crashes', 'Sovereign Debt', 'Fiscal', 'Monetary', 'Legislation', 'Legislations', 'Reform', 'Reforms', 'Rule', 'Rules', 'Norm', 'Norms', 'Normative', 'Regulation', 'Regulations', 'Law', 'Laws']
    uncertainty = ['Uncertain', 'Uncertainty', 'Uncertainties', 'Unstable', 'Instability', 'Instabilities']
    # Get Dummy for EPU Articles
    times_data['EPU'] = get_article_epu_flag(articles=times_data['Composite Text_Clean'], economic_terms=economic, policy_terms=political, uncertainty_terms=uncertainty)
    # Order Dataframe by Date
    times_data['Date'] = pd.to_datetime(times_data['Date'], errors='coerce')
    times_data.dropna(subset=['Date'], inplace=True)
    times_data = times_data.sort_values(by='Date')
    # Drop Clean Text Variable
    times_data = times_data.drop(['Composite Text_Clean'], axis=1)
    # Save Articles Dataframe
    times_data.to_csv('times_working_test.csv', index=False)
    # Aggregate Data by Time
    times_monthly = times_data.groupby(['Year', 'Month']).agg(Articles=('Link', 'count'), EPU=('EPU', 'sum')).reset_index()
    # Save Articles Dataframe
    times_monthly.to_csv('times_monthly.csv', index=False)
    print('Data Prepared for Index Calculation.')
    return times_data, times_monthly