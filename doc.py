from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urldefrag, unquote
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
OUTPUT_DIR = "doc"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DOCUMENTATION_TIMEOUT = 40  # seconds
REGULAR_TIMEOUT = 10  # seconds

TARGET_URLS = [
    "https://developer.sandbox.natwest.com/",
    "https://developer.sandbox.natwest.com/dashboard",
    "https://developer.sandbox.natwest.com/api-catalog",
    "https://www.bankofapis.com/products/natwest-group-partner/balance-reporting/documentation/nwb/3.1.4",
    "https://www.bankofapis.com/products/api/citizenship-verification/documentation/nwb/1.0.0",
    "https://bankofapis.com/products/natwest-group-partner/customer-discovery/documentation/nwb/3.0.0",
    "https://www.bankofapis.com/products/natwest-group-partner/e-commerce-quick-checkout/documentation/nwb/1.0.0#mutual-tls",
    "https://www.bankofapis.com/products/foreign-exchange/fx-rates/documentation/nwb/1.0.0#api-specification",
    "https://www.bankofapis.com/products/natwest-group-open-banking/event-notifications/documentation/nwb/4.0",
    "https://www.bankofapis.com/products/natwest-group-open-banking/payments/documentation/nwb/4.0.0"
]

def normalize_url(url):
    """Normalize URL by removing fragments."""
    return urldefrag(url)[0]

def safe_filename(url, max_length=100):
    """Generate a safe filename for saving scraped content."""
    parsed = urlparse(url)
    path = unquote(parsed.path).strip("/").replace("/", "_") or "index"
    category = "misc"
    if "api" in path.lower():
        category = "api"
    elif "documentation" in path.lower():
        category = "documentation"
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

def expand_all_elements(driver):
    """Expand all expandable elements in optimal order with retries"""
    expand_selectors = [
        ".opblock-summary-control",  # API operation blocks
        ".model-box-control",        # Model containers
        "[aria-expanded='false']",   # Any remaining expandable elements
        ".toggle-arrow",             # Additional toggle elements
        ".collapsible-control"       # Other collapsible sections
    ]
    
    max_attempts = 3
    total_expanded = 0
    
    for attempt in range(max_attempts):
        expanded_this_round = 0
        for selector in expand_selectors:
            try:
                elements = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
                for element in elements:
                    try:
                        if element.get_attribute("aria-expanded") == "false":
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            driver.execute_script("arguments[0].click();", element)
                            expanded_this_round += 1
                            time.sleep(0.2)  # Brief pause between clicks
                    except Exception:
                        continue
            except Exception:
                continue
        
        total_expanded += expanded_this_round
        if expanded_this_round == 0:
            break
            
        time.sleep(1)  # Wait for DOM updates between attempts
    
    logging.info(f"Total elements expanded: {total_expanded}")
    time.sleep(2)  # Final wait for content to settle
    
    # Final JavaScript pass to catch any stubborn elements
    try:
        driver.execute_script("""
            const expand = (selector) => {
                document.querySelectorAll(selector).forEach(el => {
                    if (el.getAttribute('aria-expanded') === 'false') {
                        el.scrollIntoView({block: 'center'});
                        el.click();
                    }
                });
            };
            expand('.opblock-summary-control');
            expand('.model-box-control');
            expand('[aria-expanded="false"]');
        """)
        time.sleep(1)
    except Exception as e:
        logging.warning(f"Final JS expansion failed: {str(e)}")

def wait_for_page_load(driver, url, timeout=30):
    """Wait for the page to fully load."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        if "documentation" in url.lower():
            time.sleep(3)  # Extra wait for documentation pages
        logging.info(f"Page loaded: {url}")
    except TimeoutException:
        logging.warning(f"Timeout waiting for page load: {url}")

def handle_iframes(driver):
    """Scrape content from all iframes on the page."""
    iframe_content = []
    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for index, iframe in enumerate(iframes):
            try:
                driver.switch_to.frame(iframe)
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                iframe_soup = BeautifulSoup(driver.page_source, "html.parser")
                iframe_content.append(iframe_soup.prettify())
                driver.switch_to.default_content()
            except Exception as e:
                logging.warning(f"Iframe {index} error: {str(e)}")
                driver.switch_to.default_content()
    except Exception as e:
        logging.error(f"Iframe handling error: {str(e)}")
    return iframe_content

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
    """Perform login to the NatWest Developer Sandbox."""
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
        
        WebDriverWait(driver, 60).until(
            lambda d: "api-catalog" in d.current_url or "dashboard" in d.current_url
        )
        logging.info("Login successful")
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
    """Main scraping function for a single page."""
    try:
        driver.get(url)
        wait_for_page_load(driver, url, 
                         DOCUMENTATION_TIMEOUT if "documentation" in url.lower() else REGULAR_TIMEOUT)
        
        if "sign-in" in driver.current_url:
            if not perform_login(driver, url):
                return None
            driver.get(url)
            wait_for_page_load(driver, url, DOCUMENTATION_TIMEOUT)
        
        handle_cookie_banner(driver)
        
        if "documentation" in url.lower():
            expand_all_elements(driver)
        
        html_content = driver.execute_script("return document.documentElement.outerHTML")
        soup = BeautifulSoup(html_content, "html.parser")
        soup = clean_html(soup)
        
        return soup
    
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
    """Main execution function."""
    options = Options()
    # Removed --headless to make browser visible
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
        
        for url in TARGET_URLS:
            clean_url = normalize_url(url)
            logging.info(f"Processing: {clean_url}")
            
            page_soup = scrape_page(driver, clean_url)
            if not page_soup:
                continue
                
            iframes = handle_iframes(driver)
            filename = safe_filename(clean_url)
            
            # Combine main content with iframes
            combined = page_soup.prettify()
            for i, iframe in enumerate(iframes, 1):
                combined += f"\n\n<!-- IFRAME {i} -->\n{iframe}"
            
            saved_path = save_html(combined, filename)
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
