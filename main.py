#!/usr/bin/env python3
"""
MCP Server for Headless Browser Automation
Allows LLMs to execute Selenium scripts on a remote machine
Enhanced with pre-built tools for common tasks
"""

import asyncio
import json
import logging
import traceback
import base64
from datetime import datetime
from typing import Any, Optional
from urllib.parse import quote_plus

from mcp.server import Server
from mcp.types import Tool, TextContent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("browser-mcp-server")

# Initialize MCP server
app = Server("browser-automation-server")

# Global configuration
SCRIPT_TIMEOUT = 300  # 5 minutes max execution time
IMPLICIT_WAIT = 10  # seconds


class BrowserExecutor:
    """Handles browser script execution with proper isolation and logging"""
    
    def __init__(self):
        self.driver = None
        self.log_messages = []
    
    def log(self, message: str, level: str = "INFO"):
        """Add log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.log_messages.append(log_entry)
        
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)
    
    def setup_driver(self):
        """Initialize headless Chrome driver"""
        self.log("Initializing headless Chrome driver")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(IMPLICIT_WAIT)
        self.log("Driver initialized successfully")
    
    def cleanup_driver(self):
        """Clean up browser resources"""
        if self.driver:
            try:
                self.log("Closing browser")
                self.driver.quit()
            except Exception as e:
                self.log(f"Error during cleanup: {str(e)}", "WARNING")
    
    async def execute_script(self, script: str) -> dict:
        """Execute the provided Selenium script"""
        result = {
            "status": "unknown",
            "output": None,
            "error": None,
            "logs": [],
            "execution_time": 0
        }
        
        start_time = datetime.now()
        
        try:
            self.setup_driver()
            
            self.log("Starting script execution")
            
            # Create execution namespace with necessary imports and driver
            exec_globals = {
                "driver": self.driver,
                "By": By,
                "Keys": Keys,
                "WebDriverWait": WebDriverWait,
                "EC": EC,
                "logger": self,
                "base64": base64,
                "__builtins__": __builtins__,
            }
            
            exec_locals = {}
            
            # Execute the script
            exec(script, exec_globals, exec_locals)
            
            # Check if script defined a 'result' variable
            if "result" in exec_locals:
                result["output"] = exec_locals["result"]
                self.log(f"Script returned result")
            else:
                result["output"] = "Script executed successfully (no explicit result returned)"
                self.log("Script executed successfully")
            
            result["status"] = "success"
            
        except SyntaxError as e:
            error_msg = f"Syntax error in script: {str(e)}"
            self.log(error_msg, "ERROR")
            result["status"] = "failed"
            result["error"] = error_msg
            
        except Exception as e:
            error_msg = f"Runtime error: {str(e)}"
            self.log(error_msg, "ERROR")
            result["status"] = "failed"
            result["error"] = str(e)
            result["traceback"] = traceback.format_exc()
            
        finally:
            self.cleanup_driver()
            end_time = datetime.now()
            result["execution_time"] = (end_time - start_time).total_seconds()
            result["logs"] = self.log_messages
            
        return result


# Pre-built script templates
SCRIPT_TEMPLATES = {
    "google_search": """
driver.get("https://www.google.com")
logger.log("Loaded Google homepage", "INFO")

# Handle cookie consent if present
try:
    consent_button = driver.find_element(By.XPATH, "//button[contains(., 'Accept') or contains(., 'Agree')]")
    consent_button.click()
    logger.log("Accepted cookie consent", "INFO")
except:
    logger.log("No cookie consent found", "INFO")

# Perform search
search_box = driver.find_element(By.NAME, "q")
search_box.send_keys("{query}")
search_box.send_keys(Keys.RETURN)
logger.log(f"Searched for: {query}", "INFO")

# Wait for results
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "search"))
)

# Extract results
results = []
search_results = driver.find_elements(By.CSS_SELECTOR, "div.g")[:{max_results}]

