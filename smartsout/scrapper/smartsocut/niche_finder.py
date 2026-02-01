# scrapper/smartscout/scraper.py
import traceback
import time
import os
import glob
import shutil
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .auth import get_authenticated_driver


def setup_download_directory(download_path: str = None):
    """Setup download directory and return path"""
    if download_path is None:
        # Use project downloads directory
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


def run_niche_finder_export(
    search_text: str, 
    username: str, 
    password: str,
    download_path: str = None,
    cleanup_downloads: bool = True  # Delete from Downloads folder after copying
) -> dict:
    """
    Full workflow - Downloads file and prepares it for API response
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
    final_file_path = None

    try:
        print("Step 1: Loading page...")
        driver.get("https://app.smartscout.com/app/subcategories")
        time.sleep(10)
        
        print("Step 2: Locating Niche Finder tab...")
        niche_tab = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@class, 'mat-tab-label-content') and contains(., 'Niche Finder')]")
            )
        )
        niche_tab.click()
        time.sleep(10)
        print("  ✅ Niche Finder tab clicked")
        
        print("Step 3: Opening Filters panel...")
        filters_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Filters']]"))
        )
        filters_button.click()
        time.sleep(10)
        print("  ✅ Filters panel opened")
        
        print("Step 4: Clicking 'Subcategory' filter group...")
        subcategory_header = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[.//span[text()='Subcategory'] and contains(@class, 'ag-group-title-bar')]")
            )
        )
        subcategory_header.click()
        time.sleep(10)
        print("  ✅ Subcategory filter expanded")
        
        print("Step 5: Waiting for filter input field...")
        filter_input = wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//input[contains(@class, 'ag-input-field-input') and @placeholder='Filter...']")
            )
        )
        
        filter_input.clear()
        time.sleep(1)
        filter_input.send_keys(search_text)
        print(f"  ✅ Typed into filter: '{search_text}'")
        time.sleep(5)
        
        print("Step 6: Triggering export...")
        
        print("  Clicking Excel side button...")
        excel_side_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@class, 'ag-side-button-button') and .//img[contains(@src, 'excel')]]")
            )
        )
        excel_side_button.click()
        time.sleep(5)
        print("  ✅ Excel side button clicked")
        
        print("  Clicking CSV export image...")
        csv_image = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//img[contains(@src, 'csv.ico') and @mattooltip='Export as CSV']")
            )
        )
        csv_image.click()
        print("  ✅ CSV export clicked")
        
        # Wait for download in system Downloads folder
        print("Step 7: Waiting for download...")
        downloaded_file = get_latest_downloaded_file(system_downloads, timeout=20)
        
        if not downloaded_file:
            raise Exception("No CSV file was downloaded")
        
        print(f"  ✅ File downloaded: {os.path.basename(downloaded_file)}")
        
        # Copy to output directory with custom name
        new_filename = f"niche_finder_{search_text.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        final_file_path = os.path.join(output_path, new_filename)
        shutil.copy2(downloaded_file, final_file_path)
        print(f"  ✅ Copied to: {final_file_path}")
        
        # Delete from Downloads folder if requested
        if cleanup_downloads:
            try:
                os.remove(downloaded_file)
                print(f"  🗑️ Removed from Downloads folder")
            except Exception as e:
                print(f"  ⚠️ Could not remove from Downloads: {e}")
        
        file_size = os.path.getsize(final_file_path)
        
        result = {
            "status": "success",
            "message": f"Export completed for '{search_text}'",
            "file_path": final_file_path,
            "file_name": new_filename,
            "file_size": file_size,
            "timestamp": datetime.now().isoformat()
        }
        
        return result

    except Exception as e:
        error_msg = f"Scraping failed: {str(e)}"
        print(error_msg)
        print(f"Traceback:\n{traceback.format_exc()}")
        raise Exception(error_msg) from e

    finally:
        driver.quit()