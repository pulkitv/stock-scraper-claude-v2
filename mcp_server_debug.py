#!/usr/bin/env python3
"""
MCP Server for Stock Scraper Integration with Claude Desktop (stdio version with debug)
"""

import asyncio
import json
import logging
import sys
import os
import traceback
from typing import Any, Dict, List, Optional

# Enhanced logging to stderr for Claude Desktop debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),  # This will show in Claude Desktop logs
        logging.FileHandler('/tmp/mcp_server_debug.log')  # Also log to file
    ]
)
logger = logging.getLogger(__name__)

# Debug: Print to stderr immediately
print("MCP Server starting...", file=sys.stderr)
print(f"Python version: {sys.version}", file=sys.stderr)
print(f"Working directory: {os.getcwd()}", file=sys.stderr)

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    from mcp.server.stdio import stdio_server
    print("MCP imports successful", file=sys.stderr)
except Exception as e:
    print(f"MCP import error: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

try:
    from screener_scraper import EnhancedScreenerScraper
    print("Scraper import successful", file=sys.stderr)
except Exception as e:
    print(f"Scraper import error: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

from datetime import datetime

logger.info("All imports successful")

# Create server instance
server = Server("stock-scraper")
print("Server instance created", file=sys.stderr)

# Initialize scraper
try:
    scraper = EnhancedScreenerScraper(delay=2)
    logger.info("Scraper initialized successfully")
    print("Scraper initialized successfully", file=sys.stderr)
except Exception as e:
    logger.error(f"Failed to initialize scraper: {e}")
    print(f"Failed to initialize scraper: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    logger.info("list_tools called")
    print("list_tools called", file=sys.stderr)
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
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    print(f"Tool called: {name} with arguments: {arguments}", file=sys.stderr)
    
    try:
        if name == "find_company_by_symbol":
            return await find_company_by_symbol_handler(arguments)
        elif name == "scrape_company_data":
            return await scrape_company_data_handler(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        print(f"Error in tool {name}: {str(e)}", file=sys.stderr)
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def find_company_by_symbol_handler(arguments: Dict[str, Any]) -> List[TextContent]:
    """Find a company by symbol"""
    symbol = arguments.get("symbol", "").upper()
    logger.info(f"Finding company by symbol: {symbol}")
    
    try:
        result = scraper.find_company_by_symbol(symbol)
        
        if not result:
            return [TextContent(
                type="text",
                text=f"No company found for symbol: {symbol}"
            )]
        
        response = f"Company found for symbol '{symbol}':\n\nCompany URL: {result}\n"
        return [TextContent(type="text", text=response)]
    except Exception as e:
        logger.error(f"Error finding company by symbol: {e}")
        return [TextContent(type="text", text=f"Error finding company by symbol: {str(e)}")]

async def scrape_company_data_handler(arguments: Dict[str, Any]) -> List[TextContent]:
    """Scrape company data"""
    symbol = arguments.get("symbol", "").upper()
    download_docs = arguments.get("download_docs", False)
    logger.info(f"Scraping company data for symbol: {symbol}")
    
    try:
        result = scraper.scrape_company_data(symbol, download_docs=download_docs)
        
        if not result:
            return [TextContent(
                type="text",
                text=f"No data found for symbol: {symbol}"
            )]
        
        response = f"Company data for symbol '{symbol}':\n\n{str(result)}\n"
        return [TextContent(type="text", text=response)]
    except Exception as e:
        logger.error(f"Error scraping company data: {e}")
        return [TextContent(type="text", text=f"Error scraping company data: {str(e)}")]

def main():
    """Main function to run the MCP server"""
    logger.info("Starting Stock Scraper MCP Server...")
    print("Starting Stock Scraper MCP Server...", file=sys.stderr)
    
    try:
        async def run_server():
            try:
                print("Creating stdio server...", file=sys.stderr)
                async with stdio_server() as (read_stream, write_stream):
                    logger.info("Server streams created successfully")
                    print("Server streams created successfully", file=sys.stderr)
                    await server.run(read_stream, write_stream, initialization_options=None)
            except Exception as e:
                logger.error(f"Error in server run: {e}")
                print(f"Error in server run: {e}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                raise
        
        asyncio.run(run_server())
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        print("Server stopped by user", file=sys.stderr)
    except Exception as e:
        logger.error(f"Server error: {e}")
        print(f"Server error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    print("Script starting...", file=sys.stderr)
    main()