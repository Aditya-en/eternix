#!/usr/bin/env python3
"""
MCP Server for Headless Browser Automation
Allows LLMs to execute Selenium scripts on a remote machine
"""

import asyncio
import json
import logging
import traceback
from datetime import datetime
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
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
                "WebDriverWait": WebDriverWait,
                "EC": EC,
                "logger": self,  # Allow script to use self.log()
                "__builtins__": __builtins__,
            }
            
            exec_locals = {}
            
            # Execute the script
            exec(script, exec_globals, exec_locals)
            
            # Check if script defined a 'result' variable
            if "result" in exec_locals:
                result["output"] = exec_locals["result"]
                self.log(f"Script returned result: {exec_locals['result']}")
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
            error_msg = f"Runtime error: {str(e)}\n{traceback.format_exc()}"
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


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available browser automation tools"""
    return [
        Tool(
            name="execute_browser_script",
            description="""
            Execute a Selenium script in a headless Chrome browser.
            
            The script should be valid Python code that uses the 'driver' variable (WebDriver instance).
            Available in the script namespace:
            - driver: Selenium WebDriver instance
            - By: Selenium By locator
            - WebDriverWait: Explicit wait utility
            - EC: Expected conditions
            - logger: Use logger.log(message, level) to add custom log messages
            
            To return data, assign it to a variable named 'result'.
            
            Example script:
            ```python
            driver.get("https://example.com")
            title = driver.title
            elements = driver.find_elements(By.TAG_NAME, "p")
            result = {
                "title": title,
                "paragraph_count": len(elements)
            }
            ```
            
            The server will return:
            - status: "success" or "failed"
            - output: The value of 'result' variable if defined
            - logs: Complete execution log with timestamps
            - error: Error message if execution failed
            - execution_time: Time taken in seconds
            """,
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
            name="navigate_and_extract",
            description="""
            Helper tool for common tasks: navigate to a URL and extract information.
            
            This is a convenience wrapper that handles common extraction patterns.
            """,
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
    
    if name == "execute_browser_script":
        script = arguments.get("script")
        description = arguments.get("description", "")
        
        if not script:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "No script provided"}, indent=2)
            )]
        
        logger.info(f"Executing browser script: {description if description else 'No description'}")
        
        executor = BrowserExecutor()
        result = await executor.execute_script(script)
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]
    
    elif name == "navigate_and_extract":
        url = arguments.get("url")
        extract_config = arguments.get("extract", {})
        
        # Build a script based on extraction requirements
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
        
        executor = BrowserExecutor()
        result = await executor.execute_script(script)
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]
    
    else:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2)
        )]


async def main():
    """Main entry point"""
    from mcp.server.stdio import stdio_server
    
    logger.info("Starting Browser Automation MCP Server")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())