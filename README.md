# Stock Scraper MCP Server

A Model Context Protocol (MCP) server that enables Claude Desktop to scrape Indian stock market data from Screener.in in real-time during conversations.

## 🚀 Features

- **🔍 Company Search**: Find companies by stock symbols (RELIANCE, INFY, TCS, etc.)
- **📊 Comprehensive Data Extraction**: 
  - Company information and financial URLs
  - Conference call documents (transcripts & presentations)
  - Annual reports from BSE
  - Historical document archives with dates
- **📥 Document Download**: Optional PDF download functionality
- **🤖 Claude Integration**: Works seamlessly within Claude Desktop conversations
- **⚡ Real-time Processing**: Live data extraction during chat
- **🛡️ Robust Error Handling**: Graceful handling of network issues and missing data

## 📋 Prerequisites

- **Python 3.8+**
- **Claude Desktop** application
- **macOS** (tested) or Linux
- **Internet connection** for web scraping

## 🛠️ Installation

### 1. Clone and Setup Project

```bash
# Clone the repository
git clone https://github.com/yourusername/stock-scraper-claude-v2.git
cd stock-scraper-claude-v2

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Create Requirements File

```bash
cat > requirements.txt << 'EOF'
requests>=2.28.0
beautifulsoup4>=4.11.0
lxml>=4.9.0
selenium>=4.15.0
webdriver-manager>=4.0.0
python-dateutil>=2.8.0
mcp>=1.0.0
anyio>=3.6.0
EOF
```

### 3. Make Server Script Executable

```bash
chmod +x run_mcp_server.sh
```

### 4. Verify Installation

```bash
# Test the MCP server
python3 mcp_server_final.py
```

## ⚙️ Claude Desktop Configuration

### 1. Locate Config File

The Claude Desktop configuration file is located at:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### 2. Update Configuration

Add the MCP server to your Claude Desktop config:

```json
{
  "mcpServers": {
    "stock-scraper": {
      "command": "/Users/pulkitvashishta/Downloads/stock-scraper-claude-v2/run_mcp_server.sh",
      "cwd": "/Users/pulkitvashishta/Downloads/stock-scraper-claude-v2"
    }
  }
}
```

**⚠️ Important**: Replace the paths with your actual project directory path.

### 3. Alternative Configuration (Direct Python)

```json
{
  "mcpServers": {
    "stock-scraper": {
      "command": "python3",
      "args": ["mcp_server_final.py"],
      "cwd": "/path/to/your/stock-scraper-claude-v2",
      "env": {
        "PATH": "/path/to/your/stock-scraper-claude-v2/.venv/bin:/usr/local/bin:/usr/bin:/bin"
      }
    }
  }
}
```

### 4. Restart Claude Desktop

1. **Completely quit Claude Desktop** (Cmd+Q)
2. **Wait 5 seconds**
3. **Reopen Claude Desktop**
4. **Check Developer Settings** → Look for "stock-scraper" server as "Connected"

## 🎯 Usage Examples

### Basic Company Search
```
User: Can you find the company with symbol RELIANCE?

Claude: I'll search for the company with symbol RELIANCE using the stock scraper.
[Uses find_company_by_symbol tool]

Response: Company found for symbol 'RELIANCE':
Company URL: https://www.screener.in/company/RELIANCE/
```

### Comprehensive Data Analysis
```
User: Get me detailed information about Vodafone Idea including recent concalls

Claude: I'll scrape comprehensive data for IDEA (Vodafone Idea Ltd).
[Uses scrape_company_data tool]

Response: Company data for symbol 'IDEA':

## Concalls (20 items)
1. Jun 2025 - Transcript
   Date: Jun-2025
2. Jun 2025 - PPT
   Date: Jun-2025
3. Apr 2025 - PPT
   Date: Apr-2025
   ... and 17 more items

## Annual Reports (5 items)
1. Financial Year 2024from bse
   Date: FY2024
2. Financial Year 2023from bse
   Date: FY2023
   ... and 3 more items
```

### Document Download
```
User: Scrape company data for TCS with document download enabled

