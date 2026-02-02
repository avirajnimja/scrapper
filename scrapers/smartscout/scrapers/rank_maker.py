# scrapers/smartscout/scrapers/rank_maker.py
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
from ..auth import get_authenticated_driver  # Corrected relative import


def setup_download_directory(download_path: str = None):
    """Setup download directory and return path"""
    if download_path is None:
        # Get absolute path of project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        download_path = os.path.join(project_root, "downloads")
    
    download_path = os.path.abspath(download_path)
    os.makedirs(download_path, exist_ok=True)
    return download_path


def get_latest_downloaded_file(download_dir: str, pattern: str = "*.csv", timeout: int = 60, start_time_marker: float = None):
    """Get the most recently downloaded CSV file with timeout"""
    print(f"  Checking for files in: {download_dir}")
    
    start_wait = time.time()
    if start_time_marker is None:
        start_time_marker = start_wait

    while time.time() - start_wait < timeout:
        files = glob.glob(os.path.join(download_dir, pattern))
        # Exclude temporary download files
        files = [f for f in files if not f.endswith('.crdownload') and not f.endswith('.tmp')]
        
        if files:
            # Filter for files created after we started the process
            new_files = [f for f in files if os.path.getctime(f) >= start_time_marker - 2] # 2s buffer
            
            if new_files:
                latest_file = max(new_files, key=os.path.getctime)
                
                # Verify file is complete (size not changing and > 0)
                try:
                    size1 = os.path.getsize(latest_file)
                    time.sleep(2)
                    size2 = os.path.getsize(latest_file)
                    
                    if size1 == size2 and size1 > 0:
                        return latest_file
                except (OSError, FileNotFoundError):
                    continue
        
        time.sleep(2)
    
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
    Full workflow for Keyword Tools/Rank Maker export
    """
    # Get desired output directory
    output_path = setup_download_directory(download_path)
    
    # Get authenticated driver WITH custom download directory
    driver = get_authenticated_driver(
        headless=True, 
        username=username, 
        password=password,
        download_dir=output_path
    )
    
    wait = WebDriverWait(driver, 25)
    downloaded_file = None
    start_marker = time.time()

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
        print("  ✅ Search submitted, waiting for results...")
        
        # Wait for either the results table or "No results found"
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'ag-root-wrapper')]")))
            print("  ✅ Search results loaded")
        except:
            print("  ⚠️ Results table not found within timeout, proceeding anyway...")
            
        time.sleep(5)
        
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
        time.sleep(5)  # Wait for panel to settle
        latest_rank_header = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class, 'ag-group-title-bar') and .//span[text()='Latest Rank']]")
            )
        )
        # Try to click using JS in case it's obscured
        driver.execute_script("arguments[0].scrollIntoView(true);", latest_rank_header)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", latest_rank_header)
        
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
        
        # Wait for download in output directory
        print("Step 10: Waiting for download...")
        downloaded_file = get_latest_downloaded_file(output_path, timeout=60, start_time_marker=start_marker)
        
        if not downloaded_file:
            raise Exception("No CSV file was downloaded")
        
        print(f"  ✅ File downloaded: {os.path.basename(downloaded_file)}")
        
        # Renaissance with final name
        new_filename = f"rank_maker_{search_text.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        final_file_path = os.path.join(output_path, new_filename)
        
        # Only rename/move if it's not already named correctly (unlikely to be, but good practice)
        if downloaded_file != final_file_path:
            shutil.move(downloaded_file, final_file_path)
            print(f"  ✅ Renamed to: {final_file_path}")
        
        file_size = os.path.getsize(final_file_path)
        
        result = {
            "status": "success",
            "message": f"Rank Maker export completed for ASIN '{search_text}' with max rank {max_rank}",
            "file_path": final_file_path,
            "file_name": new_filename,
            "file_size": file_size,
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
            # Capture error screenshot
            screenshot_name = f"rank_maker_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            os.makedirs(output_path, exist_ok=True)
            screenshot_path = os.path.join(output_path, screenshot_name)
            driver.save_screenshot(screenshot_path)
            print(f"Captured error screenshot: {screenshot_path}")
        except:
            pass
            
        raise Exception(error_msg) from e

    finally:
        driver.quit()