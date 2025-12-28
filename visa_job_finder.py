import requests
import logging
import pandas as pd
import time
from bs4 import BeautifulSoup
from urllib.parse import quote

# ---------------- LOGGING ---------------- #

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger("visa-job-finder")

# ---------------- CONFIG ---------------- #

ROLES = [
    "DevOps Engineer",
    "Platform Engineer",
    "Site Reliability Engineer"
]

COUNTRIES = [
    "Germany",
    "Netherlands",
    "Poland",
    "Ireland",
    "Sweden"
]

VISA_KEYWORDS = [
    "visa sponsorship",
    "work visa",
    "work permit provided",
    "relocation package",
    "relocation assistance",
    "international candidates",
    "open to international applicants",
    "eu blue card"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

DELAY = 2  # seconds between requests

# --------------------------------------- #

def contains_visa_keywords(text):
    text = text.lower()
    return any(k in text for k in VISA_KEYWORDS)

# -------- LINKEDIN JOBS (NO LOGIN) ------- #

def scrape_linkedin(role, country):
    log.info(f"LinkedIn | Searching '{role}' in {country}")
    results = []

    url = (
        "https://www.linkedin.com/jobs/search/?"
        f"keywords={quote(role)}&location={quote(country)}"
    )

    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        log.error(f"LinkedIn search failed: {r.status_code}")
        return results

    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.select("a.base-card__full-link")

    log.info(f"LinkedIn | Found {len(cards)} job cards")

    for card in cards[:10]:
        link = card.get("href")
        if not link:
            continue

        jd = fetch_job_description(link)
        if jd and contains_visa_keywords(jd):
            log.info("LinkedIn | VISA keyword FOUND")
            results.append({
                "source": "LinkedIn",
                "role": role,
                "country": country,
                "job_link": link
            })

        time.sleep(DELAY)

    return results

# --------------- INDEED ------------------ #

def scrape_indeed(role, country):
    log.info(f"Indeed | Searching '{role}' in {country}")
    results = []

    url = f"https://www.indeed.com/jobs?q={quote(role)}&l={quote(country)}"
    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        log.error(f"Indeed failed: {r.status_code}")
        return results

    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.select("a.tapItem")

    log.info(f"Indeed | Found {len(cards)} job cards")

    for card in cards[:10]:
        link = card.get("href")
        if not link:
            continue

        full_link = "https://www.indeed.com" + link
        jd = fetch_job_description(full_link)

        if jd and contains_visa_keywords(jd):
            log.info("Indeed | VISA keyword FOUND")
            results.append({
                "source": "Indeed",
                "role": role,
                "country": country,
                "job_link": full_link
            })

        time.sleep(DELAY)

    return results

# -------- JOB DESCRIPTION FETCH ---------- #

def fetch_job_description(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            log.warning(f"JD fetch failed: {r.status_code}")
            return ""

        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(separator=" ")
        return text.lower()

    except Exception as e:
        log.error(f"JD fetch error: {e}")
        return ""

# -------- GREENHOUSE (LEGAL) ------------- #

def scrape_greenhouse(company, board_url):
    log.info(f"Greenhouse | {company}")
    results = []

    r = requests.get(board_url, headers=HEADERS)
    if r.status_code != 200:
        log.error(f"Greenhouse failed: {company}")
        return results

    soup = BeautifulSoup(r.text, "html.parser")
    jobs = soup.select("a.posting-title")

    log.info(f"Greenhouse | Found {len(jobs)} jobs")

    for job in jobs:
        link = "https://boards.greenhouse.io" + job.get("href")
        jd = fetch_job_description(link)

        if jd and contains_visa_keywords(jd):
            log.info("Greenhouse | VISA keyword FOUND")
            results.append({
                "source": "Greenhouse",
                "company": company,
                "job_link": link
            })

        time.sleep(DELAY)

    return results

# -------- LEVER (LEGAL) ------------------ #

def scrape_lever(company, board_url):
    log.info(f"Lever | {company}")
    results = []

    r = requests.get(board_url, headers=HEADERS)
    if r.status_code != 200:
        log.error(f"Lever failed: {company}")
        return results

    soup = BeautifulSoup(r.text, "html.parser")
    jobs = soup.select("a.posting-title")

    log.info(f"Lever | Found {len(jobs)} jobs")

    for job in jobs:
        link = job.get("href")
        jd = fetch_job_description(link)

        if jd and contains_visa_keywords(jd):
            log.info("Lever | VISA keyword FOUND")
            results.append({
                "source": "Lever",
                "company": company,
                "job_link": link
            })

        time.sleep(DELAY)

    return results

# ---------------- MAIN ------------------- #

def main():
    all_jobs = []

    for role in ROLES:
        for country in COUNTRIES:
            all_jobs.extend(scrape_linkedin(role, country))
            all_jobs.extend(scrape_indeed(role, country))

    # ATS examples (add more anytime)
    all_jobs.extend(scrape_greenhouse(
        "Zalando", "https://boards.greenhouse.io/zalandogroup"
    ))
    all_jobs.extend(scrape_lever(
        "Spotify", "https://jobs.lever.co/spotify"
    ))

    df = pd.DataFrame(all_jobs).drop_duplicates()
    df.to_csv("visa_jobs.csv", index=False)

    log.info(f"✅ TOTAL VISA JOBS FOUND: {len(df)}")

if __name__ == "__main__":
    main()
