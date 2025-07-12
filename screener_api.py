#!/usr/bin/env python3
"""
FastAPI Web Service for Enhanced Screener Integration with Claude
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json
import os
from datetime import datetime
import uuid
from screener_scraper import EnhancedScreenerScraper
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enhanced Screener API",
    description="API for fetching company reports and financial documents",
    version="1.0.0"
)

# CORS middleware for Claude integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage for jobs and results
jobs_db = {}
results_cache = {}

# Pydantic models
class CompanyRequest(BaseModel):
    symbols: List[str]
    doc_types: Optional[Dict[str, bool]] = {
        "concalls": True,
        "annual_reports": True,
        "transcripts": True,
        "presentations": True
    }
    delay: Optional[int] = 2

class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed
    progress: float
    message: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class CompanyData(BaseModel):
    company_name: str
    symbol: str
    company_url: str
    concalls: List[Dict[str, Any]]
    annual_reports: List[Dict[str, Any]]
    last_updated: datetime

class DocumentResponse(BaseModel):
    job_id: str
    status: str
    companies: List[CompanyData]
    total_documents: int
    download_urls: List[str]

# Initialize scraper
scraper = EnhancedScreenerScraper(delay=2)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Enhanced Screener API is running",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "services": {
            "scraper": "operational",
            "api": "operational"
        }
    }

@app.post("/fetch-company-data", response_model=Dict[str, str])
async def fetch_company_data(request: CompanyRequest, background_tasks: BackgroundTasks):
    """
    Fetch company data for given symbols
    Returns job_id for tracking progress
    """
    job_id = str(uuid.uuid4())
    
    # Initialize job
    jobs_db[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        progress=0.0,
        message="Job queued",
        started_at=datetime.now()
    )
    
    # Start background task
    background_tasks.add_task(
        process_company_data,
        job_id,
        request.symbols,
        request.doc_types or {
            "concalls": True,
            "annual_reports": True,
            "transcripts": True,
            "presentations": True
        },
        request.delay or 2
    )
    
    return {"job_id": job_id, "status": "queued"}

@app.get("/job-status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get job status and progress"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs_db[job_id]

@app.get("/company-reports/{job_id}")
async def get_company_reports(job_id: str):
    """Get completed company reports"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    
    if job.status != "completed":
        raise HTTPException(status_code=400, detail=f"Job status: {job.status}")
    
    return job.results

