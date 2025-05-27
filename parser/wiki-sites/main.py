import requests
from bs4 import BeautifulSoup

import json
import time
import re
from urllib.parse import urljoin

WIKIS = [
    ("https://neerc.ifmo.ru", "/wiki/index.php?title=Заглавная_страница", "ifmo_dataset.jsonl"),
]

def is_valid_link(href):
    return href and href.startswith("/wiki/") and not any(x in href for x in [":", "#"])

def clean_content(soup):
    for sup in soup.select("sup.reference"):
        sup.decompose()
    for span in soup.select(".mw-editsection"):
        span.decompose()
    for div in soup.select(".hatnote, .navbox, .toc, .metadata, .vertical-navbox, .reflist"):
        div.decompose()

    content = []
    content_container = soup.select_one("div.mw-parser-output")
    if not content_container:
        return content

    for tag in content_container.children:
        if tag.name == "p":
            text = tag.get_text(strip=True)
            if text:
                text = re.sub(r'\[\d+\]', '', text)
                text = re.sub(r'\s+', ' ', text)
                content.append(text)
        elif tag.name in ["ul", "ol"]:
            for li in tag.find_all("li"):
                item = li.get_text(strip=True)
                if item:
                    item = re.sub(r'\[\d+\]', '', item)
                    item = re.sub(r'\s+', ' ', item)
                    content.append(f"- {item}")

    return content

def extract_internal_links(soup):
    links = set()
    for link in soup.select("div.mw-parser-output a[href]"):
        href = link.get("href")
        if is_valid_link(href):
            links.add(href)
    return list(links)

def scrape_page(base_url: str, uri: str):
    full_url = urljoin(base_url, uri)
    print(f"Scraping: {full_url}")
    response = requests.get(full_url, headers={"User-Agent": "WikiScraper/1.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.find('h1').text if soup.find('h1') else "No Title"
    content = clean_content(soup)
    internal_links = extract_internal_links(soup)

    return {
        "url": full_url,
        "title": title,
        "content": " ".join(content)
    }, internal_links

def collect_data_to_jsonl(
        base_url: str, start_page: str, max_pages: int = 50, output_path: str = "wiki_dataset.jsonl"
) -> None:
    to_visit = [start_page]
    visited = set()

    with open(output_path, "w", encoding="utf-8") as f_out:
        while to_visit and len(visited) < max_pages:
            current = to_visit.pop(0)
            if current in visited:
                continue

            try:
                data, internal_links = scrape_page(base_url, current)
                visited.add(current)

                json_line = json.dumps(data, ensure_ascii=False)
                f_out.write(json_line + "\n")

                for href in internal_links:
                    if href not in visited and href not in to_visit:
                        to_visit.append(href)

                time.sleep(1)
            except Exception as e:
                print(f"Error scraping {current}: {e}")

    print(f"End scraping. Total pages: {len(visited)}")

if __name__ == "__main__":
    for wiki_site in WIKIS:
        print(f"Current wiki host: {wiki_site[0]}")
        collect_data_to_jsonl(wiki_site[0], wiki_site[1], max_pages=10000, output_path=wiki_site[2])
