import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from bs4 import BeautifulSoup
import pandas as pd
import re
import os

async def scrape_article_body(url, folder_name, file_name):
    file_path = f"./transcripts/{folder_name}/{file_name}.md"

    # Configure the crawler
    config = CrawlerRunConfig(
        css_selector="div.article-body",  # Target only article-body div
    )

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=url,
            config=config
        )

        if result.success:
            # Parse the raw HTML with BeautifulSoup to extract only article-body
            soup = BeautifulSoup(result.html, 'html.parser')
            article_body = soup.select_one('div.article-body')

            if article_body:
                # Get the text content from article-body
                text_content = article_body.get_text(separator='\n', strip=True)
                print(f"Extracted Text Length for {url}: {len(text_content)}")

                # Save the content
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(text_content)
                print(f"Content saved to {file_name}.md")
                return True
            else:
                print(f"No article-body div found in {url}")
                return False
        else:
            print(f"Crawl failed for {url}: {result.error_message}")
            return False

async def process_row(row, semaphore):
    folder_name = row[0]
    url = row[1]
    pattern = r"q\d{1}-\d{4}"
    match = re.search(pattern, url, re.IGNORECASE)
    file_name = match.group() if match else "article_body_only"
    file_path = f"./transcripts/{folder_name}/{file_name}.md"

    print(f"Processing {url}...")

    # Skip if file already exists
    if os.path.exists(file_path):
        print(f"Skipping {url} - File {file_name}.md already exists")
        return True

    # Ensure directory exists
    os.makedirs(f"./transcripts/{folder_name}", exist_ok=True)

    # Use semaphore to limit concurrent requests
    async with semaphore:
        status = await scrape_article_body(url, folder_name, file_name)

    if status:
        print(f"Scraped {url} successfully!")
    else:
        print(f"Failed to scrape {url}")
    return status

async def main():
    # Load the CSV file
    df = pd.read_csv('./output/exploded_transcript_links.csv')

    # Create a semaphore to limit concurrent requests to 10
    semaphore = asyncio.Semaphore(10)

    # Create a list of tasks for parallel execution
    tasks = [process_row(row, semaphore) for row in df.itertuples(index=False)]

    # Run all tasks in parallel and wait for completion
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results and provide summary
    successful = sum(1 for r in results if r is True)
    failed = len(results) - successful
    print(f"\nScraping completed: {successful} successful, {failed} failed")

if __name__ == "__main__":
    asyncio.run(main())