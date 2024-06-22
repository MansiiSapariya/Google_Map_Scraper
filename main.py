from playwright.sync_api import sync_playwright, Playwright
from dataclasses import dataclass
import pandas as pd
from playwright.async_api import Locator
import re
import time
import argparse
import os

@dataclass
class Business:
    """holds business data"""
    name: str = '-'
    address: str = '-'
    website: str = '-'
    phone_number: str = '-'
    reviews_count: int = '-'
    ratings: float = '-'
    industry:str = '-'
    google_link:str='-'
    latitude: float = '-'
    longitude: float = '-'
    
    
    def __repr__(self) -> str:
        return f"\nCompany:{self.name}\nStars:{self.ratings}\nWebsite:{self.website}\nIndustry:{self.industry}\nPhone:{self.phone_number}\nGoogle Link:{self.google_link}"

@dataclass
class ElementAttributes:
    COMPANY_TILE = 'hfpxzc'
    FOCUS_REGION='hfpxzc'
    LIST_END='HlvSq' # The element we encounter when no-more data can be loaded.
    COMPANY_NAME = '.DUwDvf.lfPIob'
    COMPANY_WEBSITE = '.rogA2c.ITvuef'
    COMPANY_RATINGS = '.ceNzKf'
    COMPANY_INDUSTRY = '.DkEaL'
    COMPANY_DETAILS = '.Io6YTe.fontBodyMedium.kR99db'
    

def scrape_google_links(query:str):
    businesses:list[Business] = []
    
    with sync_playwright() as p:
        try:
            # DECLARATION
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            
            # INITIATE - SEARCH AND LOCATE SCRAPING REGION
            page.goto(query)
            page.locator(f'.{ElementAttributes.FOCUS_REGION}').first.focus()
            
            

            # SCROLL THE LIST TO LOAD EACH ELEMENT
            for _ in range(100):
                page.keyboard.press("End")
                print(f"\n{'-'*10}Scrolling{'-'*10}\n")
                if(page.locator(f'.{ElementAttributes.LIST_END}').is_visible()):
                    break
                time.sleep(1)
            
            # FETCHING ALL THE COMPANY TILE/BUSINESS PROFILE ELEMENTS.
            _companies = page.locator(f'.{ElementAttributes.COMPANY_TILE}').all()
            companies:list[Locator] = _companies
            total = (len(_companies))
            i=1
            
            
            # EXTRACT GOOGLE PAGE LINK FROM EACH OF THE RESULTS.
            for company in companies:
                
                biz = Business()
                biz.google_link = company.get_attribute('href')
                businesses.append(biz)

                print(f"\n{'-'*10}\n{i}/{total}\n{biz}\n{'-'*10}\n")
               
                i+=1

                
            print("out of loop now")
            browser.close()
                
            # SAVE THE RESULT IN A CSV
            df = make_dataframe_for_links(businesses)

            return df
        
        except Exception as e:
            print(f"{'-'*10}x{'-'*10}")
            print(f"Some shit timed out.")
            print(e)
            print(f"{'-'*10}x{'-'*10}")


