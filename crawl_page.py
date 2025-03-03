import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from bs4 import BeautifulSoup

async def scrape_article_body(url):
    # Configure the crawler
    config = CrawlerRunConfig(
        css_selector="div.article-body",  # Target only article-body div
               # Retry on failures
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
                print("Extracted Text Length:", len(text_content))

                # Optionally convert to Markdown manually if needed
                # Here, we use the raw text for simplicity
                return text_content
            else:
                print("No article-body div found in the page.")
                return ""
        else:
            print(f"Crawl failed: {result.error_message}")
            return ""

async def main():
    url = "https://www.fool.com/earnings/call-transcripts/2021/02/17/analog-devices-inc-adi-q1-2021-earnings-call-trans/"
    article_text = await scrape_article_body(url)

    if article_text:
        with open("article_body_only.md", "w", encoding="utf-8") as f:
            f.write(article_text)
        print("Content saved to article_body_only.txt")

if __name__ == "__main__":
    asyncio.run(main())