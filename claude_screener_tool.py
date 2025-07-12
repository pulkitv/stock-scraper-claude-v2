#!/usr/bin/env python3
"""
Claude Tool Integration for Enhanced Screener
MCP-style tool functions for Claude to access company reports
"""

import json
import requests
import time
from typing import Dict, List, Optional, Any
import asyncio
import os
from datetime import datetime

class ScreenerTool:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        
    def health_check(self) -> Dict[str, Any]:
        """Check if the screener API is running"""
        try:
            response = self.session.get(f"{self.api_base_url}/health")
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def search_company(self, query: str) -> Dict[str, Any]:
        """Search for a company by name or symbol"""
        try:
            response = self.session.get(f"{self.api_base_url}/search-companies/{query}")
            return response.json()
        except Exception as e:
            return {"found": False, "error": str(e)}
    
    def fetch_company_reports(self, symbols: List[str], doc_types: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
        """
        Fetch company reports for given symbols
        Returns job tracking information
        """
        if doc_types is None:
            doc_types = {
                "concalls": True,
                "annual_reports": True,
                "transcripts": True,
                "presentations": True
            }
        
        payload = {
            "symbols": symbols,
            "doc_types": doc_types,
            "delay": 2
        }
        
        try:
            response = self.session.post(f"{self.api_base_url}/fetch-company-data", json=payload)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a running job"""
        try:
            response = self.session.get(f"{self.api_base_url}/job-status/{job_id}")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def wait_for_job_completion(self, job_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for job completion with timeout"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_job_status(job_id)
            
            if "error" in status:
                return status
            
            if status.get("status") == "completed":
                return status
            elif status.get("status") == "failed":
                return {"error": status.get("error", "Job failed")}
            
            print(f"Job progress: {status.get('progress', 0):.1f}% - {status.get('message', 'Processing...')}")
            time.sleep(5)
        
        return {"error": "Job timeout"}
    
    def get_company_reports(self, job_id: str) -> Dict[str, Any]:
        """Get completed company reports"""
        try:
            response = self.session.get(f"{self.api_base_url}/company-reports/{job_id}")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def download_documents(self, job_id: str) -> Dict[str, Any]:
        """Start document download process"""
        try:
            response = self.session.get(f"{self.api_base_url}/download-documents/{job_id}")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def list_downloaded_files(self, company_symbol: str) -> Dict[str, Any]:
        """List downloaded files for a company"""
        try:
            response = self.session.get(f"{self.api_base_url}/list-downloaded-files/{company_symbol}")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_company_analysis(self, symbols: List[str], analysis_type: str = "basic") -> Dict[str, Any]:
        """
        High-level function to get company analysis
        Handles the full workflow: fetch -> wait -> analyze
        """
        print(f"🔍 Starting analysis for companies: {', '.join(symbols)}")
        
        # Step 1: Check API health
        health = self.health_check()
        if health.get("status") != "healthy":
            return {"error": "API is not healthy", "details": health}
        
        # Step 2: Fetch company data
        job_response = self.fetch_company_reports(symbols)
        if "error" in job_response:
            return job_response
        
        job_id = job_response.get("job_id")
        if not job_id:
            return {"error": "No job ID received"}
        
        print(f"📊 Job started: {job_id}")
        
        # Step 3: Wait for completion
        completion_status = self.wait_for_job_completion(job_id)
        if "error" in completion_status:
            return completion_status
        
        # Step 4: Get results
        reports = self.get_company_reports(job_id)
        if "error" in reports:
            return reports
        
        # Step 5: Analyze and format results
        analysis = self._analyze_company_data(reports, analysis_type)
        
        return {
            "job_id": job_id,
            "companies": list(reports.keys()),
            "analysis": analysis,
            "raw_data": reports,
            "summary": self._generate_summary(reports)
        }
    
    def _analyze_company_data(self, reports: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """Analyze company data and generate insights"""
        analysis = {}
        
        for symbol, data in reports.items():
            company_analysis = {
                "company_name": data.get("company_name", "Unknown"),
                "symbol": symbol,
                "total_concalls": len(data.get("concalls", [])),
                "total_annual_reports": len(data.get("annual_reports", [])),
                "latest_concall": None,
                "latest_annual_report": None,
                "document_types": {},
                "date_range": {}
            }
            
            # Analyze concalls
            concalls = data.get("concalls", [])
            if concalls:
                company_analysis["latest_concall"] = concalls[0]
                
                # Count document types
                doc_types = {}
                years = []
                for concall in concalls:
                    doc_type = concall.get("doc_type", "unknown")
                    doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                    
                    if concall.get("year"):
                        years.append(concall["year"])
                
                company_analysis["document_types"] = doc_types
                if years:
                    company_analysis["date_range"] = {
                        "from": min(years),
                        "to": max(years)
                    }
            
            # Analyze annual reports
            annual_reports = data.get("annual_reports", [])
            if annual_reports:
                company_analysis["latest_annual_report"] = annual_reports[0]
            
            analysis[symbol] = company_analysis
        
        return analysis
    
    def _generate_summary(self, reports: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the fetched data"""
        total_companies = len(reports)
        total_concalls = sum(len(data.get("concalls", [])) for data in reports.values())
        total_annual_reports = sum(len(data.get("annual_reports", [])) for data in reports.values())
        
        return {
            "total_companies": total_companies,
            "total_concalls": total_concalls,
            "total_annual_reports": total_annual_reports,
            "avg_concalls_per_company": total_concalls / total_companies if total_companies > 0 else 0,
            "avg_annual_reports_per_company": total_annual_reports / total_companies if total_companies > 0 else 0,
            "companies_analyzed": list(reports.keys())
        }

# Claude MCP Tool Functions
def get_company_reports_tool(symbols: List[str], doc_types: Optional[Dict[str, bool]] = None) -> str:
    """
    Tool for Claude to fetch company reports
    
    Args:
        symbols: List of company symbols (e.g., ["AAPL", "MSFT"])
        doc_types: Optional dict specifying which document types to fetch
    
    Returns:
        JSON string with company reports and analysis
    """
    tool = ScreenerTool()
    
    try:
        result = tool.get_company_analysis(symbols, "comprehensive")
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})

