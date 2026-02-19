import warnings
from bs4 import BeautifulSoup
import re

from src.utils import inflection

WHITESPACE_RE = re.compile(r"\s+")


class Article:
    """
    Represent and analyze a single WordPress article.

    An `Article` instance wraps the raw WordPress post payload and exposes
    multiple analysis methods that evaluate content quality, structure, and
    metadata. Results are accumulated into a score, a per-check report, and
    human-readable recommendations.
    """
    def __init__(self, post):
        """
        Args:
            post: Dictionary representing a WordPress post object.

        Attributes:
            self.id: Unique post identifier.
            self.url: URL of the article.
            self.title: Article title.
            self.content_html: Raw HTML content of the article.
            self.content_clean: Plain-text version of the content.
            self.meta_description: Meta description of the article.
            self.score: Total score accumulated from analysis checks.
            self.points: Mapping of analysis names to boolean pass/fail values.
            self.recommendations: List of recommendations for failed checks.
        """
        self.id = post["id"]
        self.url = post["link"]
        self.title = post["title"]["rendered"]
        self.content_html = post["content"]["rendered"] or ""
        self.content_clean = self._get_clean_content_html()
        self.meta_description = post.get("yoast_head_json", {}).get("description", "")

        self.score: int = 0
        self.points: dict[str, bool] = dict()
        self.recommendations: list[str] = list()

    def _add_to_report(self, name:str, passed: bool, recommendation: str) -> None:
        """
        Record the result of a single analysis check.

        Args:
            name: Identifier of the analysis check.
            passed: Whether the check passed.
            recommendation: Recommendation text shown if the check failed.
        """
        self.points[name] = passed
        self.score += 1 if passed else 0
        if not passed:
            self.recommendations.append(recommendation)

    def _get_clean_content_html(self) -> str:
        """
        Extract and normalize plain text from the article HTML.

        This removes table-of-contents blocks, scripts, styles, and excessive
        whitespace.

        Returns:
            Cleaned plain-text content of the article.
        """
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
        """
        Extract the first paragraph of the article.

        Returns:
            Text of the first `<p>` element, or an empty string if none exists.
        """
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
    def analyze_direct_answer(self) -> bool:
        """
        Check whether the article starts with a direct answer.

        The check fails if the introductory paragraph contains generic or
        non-informative phrases.

        Returns:
            True if no forbidden phrases are found, otherwise False.
        """
        forbidden_phrases = ["v tomto článku", "poďme sa pozrieť", "dozviete sa", "povieme si"]

        intro = self._get_first_paragraph().lower()
        found_phrases = [p for p in forbidden_phrases if p in intro]

        passed = len(found_phrases) == 0

        recommendation = f"Odstrániť nechcené frázy ({found_phrases})."
        self._add_to_report("direct_answer", passed, recommendation)
        return passed

    # 2
    def _contains_definition_in_what_is_segment(self) -> bool:
        """
        Detect whether the table of contents contains a 'what is' definition section.

        Returns:
            True if a relevant segment is found, otherwise False.
        """
        soup = BeautifulSoup(self.content_html, "html.parser")

        toc = soup.find("div", id="ez-toc-container")
        if not toc:
            return False

        toc_text = toc.get_text(" ", strip=True).lower()

        return "čo je" in toc_text or "čo sú" in toc_text

    def _contains_definition_by_title(self) -> bool:
        """
        Heuristically detect a definition based on the article title and content.

        Rules:
        - The title must contain ':'.
        - The left side of ':' must be a short keyword X (max two words).
        - The content must contain phrases such as 'X je', 'X znamená', or
          'X predstavuje'.

        Returns:
            True if a definition pattern is detected, otherwise False.
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

    def analyze_definition(self) -> bool:
        """
        Check whether the article contains a clear definition of its main topic.

        Returns:
            True if a definition is detected, otherwise False.
        """
        passed =  (self._contains_definition_in_what_is_segment()
                   or self._contains_definition_by_title())

        recommendation = "Pridať priamu definíciu hlavného pojmu."
        self._add_to_report("definition", passed, recommendation)
        return passed

    # 3
    def analyze_headings(self) -> bool:
        """
        Check whether the article contains a sufficient number of H2 headings.

        Returns:
            True if at least three H2 headings are present, otherwise False.
        """
        soup = BeautifulSoup(self.content_html, "html.parser")

        count = len(soup.find_all("h2"))

        passed = True if count >= 3 else False

        recommendation = f"Pridať nadpisy h2 v počte aspoň {3-count}."
        self._add_to_report("headings", passed, recommendation)
        return passed

    # 4
    def analyze_facts(self) -> bool:
        """
        Check whether the article contains enough numeric facts with units.

        Returns:
            True if at least three numeric facts are found, otherwise False.
        """
        facts_regex = re.compile(
            r"\d+\s?(mg|g|kg|%|kcal|ml|mcg|gramov|miligramov)",
            re.IGNORECASE
        )
        matches = facts_regex.findall(self.content_clean)
        count = len(matches)

        passed = True if count >= 3 else False

        recommendation = f"Pridať číselné údaje s jednotkami v počte aspoň {3-count}."
        self._add_to_report("facts", passed, recommendation)
        return passed

    # 5
    def analyze_sources(self) -> bool:
        """
        Check whether the article references scientific or credible sources.

        Returns:
            True if scientific links or a sources section is present, otherwise False.
        """
        soup = BeautifulSoup(self.content_html, "html.parser")

        source_domains = (
            "pubmed.ncbi.nlm.nih.gov",
            "pmc.ncbi.nlm.nih.gov",
            "examine.com",
        )
        source_text_regex = re.compile(
            r"\b(zdroje|references|štúdie)\b",
            re.IGNORECASE
        )

        links = [a.get("href", "") for a in soup.find_all("a", href=True)]
        has_scientific_link = any(
            domain in link for link in links for domain in source_domains)

        has_source_text = bool(source_text_regex.search(self.content_clean))

        passed = has_scientific_link or has_source_text

        recommendation = 'Pridať sekciu "Zdroje".'
        self._add_to_report("sources", passed, recommendation)
        return passed

    # 6
    def analyze_faq(self) -> bool:
        """
        Check whether the article contains an FAQ section.

        Returns:
            True if an FAQ section is detected, otherwise False.
        """
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
        return passed

    # 7
    def analyze_lists(self) -> bool:
        """
        Check whether the article contains at least one list.

        Returns:
            True if an ordered or unordered list is present, otherwise False.
        """
        soup = BeautifulSoup(self.content_html, "html.parser")

        has_ul = soup.find("ul") is not None
        has_ol = soup.find("ol") is not None

        passed = has_ul or has_ol

        recommendation = "Pridať aspoň 1 odrážkový alebo očíslovaný zoznam."
        self._add_to_report("lists", passed, recommendation)
        return passed

    # 8
    def analyze_tables(self) -> bool:
        """
        Check whether the article contains at least one table.

        Returns:
            True if a table is present, otherwise False.
        """
        soup = BeautifulSoup(self.content_html, "html.parser")

        passed = soup.find("table") is not None

        recommendation = "Pridať aspoň 1 tabuľku."
        self._add_to_report("tables", passed, recommendation)
        return passed

    # 9
    def analyze_word_count_ok(self, min_words: int = 500) -> bool:
        """
        Check whether the article meets the minimum word count.

        Args:
            min_words: Minimum required number of words.

        Returns:
            True if the word count is sufficient, otherwise False.
        """
        words = self.content_clean.split()
        word_count = len(words)

        passed = word_count >= min_words

        recommendation = f"Článok nie je dostatočne dlhý, pridať aspoň {min_words - word_count} slov{inflection(min_words - word_count)}."
        self._add_to_report("word_count_ok", passed, recommendation)
        return passed

    # 10
    def analyze_meta_ok(self, min_len: int = 120, max_len: int = 160) -> bool:
        """
        Check whether the meta description length is within the recommended range.

        Args:
            min_len: Minimum allowed length.
            max_len: Maximum allowed length.

        Returns:
            True if the meta description length is acceptable, otherwise False.
        """
        length = len(self.meta_description.strip())
        passed = min_len <= length <= max_len

        recommendation = ""
        if length < min_len:
            recommendation = f"Meta popis je prikrátky, pridať aspoň {min_len - length} slov{inflection(min_len - length)}."
        elif length > max_len:
            recommendation = f"Meta popis je pridlhý, ubrať aspoň {length - max_len} slov{inflection(length - max_len)}."
        self._add_to_report("meta_ok", passed, recommendation)
        return passed

    def _run_analysis_step(self, name: str, fn) -> None:
        """
        Execute an analysis step safely and record failures as warnings.
        Allows the analysis to continue despite a failure at a singular point.

        Args:
            name: Name of the analysis step.
            fn: Callable performing the analysis.
        """
        try:
            fn()
        except Exception as exc:
            warnings.warn(
                f"Analysis step '{name}' failed for article '{self.url}': {exc}",
                category=RuntimeWarning,
                stacklevel=2,
            )
            self._add_to_report(
                name=name,
                passed=False,
                recommendation=f"Analýza '{name}' zlyhala kvôli chybe."
            )

    def analyze(self) -> dict:
        """
        Run all analysis checks on the article.

        Returns:
            Dictionary containing the article URL, title, total score,
            per-check results, and generated recommendations.
        """
        self._run_analysis_step("direct_answer", self.analyze_direct_answer)  # 1
        self._run_analysis_step("definition", self.analyze_definition)  # 2
        self._run_analysis_step("headings", self.analyze_headings)  # 3
        self._run_analysis_step("facts", self.analyze_facts)  # 4
        self._run_analysis_step("sources", self.analyze_sources)  # 5
        self._run_analysis_step("faq", self.analyze_faq)  # 6
        self._run_analysis_step("lists", self.analyze_lists)  # 7
        self._run_analysis_step("tables", self.analyze_tables)  # 8
        self._run_analysis_step("word_count_ok", self.analyze_word_count_ok)  # 9
        self._run_analysis_step("meta_ok", self.analyze_meta_ok)  # 10

        return {
            "url": self.url,
            "title": self.title,
            "score": self.score,
            "report": self.points,
            "recommendations": self.recommendations,
        }
