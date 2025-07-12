
# Claude Integration Instructions

## Setup Complete! 🎉

Your Enhanced Screener is now ready for Claude integration.

## Quick Start:

1. **Start the API server:**
   ```bash
   ./start_api.sh
   ```

2. **Test the API:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Use with Claude:**
   Claude can now call these functions:
   - `get_company_reports_tool(symbols)` - Fetch company reports
   - `search_company_tool(query)` - Search for companies
   - `list_company_files_tool(symbol)` - List downloaded files
   - `analyze_company_trends_tool(symbols, focus)` - Analyze trends

## Example Claude Usage:

**Claude:** "Can you analyze the latest earnings reports for Apple and Microsoft?"

**You:** Use the tool: `get_company_reports_tool(["AAPL", "MSFT"])`

**Claude:** Will fetch the data and provide analysis based on the reports.

## API Endpoints:

- **Health Check:** http://localhost:8000/health
- **API Docs:** http://localhost:8000/docs
- **Search Company:** http://localhost:8000/search-companies/{query}
- **Fetch Reports:** POST http://localhost:8000/fetch-company-data

## Tool Functions for Claude:

```python
# In your Claude conversation, you can use:
from claude_screener_tool import get_company_reports_tool

# Fetch reports for companies
result = get_company_reports_tool(["INFY", "TCS"])

# Search for a company
result = search_company_tool("Infosys")

# List downloaded files
result = list_company_files_tool("INFY")
```

## Configuration:

Edit `claude_config.json` to customize:
- API settings (host, port)
- Scraper settings (delays, limits)
- Claude integration settings

## Troubleshooting:

1. **API not starting:** Check if port 8000 is available
2. **Permission errors:** Run `chmod +x *.sh` to make scripts executable
3. **Module errors:** Ensure all dependencies are installed in your virtual environment

## Next Steps:

1. Test the API with a simple company search
2. Try fetching reports for a known company (like INFY)
3. Integrate with your Claude workflow
4. Customize the analysis functions for your needs

## Support:

- API logs are available in the console
- Check `api.pid` file for server status
- Use `./stop_api.sh` to cleanly shutdown

Happy analyzing! 📊