for idx, result_elem in enumerate(search_results, 1):
    try:
        title_elem = result_elem.find_element(By.CSS_SELECTOR, "h3")
        link_elem = result_elem.find_element(By.CSS_SELECTOR, "a")
        snippet_elem = result_elem.find_elements(By.CSS_SELECTOR, "div.VwiC3b")
        
        results.append({{
            "rank": idx,
            "title": title_elem.text,
            "url": link_elem.get_attribute("href"),
            "snippet": snippet_elem[0].text if snippet_elem else ""
        }})
        logger.log(f"Extracted result {{idx}}: {{title_elem.text}}", "INFO")
    except Exception as e:
        logger.log(f"Error extracting result {{idx}}: {{e}}", "WARNING")

result = {{
    "query": "{query}",
    "results_count": len(results),
    "results": results
}}
""",
    
    "hackernews_top_stories": """
driver.get("https://news.ycombinator.com")
logger.log("Loaded Hacker News", "INFO")

stories = []
story_rows = driver.find_elements(By.CSS_SELECTOR, "tr.athing")[:{count}]

for story in story_rows:
    try:
        rank = story.find_element(By.CLASS_NAME, "rank").text
        title_elem = story.find_element(By.CLASS_NAME, "titleline")
        title = title_elem.text
        link = title_elem.find_element(By.TAG_NAME, "a").get_attribute("href")
        
        stories.append({{
            "rank": rank,
            "title": title,
            "url": link
        }})
        logger.log(f"Story {{rank}}: {{title}}", "INFO")
    except Exception as e:
        logger.log(f"Error extracting story: {{e}}", "WARNING")

result = {{
    "source": "Hacker News",
    "stories": stories,
    "count": len(stories)
}}
""",

    "reddit_subreddit": """
driver.get("https://old.reddit.com/r/{subreddit}")
logger.log(f"Loaded r/{subreddit}", "INFO")

posts = []
post_elements = driver.find_elements(By.CSS_SELECTOR, "div.thing")[:{count}]

for post in post_elements:
    try:
        title = post.find_element(By.CSS_SELECTOR, "a.title").text
        url = post.find_element(By.CSS_SELECTOR, "a.title").get_attribute("href")
        score = post.find_element(By.CSS_SELECTOR, "div.score.unvoted").text
        author = post.get_attribute("data-author")
        
        posts.append({{
            "title": title,
            "url": url,
            "score": score,
            "author": author
        }})
        logger.log(f"Post: {{title[:50]}}", "INFO")
    except Exception as e:
        logger.log(f"Error extracting post: {{e}}", "WARNING")

result = {{
    "subreddit": "{subreddit}",
    "posts": posts,
    "count": len(posts)
}}
""",

    "github_repo_info": """
driver.get("https://github.com/{owner}/{repo}")
logger.log(f"Loaded GitHub repo: {{owner}}/{{repo}}", "INFO")

try:
    # Extract repo information
    description_elem = driver.find_elements(By.CSS_SELECTOR, "p.f4")
    description = description_elem[0].text if description_elem else "No description"
    
    # Get stats
    stats = {{}}
    stat_elements = driver.find_elements(By.CSS_SELECTOR, "a.Link--muted")
    for stat in stat_elements:
        text = stat.text
        if "star" in text.lower():
            stats["stars"] = text
        elif "fork" in text.lower():
            stats["forks"] = text
    
    # Get language
    language_elem = driver.find_elements(By.CSS_SELECTOR, "span[itemprop='programmingLanguage']")
    language = language_elem[0].text if language_elem else "Unknown"
    
    # Get topics
    topics = []
    topic_elements = driver.find_elements(By.CSS_SELECTOR, "a.topic-tag")
    topics = [t.text for t in topic_elements]
    
    result = {{
        "owner": "{owner}",
        "repo": "{repo}",
        "description": description,
        "language": language,
        "stats": stats,
        "topics": topics,
        "url": driver.current_url
    }}
    logger.log("Successfully extracted repo info", "INFO")
    
except Exception as e:
    logger.log(f"Error extracting repo info: {{e}}", "ERROR")
    result = {{"error": str(e)}}
""",

    "wikipedia_article": """
