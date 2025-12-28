import os
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ---------------- CONFIG ---------------- #

COUNTRY_GEO_IDS = {
    'United Kingdom': '101165590',
    'Germany': '101282230',
    'France': '105015875',
    'Italy': '103350119',
    'Spain': '105646813',
    'Netherlands': '102890719',
    'Switzerland': '106693272',
    'Sweden': '105117694',
    'Poland': '105072130',
    'Belgium': '100565514',
    'Austria': '100456013',
    'Denmark': '104514075',
    'Finland': '100456013',
    'Norway': '103819153',
    'Ireland': '104738515',
    'Portugal': '100364837',
    'Czech Republic': '104508036',
    'Hungary': '100288700',
    'Romania': '106670623',
    'Greece': '104677530'
}

SEARCH_KEYWORDS = [
    "DevOps",
    "Platform Engineer",
    "Site Reliability"
]

MAX_SCROLLS = 3

# --------------------------------------- #

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(options=options)

def linkedin_login(driver):
    driver.get("https://www.linkedin.com/login")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "username"))
    )

    driver.find_element(By.ID, "username").send_keys(os.environ["LI_EMAIL"])
    driver.find_element(By.ID, "password").send_keys(os.environ["LI_PASSWORD"])
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    time.sleep(10)

def salesnav_company_search(driver, keyword, geo_id):
    url = (
        "https://www.linkedin.com/sales/search/company?"
        f"keywords={keyword}&geoIncluded={geo_id}&hiring=true"
    )
    driver.get(url)
    time.sleep(6)

    for _ in range(MAX_SCROLLS):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(3, 5))

def extract_companies(driver):
    companies = []
    cards = driver.find_elements(By.CSS_SELECTOR, "li.search-result")

    for card in cards:
        try:
            name = card.find_element(
                By.CSS_SELECTOR, "a[data-control-name='view_company']"
            ).text

            link = card.find_element(By.TAG_NAME, "a").get_attribute("href")

            companies.append({
                "Company": name,
                "Company URL": link
            })
        except:
            continue

    return companies

def extract_recruiters(driver, company_url):
    recruiters = []
    driver.get(company_url + "people/")
    time.sleep(5)

    profiles = driver.find_elements(By.CSS_SELECTOR, "li.org-people-profile-card")

    for p in profiles[:5]:
        try:
            name = p.find_element(By.CSS_SELECTOR, "a").text
            title = p.find_element(By.CSS_SELECTOR, "div.artdeco-entity-lockup__subtitle").text

            if any(x in title.lower() for x in ["recruit", "talent", "hr", "people"]):
                recruiters.append(f"{name} ({title})")
        except:
            continue

    return recruiters

def run_pipeline():
    driver = get_driver()
    linkedin_login(driver)

    results = []

    for country, geo_id in COUNTRY_GEO_IDS.items():
        for keyword in SEARCH_KEYWORDS:
            salesnav_company_search(driver, keyword, geo_id)
            companies = extract_companies(driver)

            for company in companies:
                try:
                    recruiters = extract_recruiters(driver, company["Company URL"])
                    results.append({
                        "Country": country,
                        "Keyword": keyword,
                        "Company": company["Company"],
                        "Company URL": company["Company URL"],
                        "Recruiters": "; ".join(recruiters) if recruiters else "Not Found"
                    })
                except:
                    continue

                time.sleep(random.uniform(4, 7))

    driver.quit()
    return results

if __name__ == "__main__":
    data = run_pipeline()
    df = pd.DataFrame(data)
    df.drop_duplicates(subset=["Company URL"], inplace=True)

    output = "salesnav_visa_hiring_companies.csv"
    df.to_csv(output, index=False)

    print(f"\n✅ Saved {len(df)} companies to {output}")
