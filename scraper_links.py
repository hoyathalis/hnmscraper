import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
import csv
import os

base_url = "https://www2.hm.com/en_us/women/products/tops.html"
total_pages = 31

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
]

def fetch_page_links(page_number, session):
    url = f"{base_url}?page={page_number}"
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Referer": base_url
    }
    
    try:
        time.sleep(random.uniform(1, 3))
        response = session.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching page {page_number}: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    links = set()

    product_items = soup.select('#products-listing-section ul li')
    if not product_items:
        print(f"No products found on page {page_number}")
        return None

    for item in product_items:
        section = item.find('section')
        article_tag = section.find('article') if section else None
        data_category = article_tag['data-category'] if article_tag and 'data-category' in article_tag.attrs else 'N/A'

        a_tag = item.select_one('a')
        if a_tag and 'href' in a_tag.attrs:
            href = a_tag['href']
            full_link = href if href.startswith("https://") else "https://www2.hm.com" + href
            if "page=" not in full_link:
                links.add((page_number, full_link, data_category))

    print(f"Page {page_number}: {len(links)} links found")

    return [{'page_number': page_number, 'link': link, 'data_category': data_category} for page_number, link, data_category in links]

def main():
    all_links = set()
    failed_pages = set(range(1, total_pages + 1))
    
    with requests.Session() as session:
        while failed_pages:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(fetch_page_links, page, session): page for page in failed_pages}
                
                for future in as_completed(futures):
                    page = futures[future]
                    try:
                        result = future.result()
                        if result is not None:
                            for link_dict in result:
                                all_links.add((link_dict['page_number'], link_dict['link'], link_dict['data_category']))
                            failed_pages.remove(page)
                        else:
                            print(f"Retrying page {page}")
                    except Exception as e:
                        print(f"Error processing page {page}: {e}")

    file_exists = os.path.isfile('product_links.csv')
    
    with open('product_links.csv', mode='a' if file_exists else 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['page_number', 'link', 'data_category'])
        for page_number, link, data_category in sorted(all_links):
            if data_category != "N/A":
                writer.writerow([page_number, link, data_category])

    print("Links have been saved to product_links.csv")

if __name__ == "__main__":
    main()