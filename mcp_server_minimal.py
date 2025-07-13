#!/usr/bin/env python3
"""
MCP Server for Stock Scraper - Minimal Compatible Version
"""

import asyncio
import json
import logging
import sys
import os
from typing import Any, Dict, List

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

print("Starting MCP Server...", file=sys.stderr)

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    from mcp.server.stdio import stdio_server
    from screener_scraper import EnhancedScreenerScraper
    print("All imports successful", file=sys.stderr)
except Exception as e:
    print(f"Import error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

# Create server
server = Server("stock-scraper")

# Initialize scraper
try:
    scraper = EnhancedScreenerScraper(delay=2)
    print("Scraper initialized", file=sys.stderr)
except Exception as e:
    print(f"Scraper initialization failed: {e}", file=sys.stderr)
    sys.exit(1)

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    print("Listing tools...", file=sys.stderr)
    return [
        Tool(
            name="find_company_by_symbol",
            description="Find a company by its stock symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Company stock symbol (e.g., RELIANCE, INFY)"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="scrape_company_data",
            description="Get comprehensive company data including documents and PDFs",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Company stock symbol (e.g., RELIANCE, INFY)"
                    },
                    "download_docs": {
                        "type": "boolean",
                        "description": "Whether to download documents",
                        "default": False
                    }
                },
                "required": ["symbol"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    print(f"Tool called: {name} with {arguments}", file=sys.stderr)
    
    try:
        if name == "find_company_by_symbol":
            symbol = arguments.get("symbol", "").upper()
            print(f"Finding company: {symbol}", file=sys.stderr)
            
            result = scraper.find_company_by_symbol(symbol)
            if not result:
                return [TextContent(type="text", text=f"No company found for symbol: {symbol}")]
            
            response = f"Company found for symbol '{symbol}':\n\nCompany URL: {result}\n"
            return [TextContent(type="text", text=response)]
        
        elif name == "scrape_company_data":
            symbol = arguments.get("symbol", "").upper()
            download_docs = arguments.get("download_docs", False)
            print(f"Scraping data for: {symbol}", file=sys.stderr)
            
            result = scraper.scrape_company_data(symbol, download_docs=download_docs)
            if not result:
                return [TextContent(type="text", text=f"No data found for symbol: {symbol}")]
            
            response = f"Company data for symbol '{symbol}':\n\n"
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, list) and value:
                        response += f"## {key.replace('_', ' ').title()} ({len(value)} items)\n"
                        for i, item in enumerate(value[:3], 1):  # Show first 3 items
                            if isinstance(item, dict):
                                title = item.get('title', item.get('name', 'Unknown'))
                                response += f"{i}. {title}\n"
                                if item.get('date'):
                                    response += f"   Date: {item['date']}\n"
                            else:
                                response += f"{i}. {str(item)}\n"
                        if len(value) > 3:
                            response += f"   ... and {len(value) - 3} more items\n"
                        response += "\n"
                    elif not isinstance(value, list):
                        response += f"**{key.replace('_', ' ').title()}**: {value}\n"
            else:
                response += f"Result: {str(result)}\n"
            
            return [TextContent(type="text", text=response)]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        print(f"Error in tool {name}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    """Main function"""
    print("Starting server...", file=sys.stderr)
    try:
        async with stdio_server() as (read_stream, write_stream):
            print("Server streams created", file=sys.stderr)
            await server.run(read_stream, write_stream)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped", file=sys.stderr)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)