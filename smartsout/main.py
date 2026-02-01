# app/main.py (SIMPLIFIED - Uses project downloads folder)
import asyncio
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from scrapper.smartsocut.niche_finder import run_niche_finder_export
from scrapper.smartsocut.rankmaker import run_keyword_tools_export
# Load environment variables
load_dotenv()

# Create limited thread pool (max 2 concurrent scrapers)
SCRAPER_EXECUTOR = ThreadPoolExecutor(max_workers=2)

# FastAPI app
app = FastAPI(title="SmartScout Scraper API")


class ScrapeRequest(BaseModel):
    search_text: str
    username: str 
    password: str


@app.post("/smartscout/subcategory")
async def scrape_subcategory(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Download CSV from SmartScout and return it.
    File is automatically deleted after sending.
    """
    try:
        # Run scraper - downloads to project's downloads folder
        result = await asyncio.get_event_loop().run_in_executor(
            SCRAPER_EXECUTOR,
            run_niche_finder_export,
            request.search_text,
            request.username,
            request.password,
            None,  # Use default download path
            True   # cleanup_downloads = True
        )
        
        file_path = result["file_path"]
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="File was not created")
        
        # Schedule file deletion after response is sent
        background_tasks.add_task(cleanup_file, file_path)
        
        # Return file
        return FileResponse(
            path=file_path,
            filename=result["file_name"],
            media_type="text/csv"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@app.post("/smartscout/keyword-tools")
async def scrape_keyword_tools(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Download CSV from SmartScout Keyword Tools and return it.
    File is automatically deleted after sending.
    """
    try:
        # Run scraper
        result = await asyncio.get_event_loop().run_in_executor(
            SCRAPER_EXECUTOR,
            run_keyword_tools_export,
            request.search_text,
            request.username,
            request.password,
            None,
            True
        )
        
        file_path = result["file_path"]
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="File was not created")
        
        background_tasks.add_task(cleanup_file, file_path)
        
        return FileResponse(
            path=file_path,
            filename=result["file_name"],
            media_type="text/csv"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


def cleanup_file(file_path: str):
    """Delete file after it's been sent"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ Deleted: {file_path}")
    except Exception as e:
        print(f"⚠️ Could not delete {file_path}: {e}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}



def cleanup_file(file_path: str):
    """Delete file after it's been sent"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ Deleted: {file_path}")
    except Exception as e:
        print(f"⚠️ Could not delete {file_path}: {e}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}