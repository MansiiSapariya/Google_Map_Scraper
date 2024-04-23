from playwright.sync_api import sync_playwright
from dataclasses import dataclass
import pandas as pd
import time
import re
import playwright.sync_api as sn


@dataclass
class Business:
    """holds business data"""
    name: str = None
    address: str = None
    website: str = None
    phone_number: str = None
    reviews_count: int = None
    ratings: float = None
    industry:str = None
    latitude: float = None
    longitude: float = None
    
    
    def __repr__(self) -> str:
        return f"\nCompany:{self.name}\nStars:{self.ratings}\nWebsite:{self.website}\nIndustry:{self.industry}"

@dataclass
class ElementAttributes:
    COMPANY_TILE_1='Nv2PK.tH5CWc.THOPZb'
    COMPANY_TILE_2='Nv2PK.Q2HXcd.THOPZb'
    COMPANY_NAME='NrDZNb'
    RATINGS='MW4etd'  # Stars
    NUMBER_OF_REVIEWS='UY7F9'
    INDUSTRY='W4Efsd' # Take the first Span child.
    WEBSITE='lcr4fd.S9kvJb' # Add condition `if text == 'Website'`
    RESULTS_TEXT='L1xEbb' # We have to click on it to focus the list.
    MOUSE_CLICK_REGION='k7jAl.miFGmb.lJ3Kh.w6Uhzf'
    LIST_END='HlvSq' # The element we encounter when no-more data can be loaded.
    FEED_AREA='m6QErb DxyBCb kA9KIf dS8AEf ecceSd QjC7t' #Take the second div (child)


def scrape(query:str, latlong:str='44.5000236,-89.5309026', state:str=''):
    with sync_playwright() as p:
        # DECLARATION
        businesses:list[Business] = []
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        _query = make_search_string(query)
        
        # INITIATE - SEARCH AND LOCATE SCRAPING REGION
        page.goto(f"https://www.google.com/maps/search/{_query}/@{latlong},10z")
        page.locator(f'.{ElementAttributes.MOUSE_CLICK_REGION}').first.click()
        
        # SCROLL THE LIST TO LOAD EACH ELEMENT
        for _ in range(1000):
            page.keyboard.press("End")
            if(page.locator(f'.{ElementAttributes.LIST_END}').is_visible()):
                break
            time.sleep(2)

        # FETCH EACH ELEMENT BASED ON THEIR CLASSES
        companies_1 = page.locator(f'.{ElementAttributes.COMPANY_TILE_1}').all()
        companies_2 = page.locator(f'.{ElementAttributes.COMPANY_TILE_2}').all()
        companies:list[sn.Locator] = companies_1 + companies_2
        
        print("\n ---------------- \n")

        # EXTRACT 'name, rating, website, industry' FOR EACH OF THE COMPANY ELEMENT IN THE LIST.
        for company in companies:
            biz:Business = Business()
            biz.name = find_element(company, ElementAttributes.COMPANY_NAME).all_inner_texts()[0] if find_element(company, ElementAttributes.COMPANY_NAME)  else ''
            biz.ratings = find_element(company, ElementAttributes.RATINGS).all_text_contents()[0] if len(find_element(company, ElementAttributes.RATINGS).all_text_contents())>0 else '0.0'
            biz.website = get_website(company) if get_website(company)  else ''
            biz.industry = get_industry(company)
            print(biz)
            businesses.append(biz)
        
        # SAVE THE RESULT IN A CSV
        make_dataframe(businesses, f'{query}', state)

        print("\n ---------------- \n")


# HELPERS 
def make_search_string(query:str):
    '''
    Formats a string into a search query:
    Example - 'Real Estate' -> Real+Estate
    
    Returns -> str
    '''
    split_list = query.split(" ")
    return str.join("+", split_list)

def get_website(el_locator:sn.Locator):
    try:
        el = find_element(el_locator, ElementAttributes.WEBSITE)
        if(el):
            link = el.get_attribute('href')
            return link
    except:
        return None


def find_element(el_locator:sn.Locator, element:ElementAttributes) -> sn.Locator:
    try:    
        el = el_locator.locator(f'.{element}')
        return el   
    except:
        return None


def get_industry(el_locator:sn.Locator) -> sn.Locator:
    el = find_element(el_locator, ElementAttributes.INDUSTRY)
    if(not el):
        return
    raw_industry_text = el.nth(2).all_inner_texts()[0]
    pattern:re.Pattern = re.compile(r'^[^·]*')
    return pattern.match(raw_industry_text).group(0)

def make_dataframe(bizlist:list[Business], search:str, state:str):
    data = {"company_name":[],
            "company_website":[],
            "ratings":[],
            "industry":[],
            'state':[]
            }
    for biz in bizlist:
        data['company_name'].append(biz.name) 
        data['company_website'].append(biz.website) 
        data['ratings'].append(biz.ratings) 
        data['industry'].append(biz.industry)
    
    data['state']= [state]*len(data['company_name'])
    df = pd.DataFrame(data)
    df.to_csv(f'daniel/{search}.csv', index=False, mode='a')
    
        
if __name__ == "__main__":
    search_query = "Real Estate"
    df = pd.read_csv('latlong.csv')
    for _, row in df.iterrows():
        scrape(search_query,f'{row["Lat"]},{row["Long"]}',row["State"])