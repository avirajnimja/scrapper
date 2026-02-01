# scrapper/smartscout/auth.py
import os
import pickle
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

COOKIES_PATH = Path("data/smartscout_cookies.pkl")

def get_chrome_driver(headless=True, download_dir=None):
    """Create a Chrome driver instance - SIMPLIFIED"""
    options = Options()
    
    # Force visible for now
    headless = False
    
    if headless:
        options.add_argument("--headless")
    
    # MINIMAL options - let Chrome handle downloads naturally
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=options
    )

def login_and_save_cookies(driver, username, password):
    """Perform fresh login and save cookies for next time."""
    wait = WebDriverWait(driver, 20)
    driver.get("https://app.smartscout.com/sessions/signin")
    
    wait.until(EC.presence_of_element_located((By.ID, "username")))
    
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    
    wait.until(EC.url_contains("/app/home"))
    
    COOKIES_PATH.parent.mkdir(exist_ok=True)
    pickle.dump(driver.get_cookies(), open(COOKIES_PATH, "wb"))

def get_authenticated_driver(headless=False, username=None, password=None, download_dir=None):
    """Return a driver that is already logged in."""
    driver = get_chrome_driver(headless=headless, download_dir=download_dir)
    
    driver.get("https://app.smartscout.com/app/home")
    
    cookies_restored = False
    if COOKIES_PATH.exists():
        try:
            cookies = pickle.load(open(COOKIES_PATH, "rb"))
            driver.get("https://app.smartscout.com")
            
            for cookie in cookies:
                if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                    cookie['sameSite'] = 'Lax'
                driver.add_cookie(cookie)
            
            driver.get("https://app.smartscout.com/app/home")
            
            wait = WebDriverWait(driver, 10)
            try:
                wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(), 'Dashboard') or contains(text(), 'Home')]")
                ))
                cookies_restored = True
                print("✅ Reused existing session")
            except:
                cookies_restored = False
                
        except Exception as e:
            print(f"⚠️ Cookie restore failed: {e}")
            cookies_restored = False
    
    if not cookies_restored:
        if not username or not password:
            raise ValueError("Username and password required for fresh login")
        
        print("🔑 Performing fresh login...")
        login_and_save_cookies(driver, username, password)
    
    return driver