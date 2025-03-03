import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import os
from pathlib import Path
import random

# Create output folder if it doesn't exist
output_dir = 'output'
Path(output_dir).mkdir(exist_ok=True)

# Function to initialize and return a Chrome browser instance with options
def open_new_browser() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    # Uncomment the following line if you want to hide the browser UI
    # options.add_argument("--headless")

    service = webdriver.chrome.service.Service(ChromeDriverManager().install())
    browser = webdriver.Chrome(service=service, options=options)
    return browser

# Function to check if the "Load More" button is present and visible
def is_load_more_button_present(driver):
    try:
        button = driver.find_element(By.CSS_SELECTOR, '#quote-earnings-transcripts .load-more-button')
        return button.is_displayed() and 'hidden' not in button.get_attribute('class').split()
    except (NoSuchElementException, StaleElementReferenceException):
        return False

# Improved function to scroll and click "Load More" button
def load_all_transcripts(driver):
    max_retries = 10
    retry_count = 0

    while retry_count < max_retries:
        try:
            # Check if the button exists and is not hidden
            if not is_load_more_button_present(driver):
                print("All transcripts loaded or no more to load.")
                break

            # Find the button with a more robust selector
            button = driver.find_element(By.CSS_SELECTOR, '#quote-earnings-transcripts .load-more-button')

            # Scroll to the button with offset to ensure it's in view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(random.uniform(1.5, 2.5))  # Random delay to mimic human behavior

            # Try to click the button
            try:
                # Use JavaScript click as a more reliable method
                driver.execute_script("arguments[0].click();", button)
                print("Clicked 'Load More' button.")
                time.sleep(random.uniform(2, 3))  # Wait for content to load
                retry_count = 0  # Reset retry count on successful click
            except Exception as e:
                print(f"Click attempt failed: {str(e)}")
                retry_count += 1

        except StaleElementReferenceException:
            print("Element became stale, retrying...")
            time.sleep(1)
            retry_count += 1
        except Exception as e:
            print(f"Error in loading transcripts: {str(e)}")
            retry_count += 1

    if retry_count >= max_retries:
        print("Maximum retries reached. Some transcripts may not be loaded.")

# Improved function to extract transcript links with more careful parsing
def get_transcript_links(driver):
    # Ensure we're at the transcripts section
    transcript_section = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "quote-earnings-transcripts"))
    )

    # Scroll through the entire container to ensure all content is rendered
    driver.execute_script("""
        let section = document.getElementById('quote-earnings-transcripts');
        if (section) {
            section.scrollIntoView({behavior: 'smooth', block: 'start'});

            // Scroll through the section
            let height = section.scrollHeight;
            let current = 0;
            let step = 200;

            while (current < height) {
                current += step;
                section.scrollTo(0, current);
            }
        }
    """)
    time.sleep(2)  # Give time for any lazy-loaded content

    # Parse page source with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Find all transcript containers - more robust approach
    links = []

    # Method 1: Look for links in the earnings transcript container
    transcript_container = soup.find('div', id='earnings-transcript-container')
    if transcript_container:
        container_links = [a['href'] for a in transcript_container.find_all('a', href=True)]
        links.extend(container_links)

    # Method 2: Look for transcript links by specific patterns
    transcript_section = soup.find('section', id='quote-earnings-transcripts')
    if transcript_section:
        # Find all links in the transcript section
        for a in transcript_section.find_all('a', href=True):
            href = a['href']
            # Filter for likely transcript links
            if 'earnings-call-transcript' in href or 'conference-call-transcript' in href:
                links.append(href)

    # Remove duplicates while preserving order
    unique_links = []
    for link in links:
        if link not in unique_links:
            unique_links.append(link)

    # Prepend base URL if links are relative
    base_url = 'https://www.fool.com'
    full_links = [base_url + link if link.startswith('/') else link for link in unique_links]

    return full_links

