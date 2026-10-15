import asyncio
import random
from playwright.async_api import async_playwright

# Set how many tabs you want open at exactly the same time.
# WARNING: Setting this higher than 10 might crash the browser or overwhelm Burp Suite!
CONCURRENT_TABS = 5

async def visit_url(context, url, semaphore):
    # The semaphore ensures we only run 'CONCURRENT_TABS' amount of tasks at once
    async with semaphore:
        print(f"[*] Opening: {url}")
        
        # Open a new tab
        page = await context.new_page()
        try:
            # wait_until="load" ensures all images, stylesheets, and JS are fully loaded
            await page.goto(url, wait_until="load", timeout=45000)
            
            # Scroll to the bottom of the page to trigger lazy-loaded endpoints for Burp
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            # Random delay so JS can finish executing and background requests can fire
            delay = random.uniform(3.0, 6.0)
            await page.wait_for_timeout(delay * 1000)
            
            print(f"[+] Done: {url}")
            
        except Exception as e:
            print(f"[-] Failed: {url} -> {e}")
            
        finally:
            # Always close the tab when done so we don't eat all your RAM
            await page.close()

async def run(playwright):
    proxy_settings = {
        "server": "http://127.0.0.1:8080"
    }

    print("Launching Chromium through Burp Suite proxy with concurrent tabs...\n")
    
    browser = await playwright.chromium.launch(
        headless=False, 
        proxy=proxy_settings
    )
    
    context = await browser.new_context(ignore_https_errors=True)

    try:
        with open('all.txt', 'r') as file:
            raw_urls = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print("Error: 'urls.txt' not found.")
        await browser.close()
        return

    print(f"Found {len(raw_urls)} base URLs. Generating HTTP and HTTPS tasks...")

    # Create a traffic controller (semaphore) to limit concurrent tabs
    semaphore = asyncio.Semaphore(CONCURRENT_TABS)
    
    # Create a list of tasks for all URLs (both HTTP and HTTPS)
    tasks = []
    for raw_url in raw_urls:
        # Clean the URL to get just the domain/path
        base_url = raw_url.replace('https://', '').replace('http://', '')
        
        # Add both versions to our task list as independent concurrent jobs
        tasks.append(visit_url(context, f"http://{base_url}", semaphore))
        tasks.append(visit_url(context, f"https://{base_url}", semaphore))
        
    print(f"Total tasks queued: {len(tasks)}. Processing {CONCURRENT_TABS} at a time...\n")

    # Run them all (the semaphore will throttle them to 5 at a time)
    await asyncio.gather(*tasks)

    print("\nFinished visiting all URLs. Closing browser...")
    await browser.close()

async def main():
    async with async_playwright() as playwright:
        await run(playwright)

if __name__ == "__main__":
    asyncio.run(main())