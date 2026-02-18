from bs4 import BeautifulSoup
import re

WHITESPACE_RE = re.compile(r"\s+")

class Article:
    def __init__(self, article):
        self.id = article["id"]
        self.url = article["link"]
        self.title = article["title"]["rendered"]
        self.content_html = article["content"]["rendered"]
        self.content_clean = self._get_clean_content_html()
        self.meta_description = article.get("yoast_head_json", {}).get("description", "")

        self.score: int = 0
        self.report: dict[str, bool] = dict()
        self.recommendations: list[str] = list()

    def _add_to_report(self, name:str, passed: bool, recommendation: str):
        self.report[name] = passed
        self.score += passed
        if not passed:
            self.recommendations.append(recommendation)

    def _get_clean_content_html(self) -> str:
        soup = BeautifulSoup(self.content_html, "html.parser")

        toc = soup.find("div", id="ez-toc-container")
        if toc:
            toc.decompose()

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        clean_text = soup.get_text(separator=" ")
        clean_text = WHITESPACE_RE.sub(" ", clean_text).strip()

        return clean_text

    def _get_first_paragraph(self) -> str:
        soup = BeautifulSoup(self.content_html, "html.parser")

        toc = soup.find("div", id="ez-toc-container")
        if toc:
            toc.decompose()

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        first_p = soup.select_one("p")
        if not first_p:
            return ""

        paragraph = WHITESPACE_RE.sub(" ", first_p.get_text()).strip()
        return paragraph

    # 1
    def analyze_direct_answer(self):
        forbidden_phrases = ["v tomto článku", "poďme sa pozrieť", "dozviete sa", "povieme si"]

        intro = self._get_first_paragraph().lower()
        found_phrases = [p for p in forbidden_phrases if p in intro]

        passed = len(found_phrases) == 0

        recommendation = f"Odstrániť nechcené frázy ({found_phrases})."
        self._add_to_report("direct_answer", passed, recommendation)

    # 2
    def _contains_definition_in_what_is_segment(self) -> bool:
        soup = BeautifulSoup(self.content_html, "html.parser")

        toc = soup.find("div", id="ez-toc-container")
        if not toc:
            return False

        toc_text = toc.get_text(" ", strip=True).lower()

        return "čo je" in toc_text or "čo sú" in toc_text

    def _contains_definition_by_title(self) -> bool:
        """
        Jednoduchá kontrola definície:
        - title musí obsahovať ':'
        - časť naľavo je X (max 2 slová)
        - v texte sa hľadá: 'X je', 'X znamená', 'X predstavuje'
        """

        if ":" not in self.title:
            return False

        potential_keyword = self.title.split(":", 1)[0].strip()
        words = potential_keyword.split()
        if len(words) > 2 or not potential_keyword or potential_keyword.lower()  == "fitness recept":
            return False

        text = re.sub(r"\s+", " ", self.content_clean).lower()
        keyword = potential_keyword.lower()

        patterns = [
            f"{keyword} je",
            f"{keyword} sú",
            f"{keyword} znamená",
            f"{keyword} predstavuje"]

        return any(p in text for p in patterns)

    def analyze_definition(self):
        passed =  (self._contains_definition_in_what_is_segment()
                   or self._contains_definition_by_title())

        recommendation = "Pridať priamu definíciu hlavného pojmu."
        self._add_to_report("definition", passed, recommendation)


    # 3
    def analyze_headings(self):
        soup = BeautifulSoup(self.content_html, "html.parser")

        count = len(soup.find_all("h2"))

        passed = True if count >= 3 else False

        recommendation = f"Pridať nadpisy v počte aspoň {3-count}."
        self._add_to_report("headings", passed, recommendation)

    # 4
    def analyze_facts(self):
        facts_regex = re.compile(
            r"\d+\s?(mg|g|kg|%|kcal|ml|mcg|gramov|miligramov)",
            re.IGNORECASE
        )
        matches = facts_regex.findall(self.content_clean)
        count = len(matches)

        passed = True if count >= 3 else False

        recommendation = f"Pridať číselné údaje s jednotkami v počte aspoň {3-count}."
        self._add_to_report("facts", passed, recommendation)

    # 5
    def analyze_sources(self):
        soup = BeautifulSoup(self.content_html, "html.parser")

        source_text_regex = re.compile(
            r"\b(zdroje|references|štúdie)\b",
            re.IGNORECASE
        )
        source_domains = (
            "pubmed.ncbi.nlm.nih.gov",
            "examine.com",
        )

        # 1. kontrola odkazov na známe zdroje
        # TODO: check ci links su plne url, alebo len domeny
        links = [a.get("href", "") for a in soup.find_all("a", href=True)]
        has_scientific_link = any(
            domain in link for link in links for domain in source_domains
        )

        # 2. kontrola textových výrazov
        has_source_text = bool(source_text_regex.search(self.content_clean))

        passed = has_scientific_link or has_source_text

        recommendation = 'Pridať sekciu "Zdroje".'
        self._add_to_report("sources", passed, recommendation)

    # 6
    def analyze_faq(self):
        soup = BeautifulSoup(self.content_html, "html.parser")

        faq_regex = re.compile(
            r"\b(f&q|faq|často kladené otázky|otázky a odpovede)\b",
            re.IGNORECASE
        )

        headings_text = " ".join(
            h.get_text(strip=True)
            for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        )

        has_faq_heading = bool(faq_regex.search(headings_text))
        has_faq_text = bool(faq_regex.search(self.content_clean))

        passed = has_faq_heading or has_faq_text

        recommendation = "Pridať F&Q sekciu."
        self._add_to_report("faq", passed, recommendation)

    # 7
    def analyze_lists(self):
        soup = BeautifulSoup(self.content_html, "html.parser")

        has_ul = soup.find("ul") is not None
        has_ol = soup.find("ol") is not None

        passed = has_ul or has_ol

        recommendation = "Pridať aspoň 1 odrážkový alebo očíslovaný zoznam."
        self._add_to_report("lists", passed, recommendation)

    # 8
    def analyze_tables(self):
        soup = BeautifulSoup(self.content_html, "html.parser")

        passed = soup.find("table") is not None

        recommendation = "Pridať aspoň 1 tabuľku."
        self._add_to_report("tables", passed, recommendation)

    # 9
    def analyze_word_count_ok(self, min_words: int = 500):
        words = self.content_clean.split()
        word_count = len(words)

        passed = word_count >= min_words

        recommendation = f"Článok nie je dostatočne dlhý, pridať aspoň {min_words - word_count} slov."
        self._add_to_report("word_count_ok", passed, recommendation)

    # 10
    def analyze_meta_ok(self, min_len: int = 120, max_len: int = 160):
        length = len(self.meta_description.strip())
        passed = min_len <= length <= max_len

        recommendation = ""
        if length < min_len:
            recommendation = f"Meta popis je prikrátky, pridať aspoň {min_len - length} slov."
        elif length > max_len:
            recommendation = f"Meta popis je pridlhý, ubrať aspoň {length - max_len} slov."
        self._add_to_report("meta_ok", passed, recommendation)