# Improved cookie consent and popup handling
def handle_popups(driver):
    try:
        # Try to find and click the cookie accept button with a longer timeout
        cookie_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler'))
        )
        cookie_button.click()
        print("Cookie banner dismissed.")
        time.sleep(2)  # Wait for banner to disappear
    except (TimeoutException, NoSuchElementException):
        print("No cookie banner found or already accepted.")

    # Check for and close any other popups or modals that might interfere
    try:
        # Common close buttons for modals
        close_buttons = driver.find_elements(By.CSS_SELECTOR, '.modal-close, .close-button, .dismiss-button, [aria-label="Close"]')
        for button in close_buttons:
            if button.is_displayed():
                driver.execute_script("arguments[0].click();", button)
                print("Closed a popup.")
                time.sleep(1)
    except Exception:
        pass  # Ignore if no popups

# Main execution
if __name__ == '__main__':
    # Step 1: Load company symbols and exchanges from CSV
    input_dir = 'input'
    Path(input_dir).mkdir(exist_ok=True)
    input_file = f'{input_dir}/exchanges.csv'

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Please create it in the '{input_dir}' folder.")
        exit(1)

    df = pd.read_csv(input_file)
    if 'symbol' not in df.columns or 'exchange' not in df.columns:
        print("Error: CSV must contain 'symbol' and 'exchange' columns.")
        exit(1)

    companies = df[['symbol', 'exchange']].to_dict('records')

    # Step 2: Open the browser
    print("Opening browser...")
    my_browser = open_new_browser()

    # Step 3: Process each company
    transcript_data = []
    for i, company in enumerate(companies):
        symbol = company['symbol']
        exchange = company['exchange'].lower()  # Ensure lowercase for URL
        print(f"\n[{i+1}/{len(companies)}] Scraping transcripts for {symbol} on {exchange}...")

        url = f'https://www.fool.com/quote/{exchange}/{symbol.lower()}/#quote-earnings-transcripts'
        try:
            my_browser.get(url)

            # Wait for page to load
            WebDriverWait(my_browser, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Handle any popups
            handle_popups(my_browser)

            # Scroll to the transcript section
            try:
                transcript_section = my_browser.find_element(By.ID, "quote-earnings-transcripts")
                my_browser.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'start'});", transcript_section)
                time.sleep(3)  # Wait for section to be fully visible
            except NoSuchElementException:
                print(f"No transcript section found for {symbol}. Check if the company has any transcripts.")
                transcript_data.append({'Company Symbol': symbol, 'Transcript Links': []})
                continue

            # Load all available transcripts
            load_all_transcripts(my_browser)

            # Extract links after all are loaded
            links = get_transcript_links(my_browser)

            # Add to results
            transcript_data.append({'Company Symbol': symbol, 'Transcript Links': links})
            print(f"Found {len(links)} transcripts for {symbol}")

            # Random delay between companies to avoid being detected as a bot
            if i < len(companies) - 1:
                delay = random.uniform(3, 5)
                print(f"Waiting {delay:.1f} seconds before next company...")
                time.sleep(delay)

        except Exception as e:
            print(f"Error processing {symbol}: {str(e)}")
            transcript_data.append({'Company Symbol': symbol, 'Transcript Links': []})

    # Step 4: Close the browser
    my_browser.quit()
    print("\nBrowser closed.")

    # Step 5: Save results to CSV
    output_df = pd.DataFrame(transcript_data)
    output_df['Transcript Links'] = output_df['Transcript Links'].apply(lambda x: ';'.join(x) if x else '')
    output_df['Number of Transcripts'] = output_df['Transcript Links'].apply(lambda x: len(x.split(';')) if x else 0)

    output_file = os.path.join(output_dir, 'transcript_links.csv')
    output_df.to_csv(output_file, index=False)
    print(f"Output saved to {output_file}")

    # Print summary
    total_transcripts = output_df['Number of Transcripts'].sum()
    companies_with_transcripts = (output_df['Number of Transcripts'] > 0).sum()
    print(f"\nSummary: Found {total_transcripts} transcripts across {companies_with_transcripts} companies.")