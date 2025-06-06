import json
import logging
import re
from typing import List

import requests
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_page(url: str) -> BeautifulSoup:
    """Fetch a page and return a BeautifulSoup object."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    logger.info("Fetching %s", url)
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def scrape_odds():
    """Scrape CFL odds for a single event and store them in ``odds_data.json``."""
    url = (
        "https://prolineplus.olg.ca/en-ca/"
        "event?e817839-Football-CFL-Canada-Montreal-Alouettes-Toronto-Argonauts"
    )

    try:
        soup = fetch_page(url)
    except requests.RequestException as exc:
        logger.error("Failed to retrieve page: %s", exc)
        return

    # Attempt to extract team names and odds from the page.  The site is built
    # with dynamic markup so the exact classes may change; therefore several
    # selectors are tried.
    teams: List[str] = []
    for sel in [
        '[class*="team-name"]',
        '.team-name',
        '[class*="competitor__name"]',
    ]:
        for el in soup.select(sel):
            text = el.get_text(strip=True)
            if text and text not in teams:
                teams.append(text)
        if teams:
            break

    odds_values: List[str] = []
    for sel in [
        '[class*="price"]',
        '[class*="odds"]',
        '.american-odds',
    ]:
        for el in soup.select(sel):
            text = el.get_text(strip=True)
            if re.match(r'[-+]?\d+(\.\d+)?', text):
                odds_values.append(text)
        if odds_values:
            break

    odds_data = []
    if len(teams) >= 2:
        # Pair odds if available
        odds1 = odds_values[0] if odds_values else "N/A"
        odds2 = odds_values[1] if len(odds_values) > 1 else "N/A"
        odds_data.append({
            "team1": teams[0],
            "team2": teams[1],
            "odds1": odds1,
            "odds2": odds2,
        })

    with open("odds_data.json", "w", encoding="utf-8") as f:
        json.dump(odds_data, f, indent=4)

    logger.info("Scraped %d matchups", len(odds_data))

if __name__ == "__main__":
    scrape_odds() 