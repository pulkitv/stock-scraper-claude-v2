#!/usr/bin/env python3
"""
Manual MCP Server for Stock Scraper - Fixed with Output Redirection
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict, List
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Starting Manual MCP Server...", file=sys.stderr)

try:
    from screener_scraper import EnhancedScreenerScraper
    print("Scraper import successful", file=sys.stderr)
except Exception as e:
    print(f"Scraper import error: {e}", file=sys.stderr)
    sys.exit(1)

# Initialize scraper
try:
    scraper = EnhancedScreenerScraper(delay=2)
    print("Scraper initialized", file=sys.stderr)
except Exception as e:
    print(f"Scraper initialization failed: {e}", file=sys.stderr)
    sys.exit(1)

class ManualMCPServer:
    def __init__(self):
        self.tools = [
            {
                "name": "find_company_by_symbol",
                "description": "Find a company by its stock symbol",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Company stock symbol (e.g., RELIANCE, INFY)"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "scrape_company_data",
                "description": "Get comprehensive company data including documents and PDFs",
                "inputSchema": {
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
            }
        ]
    
    def handle_initialize(self, params):
        """Handle initialization request"""
        print(f"Initialize request: {params}", file=sys.stderr)
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "stock-scraper",
                "version": "1.0.0"
            }
        }
    
    def handle_notification(self, method, params):
        """Handle notification (no response needed)"""
        print(f"Notification: {method} with {params}", file=sys.stderr)
        return None
    
    def handle_list_tools(self):
        """Handle list tools request"""
        print("List tools request", file=sys.stderr)
        return {"tools": self.tools}
    
    def handle_list_resources(self):
        """Handle list resources request"""
        print("List resources request", file=sys.stderr)
        return {"resources": []}
    
    def handle_list_prompts(self):
        """Handle list prompts request"""
        print("List prompts request", file=sys.stderr)
        return {"prompts": []}
    
    def handle_call_tool(self, params):
        """Handle tool call request"""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        print(f"Tool call: {name} with {arguments}", file=sys.stderr)
        
        try:
            if name == "find_company_by_symbol":
                symbol = arguments.get("symbol", "").upper()
                print(f"Finding company: {symbol}", file=sys.stderr)
                
                # Redirect stdout to prevent interference with JSON-RPC
                with redirect_stdout(StringIO()) as captured_output:
                    result = scraper.find_company_by_symbol(symbol)
                
                # Log captured output to stderr
                captured = captured_output.getvalue()
                if captured:
                    print(f"Scraper output: {captured}", file=sys.stderr)
                
                if not result:
                    content = f"No company found for symbol: {symbol}"
                else:
                    content = f"Company found for symbol '{symbol}':\n\nCompany URL: {result}\n"
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": content
                        }
                    ]
                }
            
            elif name == "scrape_company_data":
                symbol = arguments.get("symbol", "").upper()
                download_docs = arguments.get("download_docs", False)
                print(f"Scraping data for: {symbol}", file=sys.stderr)
                
                # Redirect stdout to prevent interference with JSON-RPC
                with redirect_stdout(StringIO()) as captured_output:
                    result = scraper.scrape_company_data(symbol, download_docs=download_docs)
                
                # Log captured output to stderr
                captured = captured_output.getvalue()
                if captured:
                    print(f"Scraper output: {captured}", file=sys.stderr)
                
                if not result:
                    content = f"No data found for symbol: {symbol}"
                else:
                    content = f"Company data for symbol '{symbol}':\n\n"
                    if isinstance(result, dict):
                        for key, value in result.items():
                            if isinstance(value, list) and value:
                                content += f"## {key.replace('_', ' ').title()} ({len(value)} items)\n"
                                for i, item in enumerate(value[:3], 1):
                                    if isinstance(item, dict):
                                        title = item.get('title', item.get('name', 'Unknown'))
                                        content += f"{i}. {title}\n"
                                        if item.get('date'):
                                            content += f"   Date: {item['date']}\n"
                                    else:
                                        content += f"{i}. {str(item)}\n"
                                if len(value) > 3:
                                    content += f"   ... and {len(value) - 3} more items\n"
                                content += "\n"
                            elif not isinstance(value, list):
                                content += f"**{key.replace('_', ' ').title()}**: {value}\n"
                    else:
                        content += f"Result: {str(result)}\n"
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": content
                        }
                    ]
                }
            
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Unknown tool: {name}"
                        }
                    ]
                }
        
        except Exception as e:
            print(f"Error in tool {name}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: {str(e)}"
                    }
                ]
            }
    
    def handle_request(self, request):
        """Handle incoming JSON-RPC request"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            print(f"Handling method: {method}", file=sys.stderr)
            
            # Handle notifications (no response needed)
            if request_id is None:
                if method == "notifications/initialized":
                    self.handle_notification(method, params)
                    return None
                else:
                    print(f"Unknown notification: {method}", file=sys.stderr)
                    return None
            
            # Handle regular requests
            if method == "initialize":
                result = self.handle_initialize(params)
            elif method == "tools/list":
                result = self.handle_list_tools()
            elif method == "resources/list":
                result = self.handle_list_resources()
            elif method == "prompts/list":
                result = self.handle_list_prompts()
            elif method == "tools/call":
                result = self.handle_call_tool(params)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        
        except Exception as e:
            print(f"Error handling request: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

async def main():
    """Main server loop"""
    server = ManualMCPServer()
    print("Manual MCP Server started", file=sys.stderr)
    
    try:
        while True:
            # Read from stdin
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            line = line.strip()
            if not line:
                continue
            
            print(f"Received: {line}", file=sys.stderr)
            
            try:
                request = json.loads(line)
                response = server.handle_request(request)
                
                # Only send response if it's not None
                if response is not None:
                    response_json = json.dumps(response)
                    print(response_json, flush=True)
                    print(f"Sent: {response_json}", file=sys.stderr)
                
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}", file=sys.stderr)
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                print(json.dumps(error_response), flush=True)
    
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