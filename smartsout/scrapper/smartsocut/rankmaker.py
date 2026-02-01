# scrapper/smartscout/keyword_scraper.py
import traceback
import time
import os
import glob
import shutil
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from .auth import get_authenticated_driver


def setup_download_directory(download_path: str = None):
    """Setup download directory and return path"""
    if download_path is None:
        download_path = os.path.join(os.path.dirname(__file__), "..", "downloads")
    
    os.makedirs(download_path, exist_ok=True)
    return download_path


def get_latest_downloaded_file(download_dir: str, pattern: str = "*.csv", timeout: int = 20):
    """Get the most recently downloaded CSV file with timeout"""
    print(f"  Checking for files in: {download_dir}")
    
    # Get initial file count
    files_before = set(glob.glob(os.path.join(download_dir, pattern)))
    files_before = {f for f in files_before if not f.endswith('.crdownload')}
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        files_now = set(glob.glob(os.path.join(download_dir, pattern)))
        files_now = {f for f in files_now if not f.endswith('.crdownload')}
        
        # Check if new file appeared
        new_files = files_now - files_before
        if new_files:
            latest_file = max(new_files, key=os.path.getctime)
            
            # Verify file is complete (size not changing)
            size1 = os.path.getsize(latest_file)
            time.sleep(1)
            size2 = os.path.getsize(latest_file)
            
            if size1 == size2 and size1 > 0:
                return latest_file
        
        time.sleep(1)
    
    return None


def run_keyword_tools_export(
    search_text: str, 
    username: str, 
    password: str,
    download_path: str = None,
    cleanup_downloads: bool = True,
    max_rank: int = 65  # Default value for Latest Rank filter
) -> dict:
    """
    Full workflow for Keyword Tools/Rank Maker export:
    1. Login to SmartScout
    2. Navigate to home page
    3. Click on Keyword Tools menu item
    4. Click on Rank Maker submenu
    5. Search for ASIN
    6. Open Filters panel
    7. Expand Latest Rank filter
    8. Set max rank value
    9. Click Export as button
    10. Click CSV option
    11. Download and save file
    """
    # Get system Downloads folder (where Chrome actually downloads)
    system_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    
    # Get desired output directory
    output_path = setup_download_directory(download_path)
    
    # Get authenticated driver WITHOUT custom download directory
    driver = get_authenticated_driver(
        headless=False, 
        username=username, 
        password=password,
        download_dir=None
    )
    
    wait = WebDriverWait(driver, 25)
    downloaded_file = None

    try:
        print("Step 1: Loading home page...")
        driver.get("https://app.smartscout.com/app/home")
        time.sleep(10)
        
        print("Step 2: Clicking Keyword Tools menu item...")
        keyword_tools_menu = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//mat-icon[@data-mat-icon-name='keyword-tools']/parent::div")
            )
        )
        keyword_tools_menu.click()
        time.sleep(10)
        print("  ✅ Keyword Tools menu clicked")
        
        print("Step 3: Clicking Rank Maker submenu...")
        rank_maker = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@class, 'submenu-item')]//div[@class='name' and text()='Rank Maker']")
            )
        )
        rank_maker.click()
        time.sleep(10)
        print("  ✅ Rank Maker clicked")
        
        print("Step 4: Searching for ASIN...")
        search_input = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@placeholder='Search ASIN' and @name='asin']")
            )
        )
        search_input.clear()
        time.sleep(1)
        search_input.send_keys(search_text)
        print(f"  ✅ Entered ASIN: '{search_text}'")
        
        # Press Enter or wait for search to complete
        search_input.send_keys(Keys.RETURN)
        time.sleep(5)
        print("  ✅ Search submitted")
        
        print("Step 5: Opening Filters panel...")
        filters_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@ref='eToggleButton' and contains(@class, 'ag-side-button-button')]//span[text()='Filters']")
            )
        )
        filters_button.click()
        time.sleep(5)
        print("  ✅ Filters panel opened")
        
        print("Step 6: Expanding 'Latest Rank' filter group...")
        latest_rank_header = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@class, 'ag-group-title-bar')]//span[@class='ag-group-title' and text()='Latest Rank']")
            )
        )
        latest_rank_header.click()
        time.sleep(5)
        print("  ✅ Latest Rank filter expanded")
        
        print(f"Step 7: Setting max rank value to {max_rank}...")
        max_input = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@formcontrolname='max' and @type='number']")
            )
        )
        max_input.clear()
        time.sleep(1)
        max_input.send_keys(str(max_rank))
        print(f"  ✅ Max rank set to: {max_rank}")
        time.sleep(3)
        
        print("Step 8: Clicking 'Export as' button...")
        export_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@class, 'btn-wrapper secondary')]//span[text()='Export as']")
            )
        )
        export_button.click()
        time.sleep(3)
        print("  ✅ Export as button clicked")
        
        print("Step 9: Clicking CSV option...")
        csv_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@mat-menu-item]//mat-icon[@svgicon='csv']/parent::button")
            )
        )
        csv_button.click()
        print("  ✅ CSV export clicked")
        
        # Wait for download in system Downloads folder
        print("Step 10: Waiting for download...")
        downloaded_file = get_latest_downloaded_file(system_downloads, timeout=20)
        
        if not downloaded_file:
            raise Exception("No CSV file was downloaded")
        
        print(f"  ✅ File downloaded: {os.path.basename(downloaded_file)}")
        
        # Copy to output directory with custom name
        new_filename = f"rank_maker_{search_text.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        dest_file = os.path.join(output_path, new_filename)
        shutil.copy2(downloaded_file, dest_file)
        print(f"  ✅ Copied to: {dest_file}")
        
        # Optionally delete from Downloads
        if cleanup_downloads:
            try:
                os.remove(downloaded_file)
                print(f"  🗑️ Removed from Downloads")
            except Exception as e:
                print(f"  ⚠️ Could not remove from Downloads: {e}")
        
        downloaded_file = dest_file
        
        result = {
            "status": "success",
            "message": f"Rank Maker export completed for ASIN '{search_text}' with max rank {max_rank}",
            "file_path": downloaded_file,
            "file_name": new_filename,
            "file_size": os.path.getsize(downloaded_file),
            "timestamp": datetime.now().isoformat(),
            "asin": search_text,
            "max_rank": max_rank
        }
        
        return result

    except Exception as e:
        error_msg = f"Scraping failed: {str(e)}"
        print(error_msg)
        print(f"Traceback:\n{traceback.format_exc()}")
        
        try:
            screenshot_path = os.path.join(output_path, f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            driver.save_screenshot(screenshot_path)
            print(f"Saved error screenshot: {screenshot_path}")
        except:
            pass
            
        raise Exception(error_msg) from e

    finally:
        driver.quit()