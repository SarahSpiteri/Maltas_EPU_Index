## Malta Today Routine Procedure Functions ##

# Imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
import numpy as np
import pandas as pd
import math
import re
import nltk
from nltk.stem import SnowballStemmer   
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords
from datetime import datetime
import datetime as dt
from selenium.common.exceptions import NoSuchElementException
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
    # urls of key website areas
    urls = ['https://www.maltatoday.com.mt/news','https://www.maltatoday.com.mt/business']
    # Load Previously Scraped Data
    malta_today_prev = pd.read_csv("Scraped Data/malta_today_main.csv")
    links_prev = malta_today_prev['Link'].tolist()
    # Main Page Scraper
    links = []
    titles = []
    summaries = []
    # Loop Over Section Links
    counter = 1
    for url in urls:
        pg = 1
        # Loop Over Section Pages
        while True:
            # Store List of Links in Section
            cat_links = []
            # Open Malta Today Page
            if pg == 1:
                driver.get(url) 
                wait_time(7)
            # Do Not Consent to Personal Data Use
            try:
                driver.find_element(By.XPATH,'/html/body/div[3]/div[2]/div[2]/div[2]/div[2]/button[2]').click()
                wait_time(3)
            except NoSuchElementException:
                pass
            # Get Article Information
            page_details = driver.find_elements(By.CLASS_NAME,"details ")
            if len(page_details) == 0:
                break
            else:
                for article in page_details:
                    # Titles
                    titles.append(article.find_element(By.TAG_NAME,"h3").text.replace('\n',''))
                    # Summaries
                    try:
                        summaries.append(article.find_element(By.CLASS_NAME,"long-standfirst").text.replace('\n',''))
                    except NoSuchElementException:
                        summaries.append(np.nan)
                    # Links
                    links.append(article.find_element(By.TAG_NAME,'a').get_attribute('href'))
                    cat_links.append(article.find_element(By.TAG_NAME,'a').get_attribute('href'))  
            # Check For Overlaps with Previously Scraped Data
            if len(set(links_prev).intersection(set(cat_links))) > 0:
                break 
            # Move to the Next Page
            pg += 1
            driver.get(url + '/' + str(pg) + '/')
            wait_time(5)
        # Update Section Counter
        counter += 1
    print('Main Page Scraping Completed.')
    # Get scraped data into dataframe format
    malta_today = pd.DataFrame()
    malta_today['Link'] = links
    malta_today['Title'] = titles
    malta_today['Summary'] = summaries
    malta_today = malta_today.drop_duplicates(subset='Link')
    # Save Main Page Dataframe
    malta_today.to_csv('Scraped Data/malta_today_main.csv', index=False)
    # Get List of Unique Article Links
    article_links = malta_today['Link'].tolist()
    # Detailed Pages Scraper
    sub_title = []
    date = []
    article_text = []
    # Loop Over Links
    counter = 1
    for link in article_links:
        # Open Article Links
        driver.get(link)
        # Wait for Page to Load
        wait_time(5)
        # Get Subtitle
        try:
            sub_title.append(driver.find_element(By.CLASS_NAME,'article-heading').find_element(By.TAG_NAME,'h2').text)
        except NoSuchElementException:
            sub_title.append(np.nan)
        # Get Date
        try:
            date.append(driver.find_element(By.CLASS_NAME,'date-text').find_element(By.CLASS_NAME,'date').text.split(',')[0])
        except NoSuchElementException:
            date.append(np.nan)
        # Get Text
        try:
            texts = []
            for i in driver.find_elements(By.CLASS_NAME, 'full-article'):
                texts.append(i.text)
            texts = " ".join(texts)
            article_text.append(texts.replace('\n\n', ' ').replace('\n', ' '))
        except NoSuchElementException:
            article_text.append(np.nan)
        # Update Counter
        counter += 1
    print('Detailed Pages Scraping Completed.')
    # Close Driver
    driver.quit()
    # Get scraped data into dataframe format
    articles = pd.DataFrame()
    articles['Link'] = article_links
    articles['Sub-Title'] = sub_title
    articles['Date'] = date
    articles['Text'] = article_text
    # Join Main Page and Articles Dataframes
    malta_today_full = pd.merge(malta_today, articles, on='Link')
    # Save Dataframe
    today_date = datetime.now().strftime('%Y%m%d')
    malta_today_full.to_csv(f'Scraped Data/malta_today_{today_date}.csv', index=False)
    return malta_today_full

