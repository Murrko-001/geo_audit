import csv
from typing import Any
from src.analyzer import Article

EXPORT_PATH = "../output/report.csv"

class Reporter:
    def __init__(self):
        self.columns = [
            "url",
            "title",
            "score",
            "direct_answer",
            "definition",
            "headings",
            "facts",
            "sources",
            "faq",
            "lists",
            "tables",
            "word_count_ok",
            "meta_ok",
            "recommendations",
        ]

        self.rows: list[dict[str, Any]] = []

    def add_article(self, article: "Article") -> None:
        result = article.analyze()
        report = result.get("report")
        recs = result.get("recommendations")

        row = {k: int(v) for k, v in report.items()}
        row["url"] = result.get("url")
        row["title"] = result.get("title")
        row["score"] = result.get("score")
        row["recommendations"] = " | ".join(recs)

        self.rows.append(row)
        print(row)

    def export_csv(self, filename: str = EXPORT_PATH) -> None:
        with open(filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.columns)
            writer.writeheader()

            for row in self.rows:
                writer.writerow(row)