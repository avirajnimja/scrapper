# scrapper/smartscout/auth.py
import os
import pickle
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

PROJECT_ROOT = Path(__file__).parent.parent.parent
COOKIES_PATH = PROJECT_ROOT / "data" / "smartscout_cookies.pkl"

def get_chrome_driver(headless=True, download_dir=None):
    """Create a Chrome driver instance - SIMPLIFIED"""
    options = Options()
    
    if headless:
        options.add_argument("--headless=new") # Using newer headless mode
    
    # MINIMAL options
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Configure download behavior if directory provided
    if download_dir:
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)
    
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=options
    )

def login_and_save_cookies(driver, username, password):
    """Perform fresh login and save cookies for next time."""
    wait = WebDriverWait(driver, 25)
    driver.get("https://app.smartscout.com/sessions/signin")
    
    try:
        wait.until(EC.presence_of_element_located((By.ID, "username")))
        
        driver.find_element(By.ID, "username").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        # Wait for home page with longer timeout for login
        wait.until(EC.url_contains("/app/home"))
        time.sleep(5) # Wait for page to fully load
        
        COOKIES_PATH.parent.mkdir(exist_ok=True)
        pickle.dump(driver.get_cookies(), open(COOKIES_PATH, "wb"))
        print("✅ Fresh login successful, cookies saved.")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        raise e

def get_authenticated_driver(headless=True, username=None, password=None, download_dir=None):
    """Return a driver that is already logged in, reusing cookies if possible."""
    driver = get_chrome_driver(headless=headless, download_dir=download_dir)
    wait = WebDriverWait(driver, 15)
    
    try:
        if COOKIES_PATH.exists():
            print("🍪 Attempting to reuse existing cookies...")
            driver.get("https://app.smartscout.com/app/home") # Need to be on domain to set cookies
            
            cookies = pickle.load(open(COOKIES_PATH, "rb"))
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception:
                    pass
            
            # Refresh to apply cookies
            driver.refresh()
            time.sleep(5)
            
            # Check if we are actually logged in
            if "/app/home" in driver.current_url:
                print("✅ Session restored from cookies.")
                return driver
            else:
                print("⚠️ Cookies expired or invalid.")
        
        # If no cookies or expired, perform fresh login
        if not username or not password:
            driver.quit()
            raise ValueError("Username and password required for login")
        
        print("🔑 Performing fresh login...")
        login_and_save_cookies(driver, username, password)
        
    except Exception as e:
        print(f"⚠️ Auth error: {e}")
        # Try login one more time if it fails
        if username and password:
            try:
                login_and_save_cookies(driver, username, password)
            except Exception:
                driver.quit()
                raise e
    
    return driver