driver.get("https://en.wikipedia.org/wiki/{article}")
logger.log(f"Loaded Wikipedia article: {{article}}", "INFO")

try:
    # Get title
    title = driver.find_element(By.ID, "firstHeading").text
    logger.log(f"Article title: {{title}}", "INFO")
    
    # Get first paragraph
    first_para = driver.find_element(By.CSS_SELECTOR, ".mw-parser-output > p").text
    
    # Get table of contents
    toc_items = driver.find_elements(By.CSS_SELECTOR, ".toc ul li a")
    sections = [item.text for item in toc_items[:10]]
    
    # Get infobox data if present
    infobox = {{}}
    try:
        infobox_rows = driver.find_elements(By.CSS_SELECTOR, ".infobox tr")
        for row in infobox_rows[:10]:
            cells = row.find_elements(By.TAG_NAME, "th") + row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                key = cells[0].text.strip()
                value = cells[1].text.strip()
                if key and value:
                    infobox[key] = value
    except:
        logger.log("No infobox found", "INFO")
    
    result = {{
        "title": title,
        "introduction": first_para[:500] + "..." if len(first_para) > 500 else first_para,
        "sections": sections,
        "infobox": infobox,
        "url": driver.current_url
    }}
    logger.log("Successfully extracted article data", "INFO")
    
except Exception as e:
    logger.log(f"Error extracting article: {{e}}", "ERROR")
    result = {{"error": str(e)}}
""",

    "screenshot_page": """
driver.get("{url}")
logger.log(f"Loaded page: {url}", "INFO")

# Wait for page to load
import time
time.sleep(2)

# Take screenshot
screenshot_b64 = driver.get_screenshot_as_base64()
logger.log("Screenshot captured", "INFO")

result = {{
    "url": driver.current_url,
    "title": driver.title,
    "screenshot_base64": screenshot_b64,
    "screenshot_size_kb": len(screenshot_b64) // 1024
}}
""",

    "extract_all_links": """
driver.get("{url}")
logger.log(f"Loaded page: {url}", "INFO")

# Extract all links
all_links = driver.find_elements(By.TAG_NAME, "a")
logger.log(f"Found {{len(all_links)}} links", "INFO")

links = []
for link in all_links:
    href = link.get_attribute("href")
    text = link.text.strip()
    if href and href.startswith("http"):
        links.append({{
            "text": text,
            "url": href
        }})

# Filter by domain if specified
{filter_code}

result = {{
    "page_url": driver.current_url,
    "page_title": driver.title,
    "total_links": len(all_links),
    "extracted_links": links[:100],  # Limit to first 100
    "link_count": len(links)
}}
logger.log(f"Extracted {{len(links)}} valid links", "INFO")
""",

    "fill_form": """
driver.get("{url}")
logger.log(f"Loaded form page: {url}", "INFO")

# Wait for form to be present
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.TAG_NAME, "form"))
)

filled_fields = []

# Fill form fields based on data provided
{fill_code}

logger.log(f"Filled {{len(filled_fields)}} form fields", "INFO")

result = {{
    "url": driver.current_url,
    "filled_fields": filled_fields,
    "status": "form_filled"
}}
""",

    "check_page_performance": """
driver.get("{url}")
logger.log(f"Loaded page: {url}", "INFO")

# Get page load timing
navigation_start = driver.execute_script("return window.performance.timing.navigationStart")
load_complete = driver.execute_script("return window.performance.timing.loadEventEnd")
dom_complete = driver.execute_script("return window.performance.timing.domComplete")

load_time = (load_complete - navigation_start) / 1000
dom_time = (dom_complete - navigation_start) / 1000

# Count resources
resources = driver.execute_script("return window.performance.getEntriesByType('resource').length")

# Get page size
page_source_size = len(driver.page_source)