def search_company_tool(query: str) -> str:
    """
    Tool for Claude to search for companies
    
    Args:
        query: Company name or symbol to search for
    
    Returns:
        JSON string with search results
    """
    tool = ScreenerTool()
    
    try:
        result = tool.search_company(query)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

def list_company_files_tool(company_symbol: str) -> str:
    """
    Tool for Claude to list downloaded files for a company
    
    Args:
        company_symbol: Company symbol (e.g., "AAPL")
    
    Returns:
        JSON string with list of downloaded files
    """
    tool = ScreenerTool()
    
    try:
        result = tool.list_downloaded_files(company_symbol)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})

def analyze_company_trends_tool(symbols: List[str], analysis_focus: str = "earnings") -> str:
    """
    Tool for Claude to analyze company trends
    
    Args:
        symbols: List of company symbols
        analysis_focus: Focus area (earnings, growth, performance)
    
    Returns:
        JSON string with trend analysis
    """
    tool = ScreenerTool()
    
    try:
        # Get company data
        result = tool.get_company_analysis(symbols, "comprehensive")
        
        if "error" in result:
            return json.dumps(result)
        
        # Generate trend analysis
        trend_analysis = {}
        
        for symbol in symbols:
            if symbol in result.get("raw_data", {}):
                company_data = result["raw_data"][symbol]
                concalls = company_data.get("concalls", [])
                
                # Analyze trends based on concall frequency and types
                quarterly_data = {}
                for concall in concalls:
                    if concall.get("quarter") and concall.get("year"):
                        key = f"{concall['quarter']}-{concall['year']}"
                        quarterly_data[key] = quarterly_data.get(key, 0) + 1
                
                trend_analysis[symbol] = {
                    "company_name": company_data.get("company_name"),
                    "reporting_frequency": len(quarterly_data),
                    "latest_quarter": max(quarterly_data.keys()) if quarterly_data else None,
                    "document_availability": {
                        "transcripts": len([c for c in concalls if c.get("doc_type") == "transcript"]),
                        "presentations": len([c for c in concalls if c.get("doc_type") == "presentation"]),
                        "recordings": len([c for c in concalls if c.get("doc_type") == "recording"])
                    }
                }
        
        return json.dumps({
            "analysis_focus": analysis_focus,
            "trend_analysis": trend_analysis,
            "summary": result.get("summary", {})
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})

# Example usage for testing
if __name__ == "__main__":
    # Test the tool
    tool = ScreenerTool()
    
    # Test search
    print("Testing search...")
    search_result = tool.search_company("INFY")
    print(json.dumps(search_result, indent=2))
    
    # Test comprehensive analysis
    print("\nTesting comprehensive analysis...")
    analysis = tool.get_company_analysis(["INFY"], "comprehensive")
    print(json.dumps(analysis, indent=2, default=str))