Claude: I'll scrape TCS data and download the documents.
[Uses scrape_company_data with download_docs=true]
```

## 🔧 Available Tools

### 1. `find_company_by_symbol`
- **Description**: Find a company by its stock symbol
- **Parameters**: 
  - `symbol` (string, required): Stock symbol (e.g., "RELIANCE", "INFY")
- **Returns**: Company URL from Screener.in

### 2. `scrape_company_data`
- **Description**: Get comprehensive company data including documents
- **Parameters**:
  - `symbol` (string, required): Stock symbol
  - `download_docs` (boolean, optional): Whether to download PDF documents
- **Returns**: Detailed company information, concall documents, annual reports

## 📁 Project Structure

```
stock-scraper-claude-v2/
├── 📄 mcp_server_final.py       # Main MCP server implementation
├── 🕷️ screener_scraper.py       # Core scraping functionality  
├── 🚀 run_mcp_server.sh         # Server startup script
├── 📋 requirements.txt          # Python dependencies
├── 📖 README.md                 # This documentation
├── 🚫 .gitignore               # Git ignore rules
└── 📁 .venv/                   # Virtual environment
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Server Not Connecting
```bash
# Check if script is executable
ls -la run_mcp_server.sh

# Make executable if needed
chmod +x run_mcp_server.sh

# Test server directly
python3 mcp_server_final.py
```

#### 2. Import Errors
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### 3. JSON Parsing Errors
- Check Claude Desktop logs for specific errors
- Ensure no print statements are going to stdout
- Verify scraper output is redirected to stderr

### Debug Logs

**Claude Desktop logs:**
```bash
tail -f ~/Library/Logs/Claude/main.log
```

**Test scraper independently:**
```bash
python3 -c "
from screener_scraper import EnhancedScreenerScraper
scraper = EnhancedScreenerScraper()
result = scraper.find_company_by_symbol('RELIANCE')
print(result)
"
```

## 🔒 Security & Rate Limiting

- **Respectful Scraping**: Built-in delays between requests
- **Rate Limiting**: 2-second delays to avoid overwhelming servers
- **Error Handling**: Graceful handling of network timeouts
- **Input Validation**: All user inputs are validated and sanitized
- **No Data Storage**: No permanent storage of scraped data

## 📊 Technical Implementation

### MCP Protocol
- **JSON-RPC 2.0**: Manual implementation for maximum compatibility
- **Stdio Communication**: Uses stdin/stdout for Claude Desktop integration
- **Error Handling**: Comprehensive error responses with proper codes
- **Async Support**: Asyncio-based server for better performance

### Web Scraping
- **HTTP Requests**: Uses `requests` library with proper headers
- **HTML Parsing**: BeautifulSoup4 for robust HTML parsing
- **Data Extraction**: Intelligent parsing of financial documents and dates

### Output Management
- **Stdout Redirection**: Prevents scraper output from interfering with JSON-RPC
- **Stderr Logging**: All debug information goes to stderr
- **JSON Formatting**: Proper JSON responses for Claude Desktop

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help

1. **Check the troubleshooting section** above
2. **Review Claude Desktop logs** for specific errors
3. **Test the server independently** to isolate issues
4. **Create an issue** with detailed error logs and steps to reproduce

### Common Support Questions

**Q: Claude Desktop says "Server disconnected"**
A: Check that the script path in `claude_desktop_config.json` is correct and the script is executable.

**Q: "No company found" for valid symbols**
A: The scraper might be rate-limited. Wait a few minutes and try again.

**Q: JSON parsing errors in logs**
A: Ensure the scraper output is properly redirected to stderr, not stdout.

## 🔄 Updates

To update the server:
```bash
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt --upgrade
# Restart Claude Desktop
```

## 🎯 Roadmap

- [ ] **NSE Integration**: Add support for NSE data
- [ ] **Real-time Prices**: Include live stock prices
- [ ] **Financial Ratios**: Extract key financial metrics
- [ ] **Peer Comparison**: Compare companies in the same sector
- [ ] **Alert System**: Set up price and news alerts

---

**⚠️ Disclaimer**: This MCP server is designed for educational and research purposes. Please respect the terms of service of the websites being scraped and implement appropriate rate limiting. Always verify financial information from official sources before making investment decisions.

**🌟 Star this repository** if you find it useful!