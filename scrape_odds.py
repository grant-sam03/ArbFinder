from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_driver():
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        return driver
    except Exception as e:
        logger.error(f"Failed to setup Chrome driver: {str(e)}")
        raise

def scrape_odds():
    url = "https://prolineplus.olg.ca/en-ca/event-path?p23480-CFL"
    driver = None
    
    try:
        logger.info("Setting up Chrome driver...")
        driver = setup_driver()
        
        logger.info("Accessing website...")
        driver.get(url)
        
        # Wait for the odds to load
        wait = WebDriverWait(driver, 30)
        logger.info("Waiting for page to load...")
        
        try:
            # Try different possible class names for the event list
            possible_selectors = [
                "event-list",
                "game-list",
                "odds-container",
                "main-content"
            ]
            
            for selector in possible_selectors:
                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, selector)))
                    logger.info(f"Found content with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            # Additional wait for dynamic content
            time.sleep(10)
            
            # Get page source for debugging
            logger.info("Page source length: %d", len(driver.page_source))
            
            # Try to find any elements that might contain odds
            elements = driver.find_elements(By.CSS_SELECTOR, "*")
            logger.info(f"Found {len(elements)} elements on the page")
            
            # Save the page source for debugging
            with open('page_source.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            
            odds_data = []
            
            # Look for elements that might contain game information
            game_elements = driver.find_elements(By.CSS_SELECTOR, "div[class*='event'], div[class*='game'], div[class*='match']")
            
            for game in game_elements:
                try:
                    game_html = game.get_attribute('outerHTML')
                    logger.info(f"Found game element: {game_html[:200]}...")
                    
                    # Try to extract team names and odds
                    teams = game.find_elements(By.CSS_SELECTOR, "span[class*='team'], div[class*='team']")
                    odds = game.find_elements(By.CSS_SELECTOR, "span[class*='odds'], div[class*='odds']")
                    
                    if len(teams) >= 2:
                        game_data = {
                            "team1": teams[0].text.strip(),
                            "team2": teams[1].text.strip(),
                            "odds1": odds[0].text.strip() if len(odds) > 0 else "N/A",
                            "odds2": odds[1].text.strip() if len(odds) > 1 else "N/A"
                        }
                        odds_data.append(game_data)
                        logger.info(f"Found odds for: {game_data['team1']} vs {game_data['team2']}")
                
                except Exception as e:
                    logger.error(f"Error processing a game: {str(e)}")
                    continue
            
            # Save the data to a JSON file
            with open('odds_data.json', 'w') as f:
                json.dump(odds_data, f, indent=4)
            
            logger.info(f"Successfully scraped {len(odds_data)} games")
            logger.info("Data saved to odds_data.json")
            
        except TimeoutException:
            logger.error("Timeout waiting for page to load")
            # Save the page source for debugging
            with open('timeout_page_source.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
    
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    scrape_odds() 