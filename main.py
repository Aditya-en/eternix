#!/usr/bin/env python3
"""
MCP Server for Headless Browser Automation
Allows LLMs to execute Selenium scripts on a remote machine
"""

import asyncio
import json
import logging
import traceback
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import modular components
from browser_executor import BrowserExecutor
from tool_definitions import get_tool_list
from tool_templates import SCRIPT_TEMPLATES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("browser-mcp-server")

# Initialize MCP server
app = Server("browser-automation-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available browser automation tools"""
    return get_tool_list()


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool execution by routing to the correct template or custom script"""
    
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
    logger.info("Starting Enhanced Browser Automation MCP Server")
    logger.info(f"Available tools: {len(get_tool_list())}")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())