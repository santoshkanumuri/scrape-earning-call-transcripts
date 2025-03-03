# Exchange Data and Transcripts Scraper

## Overview
This project extracts exchange data, scrapes company links, and downloads transcripts from financial websites. It processes a list of company symbols from a CSV file, retrieves exchange data, scrapes links from Fool.com, and downloads transcripts into structured folders.

## Features
- Retrieves exchange data for a list of companies.
- Scrapes company website links from Fool.com.
- Crawls company pages asynchronously and downloads transcripts.
- Organizes transcripts in a structured folder hierarchy.

## Prerequisites
Ensure you have `uv` installed on your system before proceeding.

## Installation and Setup
1. Clone the repository:
   ```sh
   git clone <repo_url>
   cd <repo_directory>
   ```
2. Install `uv` (if not already installed):
   ```sh
   pip install uv
   ```
3. Initialize the project with `uv`:
   ```sh
   uv init
   ```
4. Install all dependencies:
   ```sh
   uv sync
   ```

## Usage
1. Prepare a CSV file containing company symbols.
2. Run the following command to get exchange data:
   ```sh
   uv run exchange.py
   ```
   - This generates an output file containing exchange data.
3. Scrape links from Fool.com for the companies:
   ```sh
   uv run scrape_links.py
   ```
   - This stores the scraped links in an output file.
4. Crawl company pages and download transcripts:
   ```sh
   uv run crawl_all_pages_async.py
   ```
   - Transcripts are saved in the `transcripts` folder, categorized by company.

## Dependencies
This project uses the following Python libraries:
- `crawl4ai`
- `beautifulsoup4 (bs4)`
- `asyncio`
- `pandas`

## Output Structure
The transcripts are stored in the following folder structure:
```
transcripts/
    ├── Company_A/
    │   ├── transcript_1.txt
    │   ├── transcript_2.txt
    ├── Company_B/
    │   ├── transcript_1.txt
    │   ├── transcript_2.txt
```

## Notes
- Ensure the CSV file with company symbols is formatted correctly before running the script.
- The process may take time depending on the number of companies and the network speed.

## License
This project is licensed under the MIT License.

## Author
Santosh Kanumuri
