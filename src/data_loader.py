import json
import requests

from src.utils import DATA_DIR

GYMBEAM_BLOG_URL = "https://gymbeam.sk/blog"
ARTICLES_PATH = DATA_DIR / "articles.json"


def fetch_wp_posts(base_url, per_page=10) -> list[dict]:
    """
    Fetch posts from a WordPress REST API.

    This function queries the `/wp-json/wp/v2/posts` endpoint of the given
    WordPress site and retrieves a limited number of posts.

    Args:
        base_url: Base URL of the WordPress site.
        per_page: Maximum number of posts to fetch.

    Returns:
        A list of post objects as returned by the WordPress REST API.

    Raises:
        requests.HTTPError: If the HTTP request returns a non-2xx status.
        requests.RequestException: If a network-related error occurs.
    """
    url = f"{base_url}/wp-json/wp/v2/posts?per_page={per_page}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def save_posts_to_file(data, filename=ARTICLES_PATH) -> None:
    """
    Save post data to a JSON file.

    Args:
        data: a list of WordPress post objects.
        filename: Destination file path.

    Raises:
        OSError: If the file cannot be written.
        TypeError: If the provided data is not JSON serializable.
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        raise OSError(f"Failed to write posts to {filename}") from exc
    except TypeError as exc:
        raise TypeError("Post data is not JSON serializable") from exc


def load_posts_from_file(filename=ARTICLES_PATH, per_page=10) -> list[dict]:
    """
    Load posts from a local JSON file.

    Args:
        filename: Path to the JSON file containing stored posts.
        per_page: Maximum number of posts to return.

    Returns:
        A list of post objects loaded from the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file contains invalid JSON.
        OSError: If the file cannot be read.
    """
    try:
        with open(filename, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Posts file not found: {filename}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in posts file: {filename}") from exc
    except OSError as exc:
        raise OSError(f"Failed to read posts file: {filename}") from exc

    return data[:per_page]


def load_posts_wrapper(use_wp=True, file_name=ARTICLES_PATH, per_page=10) -> list[dict]:
    """
    Load posts either from the WordPress API or from a local file.

    Args:
        use_wp: If True, fetch posts from the WordPress API.
            If False, load posts from a local JSON file.
        file_name: Path to the local JSON file used when `use_wp` is False.
        per_page: Maximum number of posts to return.

    Returns:
        A list of post objects from the selected data source.
    """
    if not use_wp:
        return load_posts_from_file(file_name, per_page)
    return fetch_wp_posts(GYMBEAM_BLOG_URL, per_page)
