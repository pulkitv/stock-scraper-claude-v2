"""
Claude Desktop Tool for Company Analysis
"""

import requests
import json
from typing import List, Dict, Any

class ClaudeDesktopTool:
    def __init__(self, ngrok_url: str):
        self.api_url = ngrok_url
        self.session = requests.Session()
    
    def analyze_companies(self, companies: List[str]) -> str:
        """
        Main function for Claude Desktop to analyze companies
        Returns formatted analysis as string
        """
        try:
            # Make API request
            response = self.session.post(
                f"{self.api_url}/analyze-companies",
                json={"companies": companies},
                timeout=60
            )
            
            if response.status_code != 200:
                return f"❌ API Error: {response.status_code} - {response.text}"
            
            data = response.json()
            
            if not data.get("success"):
                return "❌ Analysis failed"
            
            # Format results for Claude
            return self._format_for_claude(data["results"])
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def _format_for_claude(self, results: Dict[str, Any]) -> str:
        """Format results for Claude Desktop"""
        
        output = "📊 COMPANY ANALYSIS RESULTS\n"
        output += "=" * 50 + "\n\n"
        
        for symbol, data in results.items():
            if "error" in data:
                output += f"❌ {symbol}: {data['error']}\n\n"
                continue
            
            company_name = data.get("company_name", "Unknown")
            output += f"🏢 {company_name} ({symbol})\n"
            output += "-" * 30 + "\n"
            
            # Concalls summary
            concalls = data.get("concalls", [])
            output += f"📞 Recent Concalls: {len(concalls)}\n"
            
            # Show latest 3 concalls
            for i, concall in enumerate(concalls[:3]):
                output += f"   {i+1}. {concall.get('title', 'Untitled')}\n"
                output += f"      Date: {concall.get('date', 'Unknown')}\n"
                output += f"      Type: {concall.get('doc_type', 'Unknown')}\n"
                if concall.get('quarter') and concall.get('year'):
                    output += f"      Quarter: {concall['quarter']} {concall['year']}\n"
                output += "\n"
            
            # Annual reports
            annual_reports = data.get("annual_reports", [])
            output += f"📋 Annual Reports: {len(annual_reports)}\n"
            
            # Document types summary
            doc_types = {}
            for concall in concalls:
                doc_type = concall.get('doc_type', 'unknown')
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            if doc_types:
                output += f"📊 Document Types: {', '.join([f'{k}: {v}' for k, v in doc_types.items()])}\n"
            
            output += "\n"
        
        return output

# Function that Claude Desktop can call directly
def get_company_analysis(companies: List[str], ngrok_url: str) -> str:
    """
    Direct function for Claude Desktop
    
    Usage: get_company_analysis(["INFY", "TCS"], "https://your-ngrok-url.ngrok.io")
    """
    tool = ClaudeDesktopTool(ngrok_url)
    return tool.analyze_companies(companies)

# Test function
def test_claude_desktop_integration():
    """Test the integration"""
    print("🧪 Testing Claude Desktop Integration...")
    
    # Replace with your actual ngrok URL
    ngrok_url = "https://0f9d55ea7296.ngrok-free.app"
    
    # Test health check
    try:
        response = requests.get(f"{ngrok_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ API is healthy")
            
            # Test analysis
            result = get_company_analysis(["INFY"], ngrok_url)
            print(result)
        else:
            print("❌ API health check failed")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("Make sure ngrok is running and API is started")

if __name__ == "__main__":
    test_claude_desktop_integration()