result = {{
    "url": driver.current_url,
    "title": driver.title,
    "load_time_seconds": round(load_time, 2),
    "dom_ready_seconds": round(dom_time, 2),
    "resource_count": resources,
    "page_size_kb": round(page_source_size / 1024, 2)
}}
logger.log(f"Page loaded in {{load_time:.2f}}s", "INFO")
"""
}


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available browser automation tools"""
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


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool execution"""
    
    executor = BrowserExecutor()
    
    try:
        if name == "execute_browser_script":
            script = arguments.get("script")
            description = arguments.get("description", "")
            
            if not script:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "No script provided"}, indent=2)
                )]
            
            logger.info(f"Executing custom script: {description if description else 'No description'}")
            result = await executor.execute_script(script)
            
        elif name == "google_search":
            query = arguments.get("query")
            max_results = arguments.get("max_results", 10)
            
            script = SCRIPT_TEMPLATES["google_search"].format(
                query=query.replace('"', '\\"'),
                max_results=max_results
            )
            result = await executor.execute_script(script)
            
        elif name == "get_hackernews_stories":
            count = arguments.get("count", 10)
            
            script = SCRIPT_TEMPLATES["hackernews_top_stories"].format(count=count)
            result = await executor.execute_script(script)
            
        elif name == "get_reddit_posts":
            subreddit = arguments.get("subreddit")
            count = arguments.get("count", 10)
            
            script = SCRIPT_TEMPLATES["reddit_subreddit"].format(
                subreddit=subreddit,
                count=count
            )
            result = await executor.execute_script(script)
            
        elif name == "get_github_repo_info":
            owner = arguments.get("owner")
            repo = arguments.get("repo")
            
            script = SCRIPT_TEMPLATES["github_repo_info"].format(
                owner=owner,
                repo=repo
            )
            result = await executor.execute_script(script)
            
        elif name == "get_wikipedia_article":
            article = arguments.get("article")
            # URL encode if needed
            article = article.replace(" ", "_")
            
            script = SCRIPT_TEMPLATES["wikipedia_article"].format(article=article)
            result = await executor.execute_script(script)
            
        elif name == "take_screenshot":
            url = arguments.get("url")
            
            script = SCRIPT_TEMPLATES["screenshot_page"].format(url=url)
            result = await executor.execute_script(script)
            
        elif name == "extract_all_links":
            url = arguments.get("url")
            filter_domain = arguments.get("filter_domain", "")
            
            filter_code = ""
            if filter_domain:
                filter_code = f"""
links = [l for l in links if "{filter_domain}" in l["url"]]
logger.log(f"Filtered to {{len(links)}} links containing '{filter_domain}'", "INFO")
"""
            
            script = SCRIPT_TEMPLATES["extract_all_links"].format(
                url=url,
                filter_code=filter_code
            )
            result = await executor.execute_script(script)
            
        elif name == "check_page_performance":
            url = arguments.get("url")
            
            script = SCRIPT_TEMPLATES["check_page_performance"].format(url=url)
            result = await executor.execute_script(script)
            
        elif name == "navigate_and_extract":
            url = arguments.get("url")
            extract_config = arguments.get("extract", {})
            
            script_parts = [f"driver.get('{url}')", "result = {}"]
            
            if extract_config.get("title"):
                script_parts.append("result['title'] = driver.title")
            
            if extract_config.get("text"):
                script_parts.append("result['body_text'] = driver.find_element(By.TAG_NAME, 'body').text")
            
            if extract_config.get("links"):
                script_parts.append("result['links'] = [elem.get_attribute('href') for elem in driver.find_elements(By.TAG_NAME, 'a')]")
            
            selectors = extract_config.get("selectors", {})
            for key, selector in selectors.items():
                script_parts.append(f"result['{key}'] = [elem.text for elem in driver.find_elements(By.CSS_SELECTOR, '{selector}')]")
            
            script = "\n".join(script_parts)
            result = await executor.execute_script(script)
            
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2)
            )]
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]
        
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "traceback": traceback.format_exc()
            }, indent=2)
        )]


async def main():
    """Main entry point"""
    from mcp.server.stdio import stdio_server
    
    logger.info("Starting Enhanced Browser Automation MCP Server")
    logger.info(f"Available tools: {len(await list_tools())}")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())