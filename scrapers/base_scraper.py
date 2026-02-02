import os
import time
import glob
import shutil
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class BaseScraper:
    def __init__(self, download_dir=None):
        if download_dir is None:
            self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.download_dir = os.path.join(self.project_root, "downloads")
        else:
            self.download_dir = download_dir
        
        os.makedirs(self.download_dir, exist_ok=True)
        self.system_downloads = os.path.join(os.path.expanduser("~"), "Downloads")

    def get_driver(self, headless=False):
        options = Options()
        if headless:
            options.add_argument("--headless")
        
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), 
            options=options
        )
        return driver

    def get_latest_download(self, pattern: str = "*.csv", timeout: int = 20, search_dir: str = None):
        """Get the most recently downloaded file with timeout"""
        target_dir = search_dir or self.system_downloads
        print(f"  Checking for files in: {target_dir}")
        
        files_before = set(glob.glob(os.path.join(target_dir, pattern)))
        files_before = {f for f in files_before if not f.endswith('.crdownload')}
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            files_now = set(glob.glob(os.path.join(target_dir, pattern)))
            files_now = {f for f in files_now if not f.endswith('.crdownload')}
            
            new_files = files_now - files_before
            if new_files:
                latest_file = max(new_files, key=os.path.getctime)
                
                # Wait for file to finish downloading
                size1 = -1
                while True:
                    size2 = os.path.getsize(latest_file)
                    if size1 == size2 and size1 > 0:
                        return latest_file
                    size1 = size2
                    time.sleep(1)
            
            time.sleep(1)
        return None

    def move_to_output(self, source_file, prefix, search_text, cleanup=True):
        """Move downloaded file to project output directory with renamed filename"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_search = search_text.replace(' ', '_')
        new_filename = f"{prefix}_{safe_search}_{timestamp}{os.path.splitext(source_file)[1]}"
        dest_path = os.path.join(self.download_dir, new_filename)
        
        shutil.copy2(source_file, dest_path)
        if cleanup:
            try:
                os.remove(source_file)
            except Exception as e:
                print(f"  ⚠️ Could not remove source file: {e}")
        
        return dest_path, new_filename
