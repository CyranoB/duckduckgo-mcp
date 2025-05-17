#!/usr/bin/env python3
"""
DuckDuckGo Search MCP Tool

This tool allows searching the web using DuckDuckGo through the MCP (Model Context Protocol) framework.
It can be run using 'mcp run' command.
"""

import json
import requests
import argparse
import sys
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP(name="duckduckgo_search")

def search_duckduckgo(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search DuckDuckGo and return parsed results.
    
    Args:
        query: The search query string
        max_results: Maximum number of results to return
        
    Returns:
        List of dictionaries containing search results with title, url, and snippet
    """
    # Validate parameters
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")
        
    if not isinstance(max_results, int) or max_results <= 0:
        raise ValueError("max_results must be a positive integer")
    
    # Set up headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Format the query for the URL
    formatted_query = query.replace(' ', '+')
    url = f"https://html.duckduckgo.com/html/?q={formatted_query}"
    
    try:
        # Make the request with timeout
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract search results
        results = []
        for result in soup.select('.result'):
            # Extract title, URL, and snippet
            title_element = result.select_one('.result__title')
            url_element = result.select_one('.result__url')
            snippet_element = result.select_one('.result__snippet')
            
            if title_element and url_element and snippet_element:
                title = title_element.get_text(strip=True)
                url = url_element.get_text(strip=True)
                
                # If the URL doesn't start with http, add it
                if not url.startswith(('http://', 'https://')):
                    url = f"https://{url}"
                    
                snippet = snippet_element.get_text(strip=True)
                
                results.append({
                    'title': title,
                    'url': url,
                    'snippet': snippet
                })
                
                if len(results) >= max_results:
                    break
        
        return results
    
    except requests.exceptions.Timeout:
        print(f"Error: Request timed out when accessing {url}")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        return []
    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Request Exception: {e}")
        return []
    except Exception as e:
        print(f"Error during search: {e}")
        return []

@mcp.tool()
def duckduckgo_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search the web using DuckDuckGo.
    
    Args:
        query: The search query
        max_results: Maximum number of search results to return (default: 5)
        
    Returns:
        List of search results with title, URL, and snippet
    """
    # Validate parameters
    if not query:
        raise ValueError("Missing required parameter: query")
    
    try:
        # Validate max_results
        if not isinstance(max_results, int):
            max_results = int(max_results)
            
        if max_results <= 0:
            raise ValueError("max_results must be a positive integer")
    except (ValueError, TypeError):
        raise ValueError("max_results must be a valid positive integer")
    
    # Perform search
    try:
        results = search_duckduckgo(query, max_results)
        
        # Check if we got any results
        if not results:
            print(f"Warning: No results found for query: '{query}'")
            
        # Return results
        return results
    except Exception as e:
        print(f"Error in duckduckgo_search: {str(e)}")
        raise

# Simple Args class for argument parsing
class Args:
    pass

def parse_args():
    """Parse command line arguments"""
    # Check for --cli mode
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        if len(sys.argv) < 3:
            print("Usage: python duckduckgo_search.py --cli <query> [max_results]")
            sys.exit(1)
            
        args = Args()
        args.cli_mode = True
        args.query = sys.argv[2]
        args.max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        return args
    
    # Standard mode (just run the MCP server)
    args = Args()
    args.cli_mode = False
    return args

if __name__ == "__main__":
    args = parse_args()
    
    # Handle CLI mode
    if args.cli_mode:
        results = search_duckduckgo(args.query, args.max_results)
        print(json.dumps(results, indent=2))
    else:
        # Run the MCP server using stdio (default transport)
        mcp.run()