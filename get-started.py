from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
import os
import re
import uuid
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === Configuration ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
EMAIL = os.getenv('NATWEST_EMAIL')
PASSWORD = os.getenv('NATWEST_PASSWORD')
OUTPUT_DIR = "scraped-html-getstarted"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DOCUMENTATION_TIMEOUT = 40  # seconds

# List of target URLs for getting-started pages
TARGET_URLS = [
    "https://developer.sandbox.natwest.com/api-catalog/4767019/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/3713276/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/3972008/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/3753898/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/3669807/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/3731625/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/3674172/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/4011581/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/3790181/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/3670341/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/1845857/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/1870428/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/4767000/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/3660690/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/4162700/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/3574477/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/4767042/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/1742236/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/4766945/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/4767066/getting-started"
]

def normalize_url(url):
    """Return URL as-is for scraping."""
    return url

def safe_filename(url, max_length=100):
    """Generate a safe filename for saving scraped content."""
    parsed = urlparse(url)
    path = unquote(parsed.path).strip("/").replace("/", "_") or "index"
    category = "documentation"  # All URLs are documentation pages
    subdir = os.path.join(OUTPUT_DIR, category)
    os.makedirs(subdir, exist_ok=True)
    safe_path = re.sub(r'[^a-zA-Z0-9_\-]', '_', path)
    truncated = safe_path[:max_length]
    uid = uuid.uuid4().hex[:6]
    return os.path.join(subdir, f"scraped_{truncated}_{uid}.html")

def save_html(content, filename):
    """Save HTML content to a file."""
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)
    logging.info(f"Saved: {filename}")
    return filename

def wait_for_page_load(driver, url, timeout=30):
    """Wait for the page to fully load."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(5)  # Additional delay for documentation pages
        logging.info(f"Page loaded: {url}")
    except TimeoutException:
        logging.warning(f"Timeout waiting for page load: {url}")

def handle_cookie_banner(driver):
    """Handle cookie consent banner if present."""
    try:
        cookie_accept = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id*='accept'], button[class*='cookie-accept']"))
        )
        cookie_accept.click()
        logging.info("Accepted cookies")
        time.sleep(1)
    except Exception:
        logging.debug("No cookie banner found")

def perform_login(driver, login_url):
    """Perform login to the NatWest Developer Sandbox with a delay for page loading."""
    try:
        driver.get(login_url)
        wait_for_page_load(driver, login_url, 30)
        
        handle_cookie_banner(driver)
        
        email_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
        )
        password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        
        email_field.send_keys(EMAIL)
        password_field.send_keys(PASSWORD)
        submit_button.click()
        
        # Wait for redirect to dashboard or API catalog
        WebDriverWait(driver, 60).until(
            lambda d: "api-catalog" in d.current_url or "dashboard" in d.current_url
        )
        
        # Add delay to ensure full page load after login
        time.sleep(5)  # 5-second delay for page stabilization
        logging.info("Login successful with post-login delay")
        return True
    except Exception as e:
        logging.error(f"Login failed: {str(e)}")
        return False

def clean_html(soup):
    """Remove unwanted elements from HTML."""
    unwanted = [
        '.modal', '.cookie-banner', '.recaptcha',
        '.overlay', '.consent', '.advertisement'
    ]
    for selector in unwanted:
        for element in soup.select(selector):
            element.decompose()
    return soup

def scrape_page(driver, url):
    """Scrape a getting-started page."""
    try:
        driver.get(url)
        wait_for_page_load(driver, url, DOCUMENTATION_TIMEOUT)
        
        if "sign-in" in driver.current_url:
            if not perform_login(driver, url):
                return None
            driver.get(url)
            wait_for_page_load(driver, url, DOCUMENTATION_TIMEOUT)
        
        handle_cookie_banner(driver)
        
        html_content = driver.execute_script("return document.documentElement.outerHTML")
        soup = BeautifulSoup(html_content, "html.parser")
        soup = clean_html(soup)
        
        return soup.prettify()
    
    except Exception as e:
        logging.error(f"Error scraping {url}: {str(e)}")
        return None

def create_index(scraped_data):
    """Create index.html with links to all scraped pages."""
    index_path = os.path.join(OUTPUT_DIR, "index.html")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Scraping Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }}
        h1 {{ color: #2c3e50; }}
        .url-list {{ list-style: none; padding: 0; }}
        .url-item {{ padding: 8px; margin-bottom: 5px; background: #f5f5f5; }}
        .url-item a {{ color: #2980b9; text-decoration: none; }}
    </style>
</head>
<body>
    <h1>Scraping Results ({timestamp})</h1>
    <p>Total pages: {len(scraped_data)}</p>
    <ul class="url-list">
        {"".join(
            f'<li class="url-item"><a href="{os.path.relpath(item["filepath"], OUTPUT_DIR)}">{item["url"]}</a></li>'
            for item in scraped_data
        )}
    </ul>
</body>
</html>"""
    
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    logging.info(f"Index created: {index_path}")

def main():
    """Main execution function to scrape getting-started pages."""
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=options)
    scraped_data = []
    
    try:
        # Initial login
        if not perform_login(driver, "https://developer.sandbox.natwest.com/api-catalog"):
            logging.error("Initial login failed")
            return
        
        # Scrape each target URL
        for url in TARGET_URLS:
            clean_url = normalize_url(url)
            logging.info(f"Processing: {clean_url}")
            
            content = scrape_page(driver, clean_url)
            if content:
                filename = safe_filename(clean_url)
                saved_path = save_html(content, filename)
                scraped_data.append({
                    "url": clean_url,
                    "filepath": saved_path
                })
            
    finally:
        driver.quit()
        if scraped_data:
            create_index(scraped_data)
        logging.info("Scraping completed")

if __name__ == "__main__":
    main()
