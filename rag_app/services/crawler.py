import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

CRAWLED_DATA_PATH = "data/crawled_data"

# Ensure crawled data directory exists
os.makedirs(CRAWLED_DATA_PATH, exist_ok=True)


class WebCrawler:
    """Handle web crawling operations"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def _is_valid_url(self, url):
        """Check if URL is valid and crawlable"""
        try:
            parsed = urlparse(url)
            return all([parsed.scheme, parsed.netloc])
        except:
            return False

    def _extract_text_from_html(self, html_content):
        """Extract clean text from HTML"""
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text and clean it
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = "\n".join(chunk for chunk in chunks if chunk)

            return text
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""

    def crawl(self, url, max_length=5000):
        """Crawl a single URL and extract text content"""
        if not self._is_valid_url(url):
            return None

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()
            if "html" not in content_type:
                return None

            text_content = self._extract_text_from_html(response.content)

            # Truncate if too long
            if len(text_content) > max_length:
                text_content = text_content[:max_length] + "..."

            return {
                "url": url,
                "title": self._extract_title(response.content),
                "content": text_content,
                "timestamp": datetime.now().isoformat(),
                "content_length": len(text_content),
            }
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return None

    def _extract_title(self, html_content):
        """Extract page title from HTML"""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            title_tag = soup.find("title")
            return title_tag.get_text().strip() if title_tag else "No title"
        except:
            return "No title"

    def crawl_multiple_urls(self, urls, max_workers=5):
        """Crawl multiple URLs concurrently"""
        crawled_data = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self.crawl, url): url for url in urls}

            for future in as_completed(future_to_url):
                result = future.result()
                if result:
                    crawled_data.append(result)

        return crawled_data

    def save_crawled_data(self, crawled_data):
        """Save crawled data and update knowledge base"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crawled_{timestamp}.json"
        filepath = os.path.join(CRAWLED_DATA_PATH, filename)

        with open(filepath, "w") as f:
            json.dump(crawled_data, f, indent=2)

        return filepath
