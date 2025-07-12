# Claude Desktop Integration - Ready to Use! 🚀

## Quick Start for Claude Desktop

### 1. Available Functions

Copy and paste these functions directly into Claude Desktop:

```python
# Import the functions
from claude_functions import *

# Single company analysis
analyze_single_company("INFY")

# Compare multiple companies
compare_companies(["INFY", "TCS", "WIPRO"])

# Sector analysis
analyze_it_sector()
analyze_banking_sector()
analyze_auto_sector()
analyze_pharma_sector()

# Custom analysis
custom_analysis(["RELIANCE", "ADANIPORTS", "BHARTIARTL"])
```

### 2. Claude Desktop Usage Examples

#### Example 1: Ask Claude to analyze a company
**You:** "Can you analyze Infosys's recent financial reports?"

**Claude:** I'll analyze Infosys's latest reports for you.

```python
result = analyze_single_company("INFY")
print(result)
```

#### Example 2: Compare IT companies
**You:** "Compare the performance of major Indian IT companies"

**Claude:** I'll compare the top IT companies.

```python
result = analyze_it_sector()
print(result)
```

#### Example 3: Custom sector analysis
**You:** "Analyze Reliance and Adani Ports"

**Claude:** I'll analyze both companies for you.

```python
result = custom_analysis(["RELIANCE", "ADANIPORTS"])
print(result)
```

### 3. Available Company Symbols

Common symbols you can use:
- **IT**: INFY, TCS, WIPRO, HCLT, TECHM
- **Banking**: HDFCBANK, ICICIBANK, SBIN, AXISBANK, KOTAKBANK
- **Auto**: MARUTI, TATAMOTORS, M&M, BAJAJ-AUTO, EICHERMOT
- **Pharma**: SUNPHARMA, DRREDDY, CIPLA, LUPIN, AUROPHARMA
- **Others**: RELIANCE, ADANIPORTS, BHARTIARTL, ITC, HINDUNILVR

### 4. What Claude Can Do With This Data

- **Earnings Analysis**: Compare quarterly results
- **Growth Trends**: Identify growth patterns
- **Document Analysis**: Analyze concall transcripts
- **Sector Comparison**: Compare companies within sectors
- **Investment Insights**: Provide investment recommendations
- **Risk Assessment**: Identify potential risks

### 5. Troubleshooting

If you get connection errors:
1. Make sure the API is running: `./start_claude_desktop.sh`
2. Check the ngrok URL in `claude_functions.py`
3. Restart if needed: `./stop_claude_desktop.sh && ./start_claude_desktop.sh`

## You're All Set! 🎯

Your enhanced scraper is now fully integrated with Claude Desktop and ready for intelligent financial analysis.