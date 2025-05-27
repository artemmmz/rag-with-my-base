import os
import time
import json
import tarfile
import feedparser
import re
import requests
import fitz

QUERIES = [
    "machine learning", "natural language processing", "generative pre-trained transformer",
]


def clean_latex_source(text):
    text = re.sub(r"\\documentclass(\[.*?\])?\{.*?\}", "", text)
    text = re.sub(r"\\usepackage(\[.*?\])?\{.*?\}", "", text)
    text = re.sub(r"\\input\{.*?\}", "", text)
    text = re.sub(r"\\include\{.*?\}", "", text)
    text = re.sub(r"(?<!\\)%.*", "", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()


def fetch_arxiv_articles(query, max_results=50, output_dir="arxiv_data", save_jsonl=True):
    base_url = "http://export.arxiv.org/api/query?"
    query = query.replace(" ", "+")
    batch_size = 20

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    results = []
    jsonl_path = "arxiv_dataset.jsonl"

    for start in range(0, max_results, batch_size):
        url = f"{base_url}search_query=all:{query}&start={start}&max_results={batch_size}"
        print(f"Fetching: {url}")
        feed = feedparser.parse(url)
        if not feed.entries:
            break

        for entry in feed.entries:
            title = entry.title.strip().replace("\n", " ")
            summary = entry.summary.strip().replace("\n", " ")
            article_id = entry.id.split("/")[-1]
            arxiv_url = f"https://arxiv.org/abs/{article_id}"

            source_url = f"https://arxiv.org/e-print/{article_id}"
            print(f"Downloading source: {source_url}")

            try:
                response = requests.get(source_url)
                response.raise_for_status()
                archive_path = os.path.join(output_dir, f"{article_id}.tar.gz")

                with open(archive_path, "wb") as f:
                    f.write(response.content)

                tex_dir = os.path.join(output_dir, article_id)
                os.makedirs(tex_dir, exist_ok=True)

                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(path=tex_dir)

                tex_contents = []
                for root, _, files in os.walk(tex_dir):
                    for file in files:
                        if file.endswith(".tex"):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                    content = f.read()
                                    tex_contents.append(f"% FILE: {file}\n" + content)
                            except Exception as e:
                                print(f"Failed to read {file_path}: {e}")

                full_tex = "\n\n".join(tex_contents)
                full_tex = clean_latex_source(full_tex)

                record = {
                    "id": article_id,
                    "title": title,
                    "summary": summary,
                    "content": full_tex,
                    "arxiv_url": arxiv_url,
                }

                if save_jsonl:
                    with open(jsonl_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")

            except Exception as e:
                print(f"Failed to fetch or extract: {e}")

        time.sleep(1)

    print(f"Collected {len(results)} articles.")
    return results

if __name__ == "__main__":
    for query in QUERIES:
        fetch_arxiv_articles(
            query=query,
            max_results=200,
            save_jsonl=True
        )
