# scrapers/smartscout/scrapers/product_search.py
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
from ..auth import get_authenticated_driver

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

def run_product_search_export(
    keywords: str, 
    username: str, 
    password: str,
    max_rank: int = 1000,
    download_path: str = None
) -> dict:
    """
    Workflow for Product Search export
    """
    output_path = setup_download_directory(download_path)
    
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
        
        print("Step 2: Clicking Market Research menu item...")
        market_research_menu = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//mat-icon[@data-mat-icon-name='market-research-active' or @data-mat-icon-name='market-research']/parent::div")
            )
        )
        market_research_menu.click()
        time.sleep(5)
        print("  ✅ Market Research menu clicked")
        
        print("Step 3: Clicking Products submenu...")
        products_submenu = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@class, 'submenu-item')]//div[@class='name' and text()='Products']")
            )
        )
        products_submenu.click()
        time.sleep(10)
        print("  ✅ Products submenu clicked")
        
        print("Step 4: Clicking Filters button...")
        filters_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@class, 'btn-wrapper primary')]//span[text()='Filters']")
            )
        )
        filters_button.click()
        time.sleep(5)
        print("  ✅ Filters button clicked")
        
        print(f"Step 5: Entering keywords: '{keywords}'...")
        keywords_input = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@placeholder='Enter keywords']")
            )
        )
        keywords_input.clear()
        time.sleep(1)
        keywords_input.send_keys(keywords)
        keywords_input.send_keys(Keys.RETURN)
        time.sleep(5)
        print("  ✅ Keywords entered and submitted")
        
        print("Step 6: Expanding 'Main Category Rank' filter group...")
        # Scroll to ensure it's visible
        rank_header = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class, 'simple-expansion-panel-header')]//h2[text()='Main Category Rank']")
            )
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", rank_header)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", rank_header)
        time.sleep(3)
        print("  ✅ Main Category Rank expanded")
        
        print(f"Step 7: Setting max rank to {max_rank}...")
        max_rank_input = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@placeholder='max']")
            )
        )
        max_rank_input.clear()
        time.sleep(1)
        max_rank_input.send_keys(str(max_rank))
        max_rank_input.send_keys(Keys.RETURN)
        time.sleep(2)
        print(f"  ✅ Max rank set to: {max_rank}")
        
        print("Step 7.5: Clicking Apply button...")
        try:
            apply_button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Apply') or .//span[text()='Apply']]")
                )
            )
            apply_button.click()
            time.sleep(5)
            print("  ✅ Apply button clicked")
        except:
            print("  ⚠️ Apply button not found or not clickable, proceeding...")
        
        print("Step 8: Clicking Export button...")
        export_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@class, 'btn-wrapper secondary')]//span[text()='Export']")
            )
        )
        export_button.click()
        time.sleep(3)
        print("  ✅ Export button clicked")
        
        print("Step 9: Clicking CSV option...")
        csv_option = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@mat-menu-item]//span[text()='CSV']")
            )
        )
        csv_option.click()
        print("  ✅ CSV option clicked")
        
        # Wait for download
        print("Step 10: Waiting for download...")
        downloaded_file = get_latest_downloaded_file(output_path, timeout=60, start_time_marker=start_marker)
        
        if not downloaded_file:
            raise Exception("No CSV file was downloaded")
        
        print(f"  ✅ File downloaded: {os.path.basename(downloaded_file)}")
        
        # Rename with final name
        safe_keywords = keywords.replace(' ', '_').replace('/', '_')
        new_filename = f"product_search_{safe_keywords}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        final_file_path = os.path.join(output_path, new_filename)
        
        shutil.move(downloaded_file, final_file_path)
        print(f"  ✅ Renamed to: {final_file_path}")
        
        file_size = os.path.getsize(final_file_path)
        
        result = {
            "status": "success",
            "message": f"Product Search export completed for keywords '{keywords}'",
            "file_path": final_file_path,
            "file_name": new_filename,
            "file_size": file_size,
            "timestamp": datetime.now().isoformat(),
            "keywords": keywords,
            "max_rank": max_rank
        }
        
        return result

    except Exception as e:
        error_msg = f"Product Search Scraping failed: {str(e)}"
        print(error_msg)
        print(f"Traceback:\n{traceback.format_exc()}")
        
        try:
            screenshot_name = f"product_search_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            os.makedirs(output_path, exist_ok=True)
            screenshot_path = os.path.join(output_path, screenshot_name)
            driver.save_screenshot(screenshot_path)
            print(f"Captured error screenshot: {screenshot_path}")
        except:
            pass
            
        raise Exception(error_msg) from e

    finally:
        driver.quit()