@app.get("/download-documents/{job_id}")
async def download_documents(job_id: str, background_tasks: BackgroundTasks):
    """Start document download process"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Company data not ready")
    
    # Start download process
    download_job_id = f"{job_id}_download"
    
    jobs_db[download_job_id] = JobStatus(
        job_id=download_job_id,
        status="pending",
        progress=0.0,
        message="Download queued",
        started_at=datetime.now()
    )
    
    background_tasks.add_task(
        download_company_documents,
        download_job_id,
        job.results
    )
    
    return {"download_job_id": download_job_id, "status": "queued"}

@app.get("/list-downloaded-files/{company_symbol}")
async def list_downloaded_files(company_symbol: str):
    """List all downloaded files for a company"""
    download_dir = os.path.join(os.getcwd(), 'downloads', company_symbol)
    
    if not os.path.exists(download_dir):
        return {"files": [], "total": 0}
    
    files = []
    for filename in os.listdir(download_dir):
        if filename.endswith(('.pdf', '.ppt', '.doc', '.docx')):
            file_path = os.path.join(download_dir, filename)
            stat = os.stat(file_path)
            
            files.append({
                "filename": filename,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "path": file_path
            })
    
    files.sort(key=lambda x: x["modified"], reverse=True)
    return {"files": files, "total": len(files)}

@app.get("/search-companies/{query}")
async def search_companies(query: str):
    """Search for companies by name or symbol"""
    try:
        # Try to find company by symbol
        company_url = scraper.find_company_by_symbol(query)
        
        if company_url:
            # Extract basic info
            response = scraper._make_request(company_url)
            if response:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                h1_tag = soup.find('h1')
                company_name = h1_tag.get_text(strip=True) if h1_tag else "Unknown"
                
                return {
                    "found": True,
                    "company": {
                        "name": company_name,
                        "symbol": query.upper(),
                        "url": company_url
                    }
                }
        
        return {"found": False, "message": f"Company '{query}' not found"}
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

async def process_company_data(job_id: str, symbols: List[str], doc_types: Dict[str, bool], delay: int):
    """Background task to process company data"""
    job = jobs_db[job_id]
    
    try:
        job.status = "running"
        job.message = "Processing companies"
        
        results = {}
        total_companies = len(symbols)
        
        for i, symbol in enumerate(symbols):
            try:
                job.progress = (i / total_companies) * 100
                job.message = f"Processing {symbol} ({i+1}/{total_companies})"
                
                # Find company
                company_url = scraper.find_company_by_symbol(symbol)
                if not company_url:
                    logger.warning(f"Company not found: {symbol}")
                    continue
                
                # Extract data
                company_data = scraper.extract_concall_data(company_url)
                if not company_data:
                    logger.warning(f"No data extracted for: {symbol}")
                    continue
                
                # Convert to serializable format
                concalls = []
                for concall in company_data.concalls:
                    concalls.append({
                        "title": concall.title,
                        "url": concall.url,
                        "doc_type": concall.doc_type,
                        "date": concall.date,
                        "parsed_date": concall.parsed_date.isoformat() if concall.parsed_date else None,
                        "quarter": concall.quarter,
                        "year": concall.year
                    })
                
                results[symbol] = {
                    "company_name": company_data.company_name,
                    "symbol": company_data.symbol,
                    "company_url": company_data.company_url,
                    "concalls": concalls,
                    "annual_reports": company_data.annual_reports,
                    "last_updated": datetime.now().isoformat()
                }
                
                logger.info(f"Successfully processed: {symbol}")
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                continue
        
        job.status = "completed"
        job.progress = 100.0
        job.message = f"Completed processing {len(results)} companies"
        job.completed_at = datetime.now()
        job.results = results
        
        # Cache results
        results_cache[job_id] = results
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.message = f"Job failed: {str(e)}"
        job.completed_at = datetime.now()
        logger.error(f"Job {job_id} failed: {str(e)}")

async def download_company_documents(job_id: str, company_results: Dict[str, Any]):
    """Background task to download documents"""
    job = jobs_db[job_id]
    
    try:
        job.status = "running"
        job.message = "Starting downloads"
        
        download_results = {}
        total_companies = len(company_results)
        
        for i, (symbol, data) in enumerate(company_results.items()):
            try:
                job.progress = (i / total_companies) * 100
                job.message = f"Downloading {symbol} documents ({i+1}/{total_companies})"
                
                download_dir = os.path.join(os.getcwd(), 'downloads', symbol)
                os.makedirs(download_dir, exist_ok=True)
                
                downloaded_files = []
                
                # Download concalls (limit to 5 most recent)
                for j, concall in enumerate(data.get('concalls', [])[:5]):
                    filename = scraper.generate_filename(symbol, type('obj', (), concall)(), j)
                    
                    if scraper.download_document(concall['url'], filename, download_dir):
                        downloaded_files.append({
                            "filename": filename,
                            "type": concall['doc_type'],
                            "url": concall['url'],
                            "date": concall['date']
                        })
                
                # Download annual reports (limit to 3 most recent)
                for j, report in enumerate(data.get('annual_reports', [])[:3]):
                    filename = scraper.generate_filename(symbol, type('obj', (), report)(), j+100)
                    
                    if scraper.download_document(report['url'], filename, download_dir):
                        downloaded_files.append({
                            "filename": filename,
                            "type": "annual_report",
                            "url": report['url'],
                            "date": report.get('date', 'unknown')
                        })
                
                download_results[symbol] = {
                    "total_downloaded": len(downloaded_files),
                    "files": downloaded_files,
                    "download_dir": download_dir
                }
                
                logger.info(f"Downloaded {len(downloaded_files)} files for {symbol}")
                
            except Exception as e:
                logger.error(f"Error downloading {symbol}: {str(e)}")
                download_results[symbol] = {
                    "total_downloaded": 0,
                    "files": [],
                    "error": str(e)
                }
        
        job.status = "completed"
        job.progress = 100.0
        job.message = f"Download completed for {len(download_results)} companies"
        job.completed_at = datetime.now()
        job.results = download_results
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.message = f"Download failed: {str(e)}"
        job.completed_at = datetime.now()
        logger.error(f"Download job {job_id} failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)