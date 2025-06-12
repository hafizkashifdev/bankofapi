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

# === Configuration ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
EMAIL = "muhammadazam.altaf@consultancyoutfit.co.uk"
PASSWORD = "!exTTS9FC86@!Sc"
OUTPUT_DIR = "natwestWeb_apis"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DOCUMENTATION_TIMEOUT = 60  # seconds
REGULAR_TIMEOUT = 30  # seconds

TARGET_URLS = [
    "https://developer.sandbox.natwest.com/",
    "https://developer.sandbox.natwest.com/dashboard",
    "https://developer.sandbox.natwest.com/api-catalog",
    "https://developer.sandbox.natwest.com/help",
    "https://developer.sandbox.natwest.com/api-catalog/4767019/getting-started",
    "https://www.bankofapis.com/products/natwest-group-open-banking/accounts/documentation/nwb/4.0.0",
    "https://developer.sandbox.natwest.com/api-catalog/4767019/specification",
    "https://developer.sandbox.natwest.com/api-catalog/3713276/getting-started",
    "https://www.bankofapis.com/products/natwest-group-partner/balance-reporting/documentation/nwb/3.1.4",
    "https://www.bankofapis.com/products/natwest-group-partner/balance-reporting/documentation/nwb/3.1.4#api-specification",
    "https://www.bankofapis.com/products/natwest-group-partner/balance-reporting#next-steps-apply-for-live-access",
    "https://developer.sandbox.natwest.com/api-catalog/3972008/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/3972008/specification",
    "https://www.bankofapis.com/products/direct-access/direct-accounts#next-steps-apply-for-live-access",
    "https://developer.sandbox.natwest.com/api-catalog/3753898/getting-started",
    "https://www.bankofapis.com/products/natwest-group-partner/address-verification/",
    "https://developer.sandbox.natwest.com/api-catalog/3753898/specification",
    "https://developer.sandbox.natwest.com/api-catalog/3669807/getting-started",
    "https://www.bankofapis.com/products/natwest-group-partner/age-verification/",
    "https://developer.sandbox.natwest.com/api-catalog/3669807/specification",
    "https://developer.sandbox.natwest.com/api-catalog/3731625/getting-started",
    "https://www.bankofapis.com/products/api/citizenship-verification/documentation/nwb/1.0.0",
    "https://developer.sandbox.natwest.com/api-catalog/3731625/specification",
    "https://developer.sandbox.natwest.com/api-catalog/3674172/getting-started",
    "https://bankofapis.com/products/natwest-group-partner/customer-discovery/documentation/nwb/3.0.0",
    "https://developer.sandbox.natwest.com/api-catalog/3674172/specification",
    "https://developer.sandbox.natwest.com/api-catalog/4011581/getting-started",
    "https://www.bankofapis.com/products/natwest-group-partner/e-commerce-quick-checkout/documentation/nwb/1.0.0#mutual-tls",
    "https://developer.sandbox.natwest.com/api-catalog/4011581/specification",
    "https://developer.sandbox.natwest.com/api-catalog/3790181/getting-started",
    "https://www.bankofapis.com/products/api/customer-identity/",
    "https://developer.sandbox.natwest.com/api-catalog/3790181/specification",
    "https://developer.sandbox.natwest.com/api-catalog/3670341/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/3670341/specification",
    "https://developer.sandbox.natwest.com/api-catalog/1845857/getting-started",
    "https://www.bankofapis.com/products/foreign-exchange/fx-rates/documentation/nwb/1.0.0#api-specification",
    "https://developer.sandbox.natwest.com/api-catalog/1845857/specification",
    "https://developer.sandbox.natwest.com/api-catalog/1870428/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/1870428/specification",
    "https://developer.sandbox.natwest.com/api-catalog/4767000/getting-started",
    "https://www.bankofapis.com/products/natwest-group-open-banking/event-notifications/documentation/nwb/4.0",
    "https://developer.sandbox.natwest.com/api-catalog/4767000/specification",
    "https://developer.sandbox.natwest.com/api-catalog/3660690/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/4162700/getting-started",
    "https://www.bankofapis.com/products/api/commercial-vrp/documentation/nwb",
    "https://developer.sandbox.natwest.com/api-catalog/4162700/specification",
    "https://developer.sandbox.natwest.com/api-catalog/3574477/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/3574477/specification",
    "https://developer.sandbox.natwest.com/api-catalog/4767042/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/4767042/specification",
    "https://developer.sandbox.natwest.com/api-catalog/1742236/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/1742236/specification",
    "https://developer.sandbox.natwest.com/api-catalog/4766945/getting-started",
    "https://www.bankofapis.com/products/natwest-group-open-banking/payments/documentation/nwb/4.0.0",
    "https://developer.sandbox.natwest.com/api-catalog/4766945/specification",
    "https://developer.sandbox.natwest.com/api-catalog/4767066/getting-started",
    "https://developer.sandbox.natwest.com/api-catalog/4767066/specification",
    "https://developer.sandbox.natwest.com/documentation",
    "https://natwest-bankofapi-servicemanagement.atlassian.net/servicedesk/customer/portals",
    "https://developer.sandbox.natwest.com/terms",
    "https://developer.sandbox.natwest.com/privacy-policy"
]
# === Utility Functions ===
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

