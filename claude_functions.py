"""
Ready-to-use functions for Claude Desktop
"""

from claude_desktop_tool import get_company_analysis
import json

# Your ngrok URL (update this when it changes)
NGROK_URL = "https://0f9d55ea7296.ngrok-free.app"

def analyze_single_company(symbol: str) -> str:
    """
    Analyze a single company
    Usage: analyze_single_company("INFY")
    """
    return get_company_analysis([symbol], NGROK_URL)

def compare_companies(symbols: list) -> str:
    """
    Compare multiple companies
    Usage: compare_companies(["INFY", "TCS", "WIPRO"])
    """
    return get_company_analysis(symbols, NGROK_URL)

def analyze_it_sector() -> str:
    """
    Analyze major IT companies
    Usage: analyze_it_sector()
    """
    it_companies = ["INFY", "TCS", "WIPRO", "HCLT", "TECHM"]
    return get_company_analysis(it_companies, NGROK_URL)

def analyze_banking_sector() -> str:
    """
    Analyze major banking companies
    Usage: analyze_banking_sector()
    """
    banking_companies = ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK"]
    return get_company_analysis(banking_companies, NGROK_URL)

def analyze_auto_sector() -> str:
    """
    Analyze major auto companies
    Usage: analyze_auto_sector()
    """
    auto_companies = ["MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO", "EICHERMOT"]
    return get_company_analysis(auto_companies, NGROK_URL)

def analyze_pharma_sector() -> str:
    """
    Analyze major pharma companies
    Usage: analyze_pharma_sector()
    """
    pharma_companies = ["SUNPHARMA", "DRREDDY", "CIPLA", "LUPIN", "AUROPHARMA"]
    return get_company_analysis(pharma_companies, NGROK_URL)

def custom_analysis(companies: list) -> str:
    """
    Custom analysis for any list of companies
    Usage: custom_analysis(["RELIANCE", "ADANIPORTS", "BHARTIARTL"])
    """
    return get_company_analysis(companies, NGROK_URL)

# Test all functions
def test_all_functions():
    """Test all available functions"""
    print("🧪 Testing all Claude Desktop functions...")
    
    # Test single company
    print("\n📊 Testing single company analysis...")
    result = analyze_single_company("INFY")
    print("✅ Single company test passed")
    
    # Test comparison
    print("\n📊 Testing company comparison...")
    result = compare_companies(["INFY", "TCS"])
    print("✅ Company comparison test passed")
    
    # Test sector analysis
    print("\n📊 Testing sector analysis...")
    result = analyze_it_sector()
    print("✅ Sector analysis test passed")
    
    print("\n🎉 All tests passed! Ready for Claude Desktop.")

if __name__ == "__main__":
    test_all_functions()