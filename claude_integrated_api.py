"""
Comprehensive API for Claude Desktop Integration
No manual code sharing required - Claude calls endpoints directly
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import time
import os
from screener_scraper import EnhancedScreenerScraper

app = FastAPI(
    title="Claude Desktop Stock Scraper API",
    description="Complete API for Claude Desktop to analyze Indian stocks",
    version="2.0.0"
)

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

# Get port from environment variable (Railway sets this)
PORT = int(os.environ.get("PORT", 8001))

class CompanyAnalysisRequest(BaseModel):
    companies: List[str]
    analysis_type: Optional[str] = "comprehensive"
    max_concalls: Optional[int] = 10
    max_annual_reports: Optional[int] = 3

@app.get("/")
async def root():
    return {
        "message": "Claude Desktop Stock Scraper API",
        "version": "2.0.0",
        "status": "ready",
        "endpoints": {
            "analyze_single": "/analyze/{symbol}",
            "analyze_multiple": "/analyze-companies",
            "compare_companies": "/compare",
            "sector_analysis": "/sector/{sector_name}",
            "claude_ready": "/claude-ready"
        }
    }

@app.get("/claude-ready")
async def claude_ready():
    """Endpoint to check if API is ready for Claude Desktop"""
    return {
        "claude_ready": True,
        "api_status": "operational",
        "available_functions": [
            "analyze_single_company",
            "compare_companies", 
            "analyze_it_sector",
            "analyze_banking_sector",
            "analyze_auto_sector",
            "analyze_pharma_sector",
            "custom_sector_analysis"
        ],
        "usage_instructions": "Claude can call these endpoints directly using the ngrok URL"
    }

@app.get("/analyze/{symbol}")
async def analyze_single_company(symbol: str):
    """
    Analyze a single company
    Claude can call: GET /analyze/INFY
    """
    try:
        # Find company
        company_url = scraper.find_company_by_symbol(symbol)
        if not company_url:
            raise HTTPException(status_code=404, detail=f"Company {symbol} not found")
        
        # Extract data
        company_data = scraper.extract_concall_data(company_url)
        if not company_data:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        # Format for Claude
        concalls = []
        for concall in company_data.concalls[:10]:  # Limit to 10 most recent
            concalls.append({
                "title": concall.title,
                "date": concall.date,
                "doc_type": concall.doc_type,
                "quarter": concall.quarter,
                "year": concall.year,
                "url": concall.url
            })
        
        # Analysis summary
        analysis = {
            "company_name": company_data.company_name,
            "symbol": symbol,
            "total_concalls": len(company_data.concalls),
            "total_annual_reports": len(company_data.annual_reports),
            "recent_concalls": concalls,
            "annual_reports": company_data.annual_reports[:3],  # Top 3
            "document_types": {},
            "latest_quarter": None,
            "reporting_frequency": "quarterly" if len(concalls) >= 4 else "irregular"
        }
        
        # Document type analysis
        doc_types = {}
        for concall in concalls:
            doc_type = concall.get('doc_type', 'unknown')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        analysis["document_types"] = doc_types
        
        # Latest quarter info
        if concalls:
            latest = concalls[0]
            if latest.get('quarter') and latest.get('year'):
                analysis["latest_quarter"] = f"{latest['quarter']} {latest['year']}"
        
        return {
            "success": True,
            "analysis_type": "single_company",
            "data": analysis,
            "claude_summary": f"Analysis complete for {company_data.company_name}. Found {len(concalls)} recent concalls and {len(company_data.annual_reports)} annual reports."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-companies")
async def analyze_multiple_companies(request: CompanyAnalysisRequest):
    """
    Analyze multiple companies
    Claude can call: POST /analyze-companies {"companies": ["INFY", "TCS"]}
    """
    try:
        results = {}
        
        for symbol in request.companies:
            try:
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
                
                # Format concalls
                concalls = []
                for concall in company_data.concalls[:request.max_concalls]:
                    concalls.append({
                        "title": concall.title,
                        "date": concall.date,
                        "doc_type": concall.doc_type,
                        "quarter": concall.quarter,
                        "year": concall.year
                    })
                
                results[symbol] = {
                    "company_name": company_data.company_name,
                    "total_concalls": len(company_data.concalls),
                    "total_annual_reports": len(company_data.annual_reports),
                    "recent_concalls": concalls,
                    "annual_reports": company_data.annual_reports[:request.max_annual_reports],
                    "latest_quarter": concalls[0].get('quarter', 'Unknown') + " " + str(concalls[0].get('year', '')) if concalls else "Unknown"
                }
                
            except Exception as e:
                results[symbol] = {"error": str(e)}
        
        return {
            "success": True,
            "analysis_type": "multiple_companies",
            "companies_analyzed": len(results),
            "data": results,
            "claude_summary": f"Analysis complete for {len(results)} companies: {', '.join(results.keys())}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/compare")
async def compare_companies(
    companies: List[str] = Query(..., description="Company symbols to compare"),
    metric: str = Query("concalls", description="Metric to compare: concalls, reports, activity")
):
    """
    Compare companies on specific metrics
    Claude can call: GET /compare?companies=INFY&companies=TCS&metric=concalls
    """
    try:
        comparison_data = {}
        
        for symbol in companies:
            company_url = scraper.find_company_by_symbol(symbol)
            if not company_url:
                comparison_data[symbol] = {"error": "Company not found"}
                continue
            
            company_data = scraper.extract_concall_data(company_url)
            if not company_data:
                comparison_data[symbol] = {"error": "No data found"}
                continue
            
            # Calculate metrics
            total_concalls = len(company_data.concalls)
            total_reports = len(company_data.annual_reports)
            
            # Recent activity (last 12 months)
            recent_activity = len([c for c in company_data.concalls if c.year and c.year >= 2023])
            
            comparison_data[symbol] = {
                "company_name": company_data.company_name,
                "total_concalls": total_concalls,
                "total_annual_reports": total_reports,
                "recent_activity": recent_activity,
                "activity_score": recent_activity * 2 + total_reports,  # Weighted score
                "latest_quarter": (str(company_data.concalls[0].quarter or "Unknown") + " " + str(company_data.concalls[0].year or "")) if company_data.concalls else "Unknown"
            }
        
        # Ranking
        if metric == "concalls":
            ranked = sorted(comparison_data.items(), key=lambda x: x[1].get("total_concalls", 0), reverse=True)
        elif metric == "reports":
            ranked = sorted(comparison_data.items(), key=lambda x: x[1].get("total_annual_reports", 0), reverse=True)
        else:  # activity
            ranked = sorted(comparison_data.items(), key=lambda x: x[1].get("activity_score", 0), reverse=True)
        
        return {
            "success": True,
            "analysis_type": "comparison",
            "comparison_metric": metric,
            "companies": comparison_data,
            "ranking": [{"rank": i+1, "symbol": symbol, "score": data.get(f"total_{metric}", data.get("activity_score", 0))} 
                       for i, (symbol, data) in enumerate(ranked) if "error" not in data],
            "claude_summary": f"Comparison complete. Top performer by {metric}: {ranked[0][0] if ranked else 'None'}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sector/{sector_name}")
async def analyze_sector(sector_name: str):
    """
    Analyze entire sectors
    Claude can call: GET /sector/it or /sector/banking
    """
    sector_mapping = {
        "it": ["INFY", "TCS", "WIPRO", "HCLT", "TECHM"],
        "banking": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK"],
        "auto": ["MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO", "EICHERMOT"],
        "pharma": ["SUNPHARMA", "DRREDDY", "CIPLA", "LUPIN", "AUROPHARMA"],
        "fmcg": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "DABUR"],
        "energy": ["RELIANCE", "ONGC", "NTPC", "POWERGRID", "COALINDIA"]
    }
    
    if sector_name.lower() not in sector_mapping:
        raise HTTPException(status_code=404, detail=f"Sector {sector_name} not supported. Available: {list(sector_mapping.keys())}")
    
    companies = sector_mapping[sector_name.lower()]
    
    # Use the analyze_multiple_companies logic
    request = CompanyAnalysisRequest(companies=companies, analysis_type="sector")
    result = await analyze_multiple_companies(request)
    
    # Add sector-specific analysis
    result["analysis_type"] = "sector_analysis"
    result["sector"] = sector_name.upper()
    result["claude_summary"] = f"Sector analysis complete for {sector_name.upper()}. Analyzed {len(companies)} companies."
    
    return result

@app.get("/claude-instructions")
async def claude_instructions():
    """
    Get instructions for Claude Desktop usage
    """
    return {
        "instructions": "Claude Desktop can call these endpoints directly using the ngrok URL",
        "examples": [
            {
                "description": "Analyze single company",
                "url": "GET /analyze/INFY",
                "claude_usage": "I'll analyze Infosys for you by calling the API endpoint."
            },
            {
                "description": "Compare companies",
                "url": "GET /compare?companies=INFY&companies=TCS",
                "claude_usage": "I'll compare Infosys and TCS by calling the comparison endpoint."
            },
            {
                "description": "Analyze IT sector",
                "url": "GET /sector/it",
                "claude_usage": "I'll analyze the entire IT sector including top companies."
            },
            {
                "description": "Analyze multiple companies",
                "url": "POST /analyze-companies",
                "body": {"companies": ["INFY", "TCS", "WIPRO"]},
                "claude_usage": "I'll analyze multiple companies with detailed comparison."
            }
        ],
        "claude_workflow": [
            "1. Claude receives user request about stocks",
            "2. Claude identifies relevant API endpoint",
            "3. Claude makes HTTP request to ngrok URL",
            "4. Claude receives structured data",
            "5. Claude provides analysis and insights"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {
        "status": "healthy",
        "service": "claude-desktop-stock-api",
        "deployment": "railway",
        "timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)