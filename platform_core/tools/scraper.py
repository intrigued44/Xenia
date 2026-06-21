import re
import urllib.parse
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

class WebScraper:
    """Helper class for scraping web content cleanly for Xenia workflows."""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]

    @classmethod
    def get_headers(cls) -> Dict[str, str]:
        import random
        return {
            "User-Agent": random.choice(cls.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }

    @classmethod
    def scrape_text(cls, url: str, selector: Optional[str] = None, use_playwright: bool = False) -> str:
        """Fetches a URL and extracts readable text or specific elements."""
        if use_playwright:
            return cls._scrape_text_playwright(url, selector)
        
        try:
            resp = requests.get(url, headers=cls.get_headers(), timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Remove scripts and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            if selector:
                elements = soup.select(selector)
                if not elements:
                    return ""
                return "\n".join([el.get_text(separator=' ', strip=True) for el in elements])
            
            # Default to extracting body text
            text = soup.get_text(separator=' ', strip=True)
            # Remove double spaces/newlines
            text = re.sub(r'\s+', ' ', text)
            return text
        except Exception as e:
            # Fallback to Playwright if request failed
            print(f"[WebScraper] Requests fetch failed ({e}). Retrying with Playwright...")
            return cls._scrape_text_playwright(url, selector)

    @classmethod
    def scrape_table(cls, url: str, table_selector: Optional[str] = None, use_playwright: bool = False) -> List[Dict[str, Any]]:
        """Scrapes table rows from a page and returns them as a list of dicts."""
        if use_playwright:
            return cls._scrape_table_playwright(url, table_selector)

        try:
            resp = requests.get(url, headers=cls.get_headers(), timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            table = None
            if table_selector:
                table = soup.select_one(table_selector)
            else:
                table = soup.find('table')
                
            if not table:
                print(f"[WebScraper] No table found at {url}")
                # Try Playwright
                return cls._scrape_table_playwright(url, table_selector)
                
            return cls._parse_html_table(table)
        except Exception as e:
            print(f"[WebScraper] Requests table fetch failed ({e}). Retrying with Playwright...")
            return cls._scrape_table_playwright(url, table_selector)

    @classmethod
    def _parse_html_table(cls, table_element) -> List[Dict[str, Any]]:
        """Parses a BeautifulSoup table element into list of dictionaries."""
        headers = []
        rows_data = []
        
        # Get headers
        thead = table_element.find('thead')
        if thead:
            header_cells = thead.find_all(['th', 'td'])
        else:
            first_row = table_element.find('tr')
            if first_row:
                header_cells = first_row.find_all(['th', 'td'])
            else:
                header_cells = []
                
        headers = [cell.get_text(strip=True) for cell in header_cells]
        
        # Clean headers to prevent empty keys
        headers = [h or f"Column_{i}" for i, h in enumerate(headers)]
        
        # Get body rows
        tbody = table_element.find('tbody')
        rows = tbody.find_all('tr') if tbody else table_element.find_all('tr')
        
        # If the first row was headers, skip it
        if not thead and rows:
            rows = rows[1:]
            
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if not cells:
                continue
            row_dict = {}
            for i, cell in enumerate(cells):
                cell_text = cell.get_text(strip=True)
                header_name = headers[i] if i < len(headers) else f"Column_{i}"
                row_dict[header_name] = cell_text
            if row_dict:
                rows_data.append(row_dict)
                
        return rows_data

    @classmethod
    def _scrape_text_playwright(cls, url: str, selector: Optional[str] = None) -> str:
        """Playwright-based text extractor for dynamic websites."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[WebScraper] Playwright not installed. Check requirements.txt.")
            return ""

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=30000)
                
                if selector:
                    page.wait_for_selector(selector, timeout=10000)
                    elements = page.locator(selector).all_text_contents()
                    browser.close()
                    return "\n".join(elements)
                
                # Default extract entire body
                body_text = page.locator("body").inner_text()
                browser.close()
                return body_text
        except Exception as e:
            print(f"[WebScraper] Playwright text scrape failed: {e}")
            return ""

    @classmethod
    def _scrape_table_playwright(cls, url: str, table_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        """Playwright-based HTML table scraper for dynamic websites."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[WebScraper] Playwright not installed. Check requirements.txt.")
            return []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=30000)
                
                sel = table_selector or "table"
                page.wait_for_selector(sel, timeout=10000)
                html_content = page.locator(sel).first.evaluate("el => el.outerHTML")
                browser.close()
                
                soup = BeautifulSoup(html_content, 'html.parser')
                return cls._parse_html_table(soup.find('table') or soup)
        except Exception as e:
            print(f"[WebScraper] Playwright table scrape failed: {e}")
            return []
