import re
import json
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options

def scrape_fighter_details(driver, fighter_relative_url):
    # Construct the full URL if it's a relative link
    if not fighter_relative_url.startswith("http"):
        detail_url = "https://www.ufc.com" + fighter_relative_url
    else:
        detail_url = fighter_relative_url

    driver.get(detail_url)
    # Use WebDriverWait or a short sleep to ensure page is loaded
    time.sleep(2)

    detail_data = {
        "nickname": None,
        "wins": None,
        "losses": None,
        "draws": None,
        "nationality": None,
        "fighting_style": None,
        "age": None,
    }

    # Example: Nickname <p class="hero-profile__nickname">"Raw Dawg"</p>
    try:
        nickname_el = driver.find_element(By.CSS_SELECTOR, "p.hero-profile__nickname")
        detail_data["nickname"] = nickname_el.text.strip()
    except:
        pass

    # Example: record <p class="hero-profile__division-body">17-7-0 (W-L-D)</p>
    try:
        record_el = driver.find_element(By.CSS_SELECTOR, ".hero-profile__division-body")
        record_text = record_el.text.strip()  # e.g. "17-7-0 (W-L-D)"
        match = re.search(r'(\d+)-(\d+)-(\d+)', record_text)
        if match:
            detail_data["wins"]   = match.group(1)
            detail_data["losses"] = match.group(2)
            detail_data["draws"]  = match.group(3)
    except:
        pass


    return detail_data

# -------------------------------------------------------------------
# MAIN SCRIPT
# -------------------------------------------------------------------

options = Options()
options.set_capability("acceptInsecureCerts", True)
# options.add_argument("--headless")  # Uncomment to run headless
driver = webdriver.Firefox(options=options)

fighters_info = []  # Will hold all fighters (champ + top 15) with minimal data

# 1) Load the Rankings page once
rankings_url = "https://www.ufc.com/rankings"
driver.get(rankings_url)

time.sleep(3)

# (Optional) Handle cookie popups
try:
    accept_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
    )
    accept_btn.click()
except:
    pass

# Collect all divisions
groupings = driver.find_elements(By.CSS_SELECTOR, "div.view-grouping")

for g in groupings:
    header_el = g.find_element(By.CSS_SELECTOR, "div.view-grouping-header")
    raw_division_name = header_el.get_attribute("innerText").strip()

    division_lower = raw_division_name.lower()
    if "pound-for-pound" in division_lower:
        continue
    if "women" in division_lower:
        continue

    division_name = raw_division_name

    table_el = g.find_element(By.TAG_NAME, "table")

    # Champion <caption>
    champion_name_els = table_el.find_elements(By.CSS_SELECTOR, "caption h5 a")
    champion_candidate = None
    if champion_name_els:
        anchor_el = champion_name_els[0]
        anchor_text        = anchor_el.text.strip()
        anchor_inner_text  = anchor_el.get_attribute("innerText").strip()
        anchor_inner_html  = anchor_el.get_attribute("innerHTML").strip()

        if anchor_text:
            champion_candidate = anchor_text
        elif anchor_inner_text:
            champion_candidate = anchor_inner_text
        else:
            champion_candidate = anchor_inner_html
        champion_candidate = champion_candidate.strip()

    champion_indicator_els = table_el.find_elements(By.CSS_SELECTOR, "caption h6 span.text")
    is_champion_label = (len(champion_indicator_els) > 0)
    champion_name = champion_candidate if champion_candidate and is_champion_label else None

    # If champion is found, store them with champion=True
    if champion_name:
        champion_link = champion_name_els[0].get_attribute("href")
        if not champion_link.startswith("http"):
            champion_link = "https://www.ufc.com" + champion_link

        item = {
            "division": division_name,
            "rank": "Champion",
            "name": champion_name,
            "champion": True,
            "url": champion_link
        }
        fighters_info.append(item)

    # Now parse top-15
    rows = table_el.find_elements(By.CSS_SELECTOR, "tbody tr")
    for idx, row in enumerate(rows[:15], start=1):
        tds = row.find_elements(By.TAG_NAME, "td")
        if len(tds) < 2:
            continue

        rank_text = tds[0].text.strip()
        name_text = tds[1].text.strip()

        # If name_text == champion_name, skip duplication
        if champion_name and (name_text == champion_name):
            continue

        # Grab link
        name_anchor = tds[1].find_element(By.TAG_NAME, "a")
        fighter_link = name_anchor.get_attribute("href")
        if not fighter_link.startswith("http"):
            fighter_link = "https://www.ufc.com" + fighter_link

        item = {
            "division": division_name,
            "rank": rank_text,
            "name": name_text,
            "champion": False,
            "url": fighter_link,
        }
        fighters_info.append(item)

# Visit each fighter's detail page exactly once
detailed_fighters = []

for fdata in fighters_info:
    detail = scrape_fighter_details(driver, fdata["url"])

    # Merge the detail data into the fighter info
    fighter_data = {
        "division": fdata["division"],
        "rank": fdata["rank"],
        "name": fdata["name"],
        "champion": fdata["champion"],
        # Extra from detail
        "nickname": detail["nickname"],
        "wins": detail["wins"],
        "losses": detail["losses"],
        "draws": detail["draws"],
        "nationality": detail["nationality"],
        "fighting_style": detail["fighting_style"],
        "age": detail["age"]
    }

    detailed_fighters.append(fighter_data)

driver.quit()

# 4) Save final data to JSON
with open("ufc_fighters_top15.json", "w", encoding="utf-8") as f:
    json.dump(detailed_fighters, f, indent=2, ensure_ascii=False)

print(f"\nDone! Scraped {len(detailed_fighters)} fighters in total.")
