"""
Simplified API for Claude Desktop with ngrok
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import time
from screener_scraper import EnhancedScreenerScraper

app = FastAPI(title="Claude Desktop Screener API", version="1.0.0")

# Enable CORS for Claude Desktop
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize scraper
scraper = EnhancedScreenerScraper(delay=2)

class CompanyRequest(BaseModel):
    companies: List[str]
    max_concalls: Optional[int] = 10
    max_annual_reports: Optional[int] = 3

@app.get("/")
async def root():
    return {"message": "Claude Desktop Screener API", "status": "ready"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "claude-desktop-api"}

@app.post("/analyze-companies")
async def analyze_companies(request: CompanyRequest):
    """
    Simplified endpoint for Claude Desktop
    Returns immediate results (no background jobs)
    """
    try:
        results = {}
        
        for symbol in request.companies:
            print(f"🔍 Processing {symbol}...")
            
            # Find company
            company_url = scraper.find_company_by_symbol(symbol)
            if not company_url:
                results[symbol] = {"error": f"Company {symbol} not found"}
                continue
            
            # Extract data
            company_data = scraper.extract_concall_data(company_url)
            if not company_data:
                results[symbol] = {"error": f"No data found for {symbol}"}
                continue
            
            # Limit results for faster response
            concalls = company_data.concalls[:request.max_concalls]
            annual_reports = company_data.annual_reports[:request.max_annual_reports]
            
            # Format for Claude
            formatted_concalls = []
            for concall in concalls:
                formatted_concalls.append({
                    "title": concall.title,
                    "date": concall.date,
                    "doc_type": concall.doc_type,
                    "quarter": concall.quarter,
                    "year": concall.year,
                    "url": concall.url
                })
            
            results[symbol] = {
                "company_name": company_data.company_name,
                "symbol": symbol,
                "concalls": formatted_concalls,
                "annual_reports": annual_reports,
                "total_concalls": len(concalls),
                "total_annual_reports": len(annual_reports),
                "company_url": company_url
            }
        
        return {
            "success": True,
            "results": results,
            "total_companies": len(results),
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/company/{symbol}")
async def get_company_info(symbol: str):
    """Get basic company information"""
    try:
        company_url = scraper.find_company_by_symbol(symbol)
        if not company_url:
            raise HTTPException(status_code=404, detail=f"Company {symbol} not found")
        
        company_data = scraper.extract_concall_data(company_url)
        if not company_data:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        return {
            "company_name": company_data.company_name,
            "symbol": symbol,
            "company_url": company_url,
            "total_concalls": len(company_data.concalls),
            "total_annual_reports": len(company_data.annual_reports),
            "latest_concall": company_data.concalls[0].__dict__ if company_data.concalls else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Use port 8001 instead of 8000
    uvicorn.run(app, host="0.0.0.0", port=8001)