def scrape_google_page(page_link) -> dict:
    with sync_playwright() as p:
       try:
            # DECLARATION
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # INITIATE - SEARCH AND LOCATE SCRAPING REGION
            page.goto(page_link)
            biz = Business()
            
            # SCRAPING DIFFERENT DATA POINTS
            name = page.locator(ElementAttributes.COMPANY_NAME).text_content()
            biz.name = name
            
            
            website = page.locator(ElementAttributes.COMPANY_WEBSITE).text_content(timeout=2500)
            biz.website = website
            
            
            ratings = page.locator(ElementAttributes.COMPANY_RATINGS).get_attribute('aria-label')
            biz.ratings = ratings
            
            
            industry = page.locator(ElementAttributes.COMPANY_INDUSTRY).first.text_content()
            biz.industry = industry
            
            #SCRAPES ALL THE COMPANY DETAILS AND FILTERS THE PHONE NUMBER USING REGEX
            detail_elements = page.locator(ElementAttributes.COMPANY_DETAILS).all()
            pattern = re.compile(r"(\+\d{1,3})?\s?\(?\d{1,4}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
            for detail in detail_elements:
                phone_number = detail.all_text_contents()
                if(len(phone_number[0])>20):
                    continue
                else:
                    match = re.search(pattern, phone_number[0])
                    if(match):
                        biz.phone_number =  phone_number[0]
                        break
            
            biz.google_link = page_link
            
            print(f"\n{'-'*10}\n{biz}\n{'-'*10}\n")
            
            df = make_dataframe_for_pages(biz)
            
            return df
       except Exception as e:
            print(f"{'-'*10}x{'-'*10}")
            print(f"Some shit timed out.")
            print(e)
            print(f"{'-'*10}x{'-'*10}")
            
# MAKING A DATAFRAME FOR INFORMATION FROM BUSINESS PAGES
def make_dataframe_for_links(bizlist:list[Business]):
    data = {
            "google_link":[],
            }
    for biz in bizlist:
        data['google_link'].append(biz.google_link)

    return data


# MAKING A DATAFRAME FOR INFORMATION TAKEN FROM BUSINESS PAGES
def make_dataframe_for_pages(biz:Business) -> dict:
    data = {"company_name":[],
            "company_website":[],
            "ratings":[],
            "industry":[],
            "phone":[],
            "google_link":[]}

    data['company_name'].append(biz.name) 
    data['company_website'].append(biz.website) 
    data['ratings'].append(biz.ratings) 
    data['industry'].append(biz.industry)
    data['phone'].append(biz.phone_number)
    data['google_link'].append(biz.google_link)

    return data

# CREATE GOOGLE MAP URLS FROM THE LIST OF STATES IN USA
def create_urls(keyword:str,):
    slug = keyword.replace(" ", "+")
    locations = []
    queries = []
    locations = open('maps.txt','r').read().splitlines()
    for loc in locations:
        query = f"https://www.google.com/maps/search/{slug}+near+{loc.replace(' ', '+')}"
        queries.append(query)
    return queries
        

# SCRAPE URLS OF BUSINESS PAGES AND STORE IT IN 'data/links/{filename}.csv'
def scrape_business_urls(keyword:str):
    urls = create_urls(keyword)
    
    for url in urls:
        result_df = scrape_google_links(url)
        
        if(result_df):
            df=pd.DataFrame(result_df)
            file_name = f'data/links/{keyword}.csv'
            if(os.path.isfile(file_name)):
                df.to_csv(file_name, index=False, header=False, mode='a')
            else:
                df.to_csv(file_name, index=False, header=True, mode='x')


# SCRAPE DATA USING THE BUSINESS PAGE LINKS IN 'data/links/{filename}.csv'
# AND STORE IT IN 'data/{filename}.csv'
def scrape_business_pages(urls_csv, keyword):
    df = pd.read_csv(urls_csv)
    links = df['google_link']

    for page_link in links.tolist():
        result_df:dict = scrape_google_page(page_link)
        
        if(result_df != None):
            if(len(result_df) > 0):
                df = pd.DataFrame(result_df, index=None)
                file_name = f'data/{keyword}.csv'
                if(os.path.isfile(file_name)):
                    df.to_csv(file_name, index=False, header=False, mode='a')
                else:
                    df.to_csv(file_name, index=False, header=True, mode='x')

def clean_data(filename:str):
    df = pd.read_csv(filename)
    df.drop_duplicates(subset=['company_name'], keep='first')
    
    df.to_csv('cleaned.csv')
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--keyword', type=str, help='Give Keyword', required=True)
    parser.add_argument('-l', action='store_true', help='Get links')
    parser.add_argument('-r', action='store_true', help='Get records')
    
    args = parser.parse_args()
    
    keyword = args.keyword
    
    if(args.r):
        scrape_business_pages(f"data/links/{keyword}.csv", keyword)
    
    if(args.l):
        scrape_business_urls(keyword)