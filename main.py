import asyncio
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# Import scrapers
from scrapers.smartscout.scrapers.niche_finder import run_niche_finder_export
from scrapers.smartscout.scrapers.rank_maker import run_keyword_tools_export

# Load environment variables
load_dotenv()

# Create limited thread pool
SCRAPER_EXECUTOR = ThreadPoolExecutor(max_workers=3)

app = FastAPI(title="Unified Scraper API")

class ScrapeRequest(BaseModel):
    search_text: str
    username: str 
    password: str
    max_rank: int = 65  # Added optional max_rank

def cleanup_file(file_path: str):
    """Delete file after it's been sent"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ Deleted: {file_path}")
    except Exception as e:
        print(f"⚠️ Could not delete {file_path}: {e}")

@app.get("/")
async def root():
    return {"message": "Welcome to the Unified Scraper API", "status": "online"}

# --- SmartScout Endpoints ---

@app.post("/smartscout/niche-finder")
async def smartscout_niche_finder(request: ScrapeRequest, background_tasks: BackgroundTasks):
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            SCRAPER_EXECUTOR,
            run_niche_finder_export,
            request.search_text,
            request.username,
            request.password
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
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/smartscout/rank-maker")
async def smartscout_rank_maker(request: ScrapeRequest, background_tasks: BackgroundTasks):
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            SCRAPER_EXECUTOR,
            run_keyword_tools_export,
            request.search_text,
            request.username,
            request.password,
            None,
            True,
            request.max_rank
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
        raise HTTPException(status_code=500, detail=str(e))

# Placeholder endpoints for future scrapers
@app.post("/smartscout/seller-search")
async def smartscout_seller_search():
    return {"message": "Endpoint not yet implemented"}

@app.post("/smartscout/product-search")
async def smartscout_product_search():
    return {"message": "Endpoint not yet implemented"}

@app.post("/website2/scrape")
async def website2_scrape():
    return {"message": "Endpoint not yet implemented"}

@app.post("/website3/scrape")
async def website3_scrape():
    return {"message": "Endpoint not yet implemented"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
