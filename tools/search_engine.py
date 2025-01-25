#!/usr/bin/env python3

import argparse
import sys
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os

def search_with_retry(query, max_results=10, max_retries=3):
    """
    Search using Google Custom Search API and return results with URLs and text snippets.
    
    Args:
        query (str): Search query
        max_results (int): Maximum number of results to return
        max_retries (int): Maximum number of retry attempts
    """
    
    api_key = os.getenv('GOOGLE_API_KEY')
    cx = os.getenv('GOOGLE_SEARCH_CX')

    if not api_key or not cx:
        raise ValueError("GOOGLE_API_KEY and GOOGLE_SEARCH_CX environment variables must be set")

    service = build('customsearch', 'v1', developerKey=api_key)

    for attempt in range(max_retries):
        try:
            print(f"DEBUG: Searching for query: {query} (attempt {attempt + 1}/{max_retries})", 
                  file=sys.stderr)
            
            # Google API returns max 10 results per request
            results = []
            for i in range(0, min(max_results, 100), 10):
                response = service.cse().list(
                    q=query,
                    cx=cx,
                    start=i + 1,
                    num=min(10, max_results - i)
                ).execute()
                
                if 'items' in response:
                    results.extend([{
                        'href': item['link'],
                        'title': item['title'],
                        'body': item['snippet']
                    } for item in response['items']])
                
                if len(results) >= max_results:
                    break
            
            if not results:
                print("DEBUG: No results found", file=sys.stderr)
                return []
            
            print(f"DEBUG: Found {len(results)} results", file=sys.stderr)
            return results[:max_results]
                
        except HttpError as e:
            print(f"ERROR: Attempt {attempt + 1}/{max_retries} failed: {str(e)}", file=sys.stderr)
            if attempt < max_retries - 1:  # If not the last attempt
                print(f"DEBUG: Waiting 1 second before retry...", file=sys.stderr)
                time.sleep(1)  # Wait 1 second before retry
            else:
                print(f"ERROR: All {max_retries} attempts failed", file=sys.stderr)
                raise
        except Exception as e:
            print(f"ERROR: Unexpected error: {str(e)}", file=sys.stderr)
            raise

def format_results(results):
    """Format and print search results."""
    for i, r in enumerate(results, 1):
        print(f"\n=== Result {i} ===")
        print(f"URL: {r.get('href', 'N/A')}")
        print(f"Title: {r.get('title', 'N/A')}")
        print(f"Snippet: {r.get('body', 'N/A')}")

def search(query, max_results=10, max_retries=3):
    """
    Main search function that handles search with retry mechanism.
    
    Args:
        query (str): Search query
        max_results (int): Maximum number of results to return
        max_retries (int): Maximum number of retry attempts
    """
    try:
        results = search_with_retry(query, max_results, max_retries)
        if results:
            format_results(results)
            
    except Exception as e:
        print(f"ERROR: Search failed: {str(e)}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Search using DuckDuckGo API")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--max-results", type=int, default=10,
                      help="Maximum number of results (default: 10)")
    parser.add_argument("--max-retries", type=int, default=3,
                      help="Maximum number of retry attempts (default: 3)")
    
    args = parser.parse_args()
    search(args.query, args.max_results, args.max_retries)

if __name__ == "__main__":
    main()
