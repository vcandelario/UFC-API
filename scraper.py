from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options  # Firefox Options
import json
import time

options = Options()
options.set_capability("acceptInsecureCerts", True)
options.add_argument("--headless")  # Remove if you want to see the browser

driver = webdriver.Firefox(options=options)

fighters = []  # We'll accumulate all fighters here across all letters

alphabet = "abcdefghijklmnopqrstuvwxyz"
for letter in alphabet:
    url = f"http://ufcstats.com/statistics/fighters?char={letter}&page=all"
    print(f"Scraping letter '{letter}' - {url}")
    driver.get(url)

    # Brief pause for the page to load
    time.sleep(2)
    
    # If there's an SSL interstitial, try to click "Advanced" & "Proceed" (probably not needed in Firefox, but kept just in case)
    advanced_buttons = driver.find_elements(By.ID, "details-button")
    if advanced_buttons:
        advanced_buttons[0].click()
        time.sleep(1)
        
        proceed_links = driver.find_elements(By.ID, "proceed-link")
        if proceed_links:
            proceed_links[0].click()
            time.sleep(2)

    # (Optional) Accept cookies if needed
    try:
        accept_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        accept_btn.click()
    except:
        pass

    time.sleep(2)  # Let the page load fully

    # Scrape fighters for this letter
    rows = driver.find_elements(By.CSS_SELECTOR, "tr.b-statistics__table-row")
    
    for row in rows:
        cells = row.find_elements(By.CSS_SELECTOR, "td.b-statistics__table-col")
        if len(cells) < 10:
            continue

        first_name = cells[0].text.strip()
        last_name = cells[1].text.strip()
        weight_class = cells[4].text.strip()
        wins = cells[7].text.strip()
        losses = cells[8].text.strip()
        draws = cells[9].text.strip()

        link_tag = cells[0].find_element(By.TAG_NAME, "a")
        fighter_url = link_tag.get_attribute("href")

        fighters.append({
            "first_name": first_name,
            "last_name": last_name,
            "weight_class": weight_class,
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "profile_url": fighter_url,
        })

driver.quit()

# Save all fighters to JSON
with open("ufc_fighters.json", "w") as f:
    json.dump(fighters, f, indent=2)

print(f"🎉 Done! Scraped {len(fighters)} fighters in total.")
