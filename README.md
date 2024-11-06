# H&M Product Scraper

This project scrapes product links and details from the H&M women's tops section on their website. The scraper is designed to efficiently collect product information using concurrent requests and rotating user-agent headers to mimic real browser requests.

## Features

- **Product Link Scraper**: Collects product URLs and categories from each page in the women's tops section.
- **Product Details Scraper**: Extracts detailed information about each product, including name, description, sleeve length, neckline, color, and category.

## Setup

1. **Clone the repository**:
   ```bash
   git clone <repository_url>
   cd hnm-product-scraper
   ```
2. **Install dependencies:** Install the required packages by running:

   ```bash
  pip install -r requirements.txt
   ```

## Files
* product_link_scraper.py: Fetches product links and categories for each page.
* product_details_scraper.py: Uses the collected links to extract detailed information for each product.
* product_links.csv: Stores the product links and their categories.
* product_details.csv: Stores detailed information about each product.