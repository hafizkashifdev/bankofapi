# Automated Multi-Domain Web Scraper

This script uses Selenium and BeautifulSoup to automate login, navigation, and scraping of web pages (including dynamic Swagger UI/API documentation) from a specified domain. It handles cookies, login, CAPTCHAs (manual intervention), and saves HTML content for each visited page.

## Features
- Automated login and cookie handling
- Dynamic content expansion (Swagger UI, dropdowns, etc.)
- Handles iframes and nested elements
- Saves HTML of each visited page in organized folders
- Resilient to timeouts and common Selenium errors

## Requirements
- **Python 3.7+**
- **Google Chrome** browser
- **ChromeDriver** (matching your Chrome version)

## Installation & Setup (Step-by-Step)

### 1. Install Python
- Download and install Python 3.7 or newer from [python.org](https://www.python.org/downloads/).
- During installation, check the box **"Add Python to PATH"**.
- To verify installation, open PowerShell and run:
  ```powershell
  python --version
  ```

### 2. Install Google Chrome
- Download and install Google Chrome from [google.com/chrome](https://www.google.com/chrome/).

### 3. Install ChromeDriver
- Find your Chrome version by navigating to `chrome://settings/help` in Chrome.
- Download the matching ChromeDriver from: https://sites.google.com/chromium.org/driver/
- Extract the `chromedriver.exe` and place it:
  - In the same folder as your script, **or**
  - In a folder included in your system's PATH.
- To verify, run in PowerShell:
  ```powershell
  .\chromedriver.exe --version
  ```

### 4. Install Python Dependencies
- Open PowerShell in the script directory and run:
  ```powershell
  pip install selenium beautifulsoup4
  ```

### 5. Run the Script
- In PowerShell, navigate to the script folder:
  ```powershell
  cd "c:\Users\Orcalo PC\Desktop\Auth_python\demo\Python_scricpt\auto_auth_scricpt"
  python scricpt_multidomain.py
  ```

## ChromeDriver Setup
1. Download ChromeDriver from: https://sites.google.com/chromium.org/driver/
2. Place the `chromedriver` executable in your PATH or in the same directory as the script.

## Usage
1. **Edit Credentials and URLs**
   - Open `scricpt_multidomain.py`.
   - Set `START_URL`, `TARGET_URL`, `EMAIL`, and `PASSWORD` at the top of the script.

2. **Run the Script**
   - In your terminal, navigate to the script directory:
     ```bash
     cd path/to/Python_scricpt/auto_auth_scricpt
     ```
   - Run:
     ```bash
     python scricpt_multidomain.py
     ```

3. **Output**
   - Scraped HTML files will be saved in the `apis/` subfolders by category.

## Troubleshooting
- If you get a `chromedriver` error, ensure ChromeDriver matches your Chrome version and is in your PATH.
- If Python is not recognized, add its install path to your system's PATH variable.
- For CAPTCHA, manual intervention is required (the script will pause and prompt you).

## Customization
- Adjust scraping logic, login selectors, or output directory as needed for your target site.

---
**Author:**
- [Your Name or Organization]

**License:**
- MIT (or your preferred license)
