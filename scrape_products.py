import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import random
import time
import json
import re

# Load links from CSV, limiting to the first 10 for testing
input_file = "product_links.csv"
output_file = "product_details.csv"

df_links = pd.read_csv(input_file)  # Only the first 10 links for testing

# List of User-Agent strings to rotate
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
]

# Headers to mimic a browser request more closely
base_headers = {
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Connection": "keep-alive",
}

def fetch_product_details(url, category, max_retries=20):
    for attempt in range(max_retries):
        headers = base_headers.copy()
        headers["User-Agent"] = random.choice(user_agents)  # Rotate User-Agent
        
        try:
            # Random delay between 1 and 5 seconds for each request
            time.sleep(random.uniform(1, 5))

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract required information
            product_name = soup.find("h1", {"class": "fa226d af6753 d582fb"}).get_text(strip=True) if soup.find("h1", {"class": "fa226d af6753 d582fb"}) else None
            description = soup.find("p", {"class": "d1cd7b ca7db2 e2b79d"}).get_text(strip=True) if soup.find("p", {"class": "d1cd7b ca7db2 e2b79d"}) else None
            product_url = url
            
            sleeve = neckline = color = None
            for div in soup.select("#section-descriptionAccordion div.ecc0f3"):
                label = div.find("dt").get_text(strip=True) if div.find("dt") else None
                value = div.find("dd").get_text(strip=True) if div.find("dd") else None
                
                if label == "Sleeve Length:":
                    sleeve = value
                elif label == "Neckline:":
                    neckline = value
                elif label == "Description:":
                    color = value  # Assume Description here holds the color

            return {
                "Product Name": product_name,
                "Description": description,
                "Product URL": product_url,
                "Sleeve Length": sleeve,
                "Neckline": neckline,
                "Color": color,
                "Category": category,
            }
        except Exception as e:
            print(f"Error fetching {url} (Attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return None
            time.sleep(random.uniform(5, 10))  # Wait longer between retries

# Use ThreadPoolExecutor to fetch data concurrently with tqdm for progress display
results = []
failed_urls = []

with ThreadPoolExecutor(max_workers=10) as executor:
    # Create a list of futures
    futures = {
        executor.submit(fetch_product_details, row['link'], row['data_category']): row['link']
        for _, row in df_links.iterrows()
    }
    
    # Use tqdm to display progress
    for future in tqdm(as_completed(futures), total=len(futures), desc="Fetching product details"):
        url = futures[future]
        try:
            data = future.result()
            if data:
                results.append(data)
            else:
                failed_urls.append(url)
        except Exception as e:
            print(f"An error occurred for {url}: {e}")
            failed_urls.append(url)

# Retry failed URLs
if failed_urls:
    print(f"Retrying {len(failed_urls)} failed URLs...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        retry_futures = {
            executor.submit(fetch_product_details, url, df_links[df_links['link'] == url]['data_category'].iloc[0], max_retries=2): url
            for url in failed_urls
        }
        
        for future in tqdm(as_completed(retry_futures), total=len(retry_futures), desc="Retrying failed URLs"):
            url = retry_futures[future]
            try:
                data = future.result()
                if data:
                    results.append(data)
                    failed_urls.remove(url)
                else:
                    print(f"Failed to fetch after retry: {url}")
            except Exception as e:
                print(f"Failed to fetch after retry for {url}: {e}")

# Save results to CSV
df_results = pd.DataFrame(results)
df_results.to_csv(output_file, index=False)
print(f"Results saved to {output_file}")
print(f"Total successful fetches: {len(results)}")
print(f"Total failed fetches: {len(failed_urls)}")