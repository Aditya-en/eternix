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