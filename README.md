# Unified Scraper API

A modular, scalable web scraping API built with FastAPI and Selenium. This project is designed to handle multiple scraping tasks across different websites through a single entry point.

## 🚀 Features
- **Modular Architecture**: Separate packages for different websites (SmartScout, etc.).
- **Unified API**: Single FastAPI entry point for all scraping tasks.
- **Dynamic Authentication**: Provide credentials per request for flexibility.
- **Base Scraper**: Shared utility class for browser management and automatic download handling.

## 📂 Structure
```text
/scrapper
├── main.py                 # FastAPI Application (Entry Point)
├── requirements.txt        # Dependencies
├── scrapers/               # Core Scraper Package
│   ├── base_scraper.py     # Shared logic & driver setup
│   ├── smartscout/         # SmartScout Package
│   │   ├── auth.py         # Website-specific login logic
│   │   └── scrapers/       # Individual tasks
│   │       ├── niche_finder.py
│   │       ├── rank_maker.py
│   │       └── ...         # Add more here
│   ├── website2/           # Placeholder for next site
│   └── website3/           # Placeholder for next site
└── downloads/              # Output folder for scraped files
```

## 🛠️ Setup & Installation

1. **Create Virtual Environment**:
   ```bash
   python3 -m venv venv
   ```

2. **Activate Environment**:
   ```bash
   source venv/bin/activate  # Linux/Mac
   # OR
   .\venv\Scripts\activate   # Windows
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 🏃 Running the API

Start the server using Uvicorn:
```bash
python main.py
```
By default, the API will be available at `http://localhost:8000`.

## 📡 Usage (API Examples)

### Niche Finder Scrape
```bash
curl -X POST "http://localhost:8000/smartscout/niche-finder" \
     -H "Content-Type: application/json" \
     -d '{
           "search_text": "kitchen faucet",
           "username": "your_email@example.com",
           "password": "your_password"
         }'
```

The API will:
1. Initialize a browser session.
2. Log in using the provided credentials.
3. Perform the scrape.
4. Return the resulting CSV file directly in the response.

## 🔧 Extending the Project
To add a new scraper for an existing website:
1. Create a new `.py` file in `scrapers/[website]/scrapers/`.
2. Implement your scraping logic.
3. Register the new endpoint in `main.py`.

To add a new website:
1. Create a new directory in `scrapers/`.
2. Add an `auth.py` for login.
3. Follow the same pattern as `smartscout/`.