# Function to Clean Scraped Data
def data_cleaning(malta_today_data):
    # Combine Main Text Features
    malta_today_data['Composite Text'] = malta_today_data['Title']+' '+malta_today_data['Sub-Title']+' '+malta_today_data['Text']
    # Adjust Dates
    malta_today_data['Date'] = malta_today_data['Date'].astype(str)
    for i in range(malta_today_data.shape[0]):
        if len(malta_today_data.loc[i, 'Date']) > 19:
            malta_today_data.loc[i, 'Date'] = malta_today_data.loc[i, 'Date'].replace('Last updated on ', '')
            if '\n' in malta_today_data.loc[i, 'Date']:
                malta_today_data.loc[i, 'Date'] = malta_today_data.loc[i, 'Date'].split('\n')[1]
    # Drop Rows that do Not Contain Dates
    malta_today_data['Contains_Dates'] = malta_today_data['Date'].apply(lambda x: bool(re.search(r'\d', str(x))))
    malta_today_data = malta_today_data[malta_today_data['Contains_Dates']]
    malta_today_data.drop(columns=['Contains_Dates'], inplace=True)
    # Format Dates
    malta_today_data['Date'] = pd.to_datetime(malta_today_data['Date'], infer_datetime_format=True)
    malta_today_data = malta_today_data[malta_today_data.Date.astype(str).str.len() == 10]
    # Get Year and Month Variables
    malta_today_data['Year'] = malta_today_data['Date'].dt.year
    malta_today_data['Month'] = malta_today_data['Date'].dt.month
    # Order Observations by Time
    malta_today_data = malta_today_data.sort_values(by='Date') 
    # Get News Category Feature
    categories = []
    links = malta_today_data['Link'].tolist()
    for link in links:
        try:
            category = re.search(r'https://www.maltatoday.com.mt/news/(.*)/', link).group(1)
        except:
            category = re.search(r'https://www.maltatoday.com.mt/business/(.*)/', link).group(1)
        categories.append(category)
    malta_today_data['News Category'] = categories
    malta_today_data['News Category'] = malta_today_data['News Category'].str.replace(r'[0-9/]', '', regex=True)
    # Get Clean Condensed Data File
    malta_today_data = malta_today_data[['Link', 'Date', 'Year', 'Month', 'News Category', 'Composite Text']]
    # Save Clean Condensed Data File for Main Page
    malta_today_data.to_csv('Cleaned Data/malta_today_articles_clean.csv', index=False)
    # Combine With Previous Data
    malta_today_prev = pd.read_csv('Cleaned Data/malta_today_clean.csv')
    malta_today = pd.concat([malta_today_prev, malta_today_data])
    # Save Combined Dataset
    malta_today.to_csv('Cleaned Data/malta_today_clean.csv', index=False)
    print('Completed Data Cleaning.')
    return malta_today

# Function to Get EPU Data
def epu_data(malta_today_data):
    # Drop NAs
    malta_today_data = malta_today_data.dropna(subset=['Date','Year','Month','Composite Text'])
    # Drop Insignificant Categories 
    for  i in ['opinion', 'interview', 'arts', 'editorial', 'sports', 'europe', 'blogs', 'gourmet', 'world', 'xtra', 'lifestyle', 'business_comment', 'letters', 'christmas', 'skinny', 'announcements', 'blog', 'cartoons', 'offer', 'architecture-and-design']:
        malta_today_data = malta_today_data[malta_today_data['News Category'] != i]
    # Lowercase and stopwords removal only
    malta_today_data['Composite Text_Clean'] = [tokenize(article, 0) for article in malta_today_data['Composite Text']]
    # Define Keywords lists 
    economic = ['Economic','Economics','Economy','Economies','Industry','Industries','Industrial','Business','Businesses','Commerce']
    political = ['Political','Politics','Central Bank','ECB','Policy','Policies','Tax','Taxation','Taxes','Spending','Regulation','Budget','Deficit','Debt',
                 'Castille','Parliament','Government','MP','Member of Parliament','Members of Parliament','MEP','Member of the European Parliament',
                 'Members of the European Parliament','Minister','Ministers','Ministry','Tariff','Tariffs','Exchange Rate','Exchange Rates','Currency',
                 'Crash','Crashes','Sovereign Debt','Fiscal','Monetary','Legislation','Legislations','Reform','Reforms','Rule','Rules','Norm','Norms',
                 'Normative','Regulation','Regulations','Law','Laws']
    uncertainty = ['Uncertain','Uncertainty','Uncertainties','Unstable','Instability','Instabilities']
    # Obtain EPU Flag
    malta_today_data['EPU']=get_article_epu_flag(articles=malta_today_data['Composite Text_Clean'], economic_terms=economic, policy_terms=political, uncertainty_terms=uncertainty)
    # Drop Duplicates
    malta_today_data = malta_today_data.drop_duplicates(subset = ['Link'])
    # Drop Clean Text Variable
    malta_today_data = malta_today_data.drop(['Composite Text_Clean'], axis=1)
    # Save Articles Dataframe
    malta_today_data.to_csv('malta_today_working.csv', index=False)
    # Aggregate Data by Time
    mt_monthly = malta_today_data.groupby(['Year', 'Month']).agg(Articles=('Link', 'count'), EPU=('EPU', 'sum')).reset_index()
    # Save Articles Dataframe
    mt_monthly.to_csv('malta_today_monthly.csv', index=False)
    print('Data Prepared for Index Calculation.')
    return malta_today_data, mt_monthly