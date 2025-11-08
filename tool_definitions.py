from mcp.types import Tool

def get_tool_list() -> list[Tool]:
    """Returns the static list of all available tools"""
    return [
        Tool(
            name="execute_browser_script",
            description="Execute a custom Selenium script in a headless Chrome browser.",
            inputSchema={
                "type": "object",
                "properties": {
                    "script": {
                        "type": "string",
                        "description": "Python Selenium script to execute"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description of what the script does"
                    }
                },
                "required": ["script"]
            }
        ),
        
        Tool(
            name="google_search",
            description="Search Google and extract top results with titles, URLs, and snippets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        
        Tool(
            name="get_hackernews_stories",
            description="Get top stories from Hacker News with titles and links.",
            inputSchema={
                "type": "object",
                "properties": {
                    "count": {
                        "type": "integer",
                        "description": "Number of stories to fetch (default: 10)",
                        "default": 10
                    }
                }
            }
        ),
        
        Tool(
            name="get_reddit_posts",
            description="Get top posts from a Reddit subreddit.",
            inputSchema={
                "type": "object",
                "properties": {
                    "subreddit": {
                        "type": "string",
                        "description": "Subreddit name (without r/)"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of posts to fetch (default: 10)",
                        "default": 10
                    }
                },
                "required": ["subreddit"]
            }
        ),
        
        Tool(
            name="get_github_repo_info",
            description="Get detailed information about a GitHub repository.",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Repository owner username"
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name"
                    }
                },
                "required": ["owner", "repo"]
            }
        ),
        
        Tool(
            name="get_wikipedia_article",
            description="Extract information from a Wikipedia article including title, introduction, sections, and infobox.",
            inputSchema={
                "type": "object",
                "properties": {
                    "article": {
                        "type": "string",
                        "description": "Wikipedia article title (URL-encoded or plain)"
                    }
                },
                "required": ["article"]
            }
        ),
        
        Tool(
            name="take_screenshot",
            description="Take a screenshot of any webpage and return as base64.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of the page to screenshot"
                    }
                },
                "required": ["url"]
            }
        ),
        
        Tool(
            name="extract_all_links",
            description="Extract all links from a webpage with optional domain filtering.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to extract links from"
                    },
                    "filter_domain": {
                        "type": "string",
                        "description": "Optional: Only return links containing this domain"
                    }
                },
                "required": ["url"]
            }
        ),
        
        Tool(
            name="check_page_performance",
            description="Check page load performance metrics including load time, DOM ready time, and resource count.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to check performance for"
                    }
                },
                "required": ["url"]
            }
        ),
        
        Tool(
            name="navigate_and_extract",
            description="Navigate to a URL and extract specific information using CSS selectors.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to navigate to"
                    },
                    "extract": {
                        "type": "object",
                        "description": "What to extract from the page",
                        "properties": {
                            "title": {"type": "boolean"},
                            "text": {"type": "boolean"},
                            "links": {"type": "boolean"},
                            "selectors": {
                                "type": "object",
                                "description": "CSS selectors to extract specific elements",
                                "additionalProperties": {"type": "string"}
                            }
                        }
                    }
                },
                "required": ["url"]
            }
        )
    ]