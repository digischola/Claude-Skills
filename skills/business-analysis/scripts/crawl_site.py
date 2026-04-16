#!/usr/bin/env python3
"""
Website Crawler for Business Analysis Skill

Fetches a business website and extracts structured data:
- Page inventory (from sitemap.xml or internal links)
- Per-page: title, meta description, headings, links, key content
- Social media links
- Structured data (JSON-LD if present)

Usage:
    python crawl_site.py <url> [--max-pages 20] [--depth 2]

Output:
    JSON object with crawl results to stdout
"""

import sys
import json
import re
import time
from urllib.request import urlopen, Request
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser
from xml.etree import ElementTree


DEFAULT_MAX_PAGES = 20
DEFAULT_DEPTH = 2
USER_AGENT = "Mozilla/5.0 (compatible; BusinessAnalysisCrawler/1.0)"
TIMEOUT = 15


class PageParser(HTMLParser):
    """Extract structured data from a single HTML page."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta_description = ""
        self.headings = []  # (level, text)
        self.links = []  # internal links
        self.social_links = []
        self.images = []
        self.jsonld = []
        self.current_tag = None
        self.current_attrs = {}
        self.tag_content = ""
        self.in_heading = False
        self.heading_level = 0
        self.in_title = False
        self.in_script = False
        self.script_type = ""
        self.script_content = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self.current_tag = tag
        self.current_attrs = attrs_dict

        if tag == "title":
            self.in_title = True
            self.tag_content = ""

        if tag in ("h1", "h2", "h3"):
            self.in_heading = True
            self.heading_level = int(tag[1])
            self.tag_content = ""

        if tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            content = attrs_dict.get("content", "")
            if name == "description" or prop == "og:description":
                self.meta_description = content.strip()

        if tag == "a":
            href = attrs_dict.get("href", "")
            if href:
                self.links.append(href)
                # Detect social media links
                social_domains = [
                    "facebook.com", "instagram.com", "twitter.com", "x.com",
                    "linkedin.com", "youtube.com", "tiktok.com", "pinterest.com",
                ]
                for domain in social_domains:
                    if domain in href:
                        self.social_links.append(href)
                        break

        if tag == "img":
            src = attrs_dict.get("src", "")
            alt = attrs_dict.get("alt", "")
            if src:
                self.images.append({"src": src, "alt": alt})

        if tag == "script":
            script_type = attrs_dict.get("type", "")
            if "json" in script_type.lower():
                self.in_script = True
                self.script_content = ""

    def handle_data(self, data):
        if self.in_title:
            self.tag_content += data
        if self.in_heading:
            self.tag_content += data
        if self.in_script:
            self.script_content += data

    def handle_endtag(self, tag):
        if tag == "title" and self.in_title:
            self.in_title = False
            self.title = self.tag_content.strip()

        if tag in ("h1", "h2", "h3") and self.in_heading:
            self.in_heading = False
            text = self.tag_content.strip()
            if text:
                self.headings.append((self.heading_level, text))

        if tag == "script" and self.in_script:
            self.in_script = False
            try:
                data = json.loads(self.script_content)
                self.jsonld.append(data)
            except (json.JSONDecodeError, ValueError):
                pass


def fetch_page(url):
    """Fetch a URL and return HTML content."""
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=TIMEOUT) as response:
            content_type = response.headers.get("Content-Type", "")
            if "html" not in content_type.lower() and "text" not in content_type.lower():
                return None
            return response.read().decode("utf-8", errors="replace")
    except Exception as e:
        return None


def fetch_sitemap(base_url):
    """Try to fetch and parse sitemap.xml."""
    sitemap_urls = [
        urljoin(base_url, "/sitemap.xml"),
        urljoin(base_url, "/sitemap_index.xml"),
    ]

    for sitemap_url in sitemap_urls:
        try:
            req = Request(sitemap_url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=TIMEOUT) as response:
                content = response.read().decode("utf-8", errors="replace")
                # Parse XML
                root = ElementTree.fromstring(content)
                # Handle namespace
                ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                urls = []
                # Try standard sitemap
                for url_elem in root.findall(".//sm:url/sm:loc", ns):
                    urls.append(url_elem.text.strip())
                # Try without namespace
                if not urls:
                    for url_elem in root.findall(".//url/loc"):
                        urls.append(url_elem.text.strip())
                if urls:
                    return urls
        except Exception:
            continue

    return []


def extract_internal_links(html, base_url):
    """Extract internal links from HTML."""
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc

    links = re.findall(r'href=["\']([^"\']+)["\']', html)
    internal = set()

    for link in links:
        # Skip anchors, javascript, mailto
        if link.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        full_url = urljoin(base_url, link)
        parsed = urlparse(full_url)

        # Only same domain
        if parsed.netloc == base_domain:
            # Clean URL (remove fragments and query params for dedup)
            clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if clean.endswith("/"):
                clean = clean[:-1]
            internal.add(clean)

    return list(internal)


def classify_page(url, title, headings):
    """Classify a page type based on URL and content."""
    url_lower = url.lower()
    title_lower = (title or "").lower()
    h_text = " ".join(h[1].lower() for h in headings)

    patterns = {
        "homepage": lambda: url_lower.rstrip("/") == urlparse(url).scheme + "://" + urlparse(url).netloc,
        "about": lambda: any(k in url_lower for k in ["/about", "/our-story", "/who-we-are", "/team"]),
        "services": lambda: any(k in url_lower for k in ["/service", "/what-we-do", "/programs", "/offerings"]),
        "pricing": lambda: any(k in url_lower for k in ["/pricing", "/rates", "/packages", "/plans"]),
        "contact": lambda: any(k in url_lower for k in ["/contact", "/get-in-touch", "/location"]),
        "testimonials": lambda: any(k in url_lower for k in ["/testimonial", "/review", "/success-stories"]),
        "blog": lambda: any(k in url_lower for k in ["/blog", "/news", "/articles", "/resources"]),
        "faq": lambda: any(k in url_lower for k in ["/faq", "/frequently-asked"]),
        "booking": lambda: any(k in url_lower for k in ["/book", "/reserve", "/schedule", "/register"]),
        "gallery": lambda: any(k in url_lower for k in ["/gallery", "/photos", "/portfolio"]),
    }

    for page_type, check in patterns.items():
        if check():
            return page_type

    return "other"


def crawl_site(base_url, max_pages=DEFAULT_MAX_PAGES, max_depth=DEFAULT_DEPTH):
    """Main crawl function."""
    if not base_url.startswith("http"):
        base_url = "https://" + base_url
    base_url = base_url.rstrip("/")

    results = {
        "base_url": base_url,
        "sitemap_found": False,
        "pages_crawled": 0,
        "pages": [],
        "social_links": [],
        "errors": [],
    }

    # Step 1: Try sitemap
    sitemap_urls = fetch_sitemap(base_url)
    if sitemap_urls:
        results["sitemap_found"] = True
        urls_to_crawl = sitemap_urls[:max_pages]
    else:
        # Step 2: Crawl from homepage
        urls_to_crawl = [base_url]

    crawled = set()
    all_social = set()
    queue = [(url, 0) for url in urls_to_crawl]

    while queue and len(crawled) < max_pages:
        url, depth = queue.pop(0)

        # Normalize
        url = url.rstrip("/")
        if url in crawled:
            continue

        # Skip non-HTML resources
        skip_extensions = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".css", ".js", ".xml", ".zip")
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            continue

        html = fetch_page(url)
        if html is None:
            results["errors"].append(f"Failed to fetch: {url}")
            continue

        crawled.add(url)

        # Parse page
        parser = PageParser()
        try:
            parser.feed(html)
        except Exception as e:
            results["errors"].append(f"Parse error on {url}: {str(e)}")
            continue

        page_type = classify_page(url, parser.title, parser.headings)

        page_data = {
            "url": url,
            "type": page_type,
            "title": parser.title,
            "meta_description": parser.meta_description,
            "headings": [{"level": h[0], "text": h[1]} for h in parser.headings[:20]],
            "image_count": len(parser.images),
            "jsonld": parser.jsonld if parser.jsonld else None,
        }

        results["pages"].append(page_data)
        all_social.update(parser.social_links)

        # Discover more internal links (if not from sitemap and within depth)
        if not results["sitemap_found"] and depth < max_depth:
            internal_links = extract_internal_links(html, url)
            for link in internal_links:
                if link not in crawled:
                    queue.append((link, depth + 1))

        # Be polite
        time.sleep(0.5)

    results["pages_crawled"] = len(crawled)
    results["social_links"] = sorted(all_social)

    # Sort pages by type priority
    type_priority = {
        "homepage": 0, "about": 1, "services": 2, "pricing": 3,
        "testimonials": 4, "contact": 5, "booking": 6, "faq": 7,
        "blog": 8, "gallery": 9, "other": 10,
    }
    results["pages"].sort(key=lambda p: type_priority.get(p["type"], 10))

    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python crawl_site.py <url> [--max-pages 20] [--depth 2]")
        sys.exit(1)

    url = sys.argv[1]
    max_pages = DEFAULT_MAX_PAGES
    max_depth = DEFAULT_DEPTH

    # Parse optional args
    args = sys.argv[2:]
    for i, arg in enumerate(args):
        if arg == "--max-pages" and i + 1 < len(args):
            max_pages = int(args[i + 1])
        if arg == "--depth" and i + 1 < len(args):
            max_depth = int(args[i + 1])

    results = crawl_site(url, max_pages, max_depth)
    print(json.dumps(results, indent=2))

    # Summary to stderr
    import sys as _sys
    _sys.stderr.write(f"\n--- Crawl Summary ---\n")
    _sys.stderr.write(f"URL: {results['base_url']}\n")
    _sys.stderr.write(f"Sitemap found: {results['sitemap_found']}\n")
    _sys.stderr.write(f"Pages crawled: {results['pages_crawled']}\n")
    _sys.stderr.write(f"Social links: {len(results['social_links'])}\n")
    if results["errors"]:
        _sys.stderr.write(f"Errors: {len(results['errors'])}\n")
    _sys.stderr.write(f"\nPage types found:\n")
    type_counts = {}
    for page in results["pages"]:
        t = page["type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    for t, count in sorted(type_counts.items()):
        _sys.stderr.write(f"  {t}: {count}\n")


if __name__ == "__main__":
    main()
