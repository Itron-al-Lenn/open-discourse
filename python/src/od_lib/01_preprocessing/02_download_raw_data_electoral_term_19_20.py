from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from od_lib.definitions.path_definitions import ELECTORAL_TERM_19_20_STAGE_01
from od_lib.helper_functions.progressbar import progressbar
import time
import random
import regex
import requests

# Setup output directory
ELECTORAL_TERM_19_20_OUTPUT = ELECTORAL_TERM_19_20_STAGE_01
ELECTORAL_TERM_19_20_OUTPUT.mkdir(parents=True, exist_ok=True)

election_periods = [
    {
        "election_period": 19,
        "url": "https://www.bundestag.de/ajax/filterlist/de/services/opendata/543410-543410?offset={}",
    },
    {
        "election_period": 20,
        "url": "https://www.bundestag.de/ajax/filterlist/de/services/opendata/866354-866354?offset={}",
    },
    {
        "election_period": 21,
        "url": "https://www.bundestag.de/ajax/filterlist/de/services/opendata/1058442-1058442?offset={}",
    },
]

# Selenium setup (Chrome)
chrome_options = Options()
chrome_options.add_argument("--headless")  # run in background
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
driver = webdriver.Chrome(service=ChromeService(), options=chrome_options)

req_session = requests.Session()
req_session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

for election_period in election_periods:
    print(
        f"Scraping links for term {election_period['election_period']}...",
        end="",
        flush=True,
    )

    OUTPUT_PATH = (
        ELECTORAL_TERM_19_20_OUTPUT
        / f"electoral_term_{election_period['election_period']}"
    )
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    offset = 0
    xml_links = []

    while True:
        URL = election_period["url"].format(str(offset))
        driver.get(URL)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "a[href$='.xml']")
                )
            )
        except:
            break  # no more links

        links = driver.find_elements(By.CSS_SELECTOR, "a[href$='.xml']")
        if not links:
            break

        xml_links.extend([link.get_attribute("href") for link in links])
        offset += len(links)
        time.sleep(0.5 + random.random())

    print("Done.")

    # Download XML files
    for url in progressbar(
        xml_links,
        f"Download XML-files for term {election_period['election_period']}...",
    ):
        page = req_session.get(url)
        time.sleep(0.5 + random.random())
        session = regex.search(r"\d{5}(?=\.xml)", url).group(0)

        with open(OUTPUT_PATH / (session + ".xml"), "w", encoding="utf-8") as file:
            file.write(
                regex.sub(
                    "</sub>", "", regex.sub("<sub>", "", page.content.decode("utf-8"))
                )
            )

driver.quit()
