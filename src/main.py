from data_loader import *

posts = fetch_wp_articles(GYMBEAM_BLOG_URL)
save_to_file(posts, "../data/articles.json")