def wait_for_page_load(driver, url, timeout=30):
    """Wait for the page to fully load."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        if "documentation" in url.lower():
            time.sleep(5)  # Extra wait for documentation pages
        logging.info(f"Page fully loaded (timeout: {timeout}s)")
    except TimeoutException:
        logging.warning(f"Timeout waiting for page to load (timeout: {timeout}s)")

def handle_iframes(driver):
    """Scrape content from all iframes on the page."""
    iframe_content = []
    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        logging.info(f"Found {len(iframes)} iframes")
        for index, iframe in enumerate(iframes):
            try:
                driver.switch_to.frame(iframe)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                iframe_soup = BeautifulSoup(driver.page_source, "html.parser")
                iframe_content.append(iframe_soup.prettify())
                driver.switch_to.default_content()
            except Exception as e:
                logging.warning(f"Failed to scrape iframe {index + 1}: {e}")
                driver.switch_to.default_content()
    except Exception as e:
        logging.error(f"Error finding iframes: {e}")
    return iframe_content

def expand_dynamic_elements(driver, url):
    """Expand Swagger UI or other dynamic elements."""
    try:
        WebDriverWait(driver, DOCUMENTATION_TIMEOUT if "documentation" in url.lower() else 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "opblock"))
        )
        operation_blocks = driver.find_elements(By.CLASS_NAME, "opblock")
        logging.info(f"Found {len(operation_blocks)} Swagger operation blocks")
        for block in operation_blocks:
            try:
                if "is-open" not in block.get_attribute("class"):
                    header = block.find_element(By.CLASS_NAME, "opblock-summary")
                    header.click()
                    if "documentation" in url.lower():
                        time.sleep(1)  # Increased wait for documentation
            except NoSuchElementException:
                logging.warning("Missing element in Swagger block")
    except TimeoutException:
        logging.info("No Swagger UI elements found")

def clean_html(soup):
    """Remove unwanted elements like modals, consent forms, and reCAPTCHA."""
    for element in soup.select('.modal, .modal-dialog, .modal-content, .consent, .recaptcha'):
        element.decompose()
    return soup

def perform_login(driver, login_url):
    """Perform login to the NatWest Developer Sandbox."""
    try:
        driver.get(login_url)
        wait_for_page_load(driver, login_url, timeout=30)

        # Skip cookie popup handling unless strictly necessary
        try:
            allow_cookies_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Allow All Cookies')]"))
            )
            allow_cookies_button.click()
            logging.info("Cookies accepted")
            time.sleep(1)
        except (TimeoutException, NoSuchElementException):
            pass  # Skip if no cookie popup is found

        # Perform login
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']")))
        email_field = driver.find_element(By.XPATH, "//input[@type='email']")
        password_field = driver.find_element(By.XPATH, "//input[@type='password']")
        sign_in_button = driver.find_element(By.XPATH, "//button[contains(., 'Sign in')]")

        email_field.clear()
        email_field.send_keys(EMAIL)
        password_field.clear()
        password_field.send_keys(PASSWORD)
        sign_in_button.click()
        logging.info("Login submitted")

        WebDriverWait(driver, 60).until(lambda d: "api-catalog" in d.current_url or "dashboard" in d.current_url)
        logging.info("Redirected after login")
        time.sleep(2)

        return True
    except Exception as e:
        logging.error(f"Login failed: {e}")
        return False

def create_index_file(scraped_urls):
    """Create an index.html file with links to all scraped pages."""
    index_path = os.path.join(OUTPUT_DIR, "index.html")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>NatWest API Scraping Results</title>
    <style>body{font-family:Arial,sans-serif;line-height:1.6;margin:0;padding:20px;}h1{color:#2c3e50;}.header{margin-bottom:30px;}.url-list{list-style-type:none;padding:0;}.url-item{margin-bottom:10px;padding:10px;background:#f5f5f5;border-radius:4px;}.url-item a{color:#2980b9;text-decoration:none;}.url-item a:hover{text-decoration:underline;}.timestamp{color:#7f8c8d;font-size:0.9em;}</style></head>
    <body><div class="header"><h1>NatWest API Scraping Results</h1><p class="timestamp">Generated on: {timestamp}</p><p>Total pages scraped: {len(scraped_urls)}</p></div>
    <ul class="url-list">{"".join(f'<li class="url-item"><a href="{os.path.relpath(url["filepath"], OUTPUT_DIR)}" target="_blank">{url["url"]}</a></li>' for url in scraped_urls)}</ul></body></html>
    """
    with open(index_path, "w", encoding="utf-8") as file:
        file.write(html_content)
    logging.info(f"Index file created: {index_path}")

# === Main Scraping Process ===
def main():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)

    scraped_data = []
    
    try:
        login_url = "https://developer.sandbox.natwest.com/api-catalog"
        if not perform_login(driver, login_url):
            logging.error("Cannot proceed due to login failure")
            return

        visited = set()
        for url in TARGET_URLS:
            norm_url = normalize_url(url)
            if norm_url in visited or norm_url.endswith("#"):
                logging.info(f"Skipping {url} (visited or fragment)")
                continue
            visited.add(norm_url)
            logging.info(f"Scraping: {url}")

            try:
                driver.get(url)
                wait_for_page_load(driver, url, DOCUMENTATION_TIMEOUT if "documentation" in url.lower() else REGULAR_TIMEOUT)

                expand_dynamic_elements(driver, url)

                soup = BeautifulSoup(driver.page_source, "html.parser")
                soup = clean_html(soup)  # Remove unwanted elements
                iframe_content = handle_iframes(driver)
                filename = safe_filename(url)
                combined_content = soup.prettify()
                for i, content in enumerate(iframe_content):
                    combined_content += f"\n\n<!-- Iframe {i + 1} Content -->\n{content}"

                saved_path = save_html(combined_content, filename)
                scraped_data.append({"url": url, "filepath": saved_path})

            except TimeoutException:
                logging.warning(f"Timeout scraping {url}")
            except Exception as e:
                logging.error(f"Error scraping {url}: {e}")

    finally:
        driver.quit()
        logging.info(f"Scraping completed. Total pages scraped: {len(visited)}")
        if scraped_data:
            create_index_file(scraped_data)

if __name__ == "__main__":
    main()