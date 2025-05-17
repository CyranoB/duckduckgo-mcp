#!/usr/bin/env python3
"""
DuckDuckGo Search MCP Tool

This tool allows searching the web using DuckDuckGo through the MCP (Model Context Protocol) framework.
It integrates with the duckduckgo_search library to provide reliable search results.
"""

import sys
import json
import logging
import argparse
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import DuckDuckGoSearchException

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create the MCP server
mcp = FastMCP(name="duckduckgo_search")

def search_duckduckgo(query: str, max_results: int = 5, 
                      safesearch: str = "moderate", region: str = "wt-wt",
                      timeout: int = 15) -> List[Dict[str, str]]:
    """
    Search DuckDuckGo using the duckduckgo_search library and return parsed results.
    
    Args:
        query: The search query string
        max_results: Maximum number of results to return
        safesearch: Safe search setting ('on', 'moderate', 'off')
        region: Region code for localized results (default: wt-wt for no region)
        timeout: Request timeout in seconds
        
    Returns:
        List of dictionaries containing search results with title, url, and snippet
    """
    # Validate parameters
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")
        
    if not isinstance(max_results, int) or max_results <= 0:
        raise ValueError("max_results must be a positive integer")
    
    # Validate safesearch parameter
    valid_safesearch = ["on", "moderate", "off"]
    if safesearch not in valid_safesearch:
        logger.warning(f"Invalid safesearch value: '{safesearch}'. Using 'moderate' instead.")
        safesearch = "moderate"
    
    try:
        # Using the DDGS class from duckduckgo_search package to perform the search
        ddgs = DDGS(timeout=timeout)
        
        # Get search results - the text method returns results in the format we need
        # See: https://github.com/deedy5/duckduckgo_search
        results = ddgs.text(
            keywords=query,
            region=region,
            safesearch=safesearch,
            max_results=max_results,
            backend="lite" if len(query) > 100 else "html"  # Use lite backend for long queries
        )
        
        # Transform the results to the expected format
        formatted_results = []
        for result in results:
            formatted_results.append({
                'title': result.get('title', ''),
                'url': result.get('href', ''),  # duckduckgo-search uses 'href' for the URL
                'snippet': result.get('body', '')  # duckduckgo-search uses 'body' for snippets
            })
            
        return formatted_results
    
    except DuckDuckGoSearchException as e:
        # Handle specific exceptions from the duckduckgo-search library
        logger.error(f"DuckDuckGo search error: {str(e)}")
        # Try using the lite backend as a fallback
        try:
            if "backend" not in str(e).lower():
                logger.info("Retrying with lite backend as fallback")
                ddgs = DDGS(timeout=timeout)
                results = ddgs.text(
                    keywords=query,
                    region=region,
                    safesearch=safesearch,
                    max_results=max_results,
                    backend="lite"
                )
                
                # Transform the results
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        'title': result.get('title', ''),
                        'url': result.get('href', ''),
                        'snippet': result.get('body', '')
                    })
                return formatted_results
        except Exception as inner_e:
            logger.error(f"Fallback search failed: {str(inner_e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error during search: {str(e)}")
        return []

@mcp.tool()
def duckduckgo_search(query: str, max_results: int = 5, 
                      safesearch: str = "moderate") -> List[Dict[str, str]]:
    """
    Search the web using DuckDuckGo.
    
    Args:
        query: The search query
        max_results: Maximum number of search results to return (default: 5)
        safesearch: Safe search setting ('on', 'moderate', 'off'; default: 'moderate')
        
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
        results = search_duckduckgo(query, max_results, safesearch)
        
        # Check if we got any results
        if not results:
            logger.warning(f"No results found for query: '{query}'")
            
        # Return results
        return results
    except Exception as e:
        logger.error(f"Error in duckduckgo_search: {str(e)}")
        raise

def main():
    """Main function for CLI usage"""
    parser = argparse.ArgumentParser(description="Search DuckDuckGo from the command line")
    parser.add_argument("query", help="The search query", nargs='+')
    parser.add_argument("--max-results", "-n", type=int, default=5, 
                        help="Maximum number of results (default: 5)")
    parser.add_argument("--safesearch", choices=["on", "moderate", "off"], 
                        default="moderate", help="Safe search setting (default: moderate)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Join query arguments to handle quotes properly
    query = " ".join(args.query)
    
    # Perform search
    results = search_duckduckgo(
        query=query,
        max_results=args.max_results,
        safesearch=args.safesearch
    )
    
    # Output results as JSON
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()