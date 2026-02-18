import json
import requests

GYMBEAM_BLOG_URL = "https://gymbeam.sk/blog"
ARTICLES_PATH = "../data/articles.json"


def fetch_wp_articles(base_url, per_page=10):
    url = f"{base_url}/wp-json/wp/v2/posts?per_page={per_page}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def save_to_file(data, filename=ARTICLES_PATH):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_from_file(filename=ARTICLES_PATH):
    with open(filename, encoding="utf-8") as f:
        return json.load(f)


def load_articles_wrapper(from_file=False, file_name=ARTICLES_PATH, per_page=10):
    if from_file:
        return load_from_file(file_name)
    return fetch_wp_articles(GYMBEAM_BLOG_URL, per_page)


def strip_article(post):
    data = {
        "id": post["id"],
        "url": post["link"],
        "title": post["title"]["rendered"],
        "content_html": post["content"]["rendered"],
        "meta_description": post.get("yoast_head_json", {}).get("description", "")
    }
    return json.dumps(data, ensure_ascii=False, indent=2)
