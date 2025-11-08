import logging
import traceback
import base64
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logger = logging.getLogger("browser-mcp-server.executor")

# Global configuration
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
                "logger": self,  # Allows script to call self.log()
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