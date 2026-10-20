import json
import re
import html
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import requests
from app.config import logger, settings
from app.database import DatabaseManager

LEETCODE_GRAPHQL_QUERY = """
query questionData($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionId
    questionFrontendId
    title
    titleSlug
    content
    difficulty
    isPaidOnly
    codeSnippets {
      lang
      langSlug
      code
    }
    sampleTestCase
    exampleTestcaseList
    metaData
  }
}
"""

def clean_html(raw_html: Optional[str]) -> str:
    """Converts LeetCode problem HTML content into clean readable plain text."""
    if not raw_html:
        return ""
    text = html.unescape(raw_html)
    # Replace common formatting tags
    text = re.sub(r"<code>(.*?)</code>", r"`\1`", text, flags=re.DOTALL)
    text = re.sub(r"<pre>(.*?)</pre>", r"```\n\1\n```", text, flags=re.DOTALL)
    text = re.sub(r"<strong>(.*?)</strong>", r"**\1**", text, flags=re.DOTALL)
    text = re.sub(r"<p>", r"\n", text)
    text = re.sub(r"</p>", r"\n", text)
    text = re.sub(r"<li>", r"\n* ", text)
    text = re.sub(r"</li>", r"", text)
    text = re.sub(r"<br\s*/?>", r"\n", text)
    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Remove excess whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def extract_signature_from_snippet(python_snippet: str) -> Tuple[str, Optional[str]]:
    """Extracts class name and primary method name from python3 code snippet."""
    class_match = re.search(r"class\s+([A-Za-z0-9_]+)", python_snippet)
    class_name = class_match.group(1) if class_match else "Solution"

    method_match = re.search(r"def\s+([A-Za-z0-9_]+)\s*\(", python_snippet)
    method_name = method_match.group(1) if method_match else None

    return class_name, method_name


class ProblemSource:
    """Handles fetching and caching of LeetCode problem metadata and statements."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or settings.PROBLEMS_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = settings.NEETCODE_MANIFEST_PATH

    def load_manifest(self) -> List[Dict[str, Any]]:
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found at {self.manifest_path}")
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_cached_problem(self, slug: str) -> Optional[Dict[str, Any]]:
        cache_file = self.cache_dir / f"{slug}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error reading cache for {slug}: {e}")
        return None

    def save_cache(self, slug: str, data: Dict[str, Any]) -> None:
        cache_file = self.cache_dir / f"{slug}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save cache for {slug}: {e}")

    def fetch_problem_details(self, slug: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Fetches problem statement, starter code, and test cases via LeetCode's public GraphQL API."""
        if not force_refresh:
            cached = self.get_cached_problem(slug)
            if cached and cached.get("starter_code"):
                return cached

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": f"https://leetcode.com/problems/{slug}/"
        }
        payload = {
            "query": LEETCODE_GRAPHQL_QUERY,
            "variables": {"titleSlug": slug}
        }

        try:
            resp = requests.post(
                settings.LEETCODE_GRAPHQL_URL,
                json=payload,
                headers=headers,
                timeout=15
            )
            resp.raise_for_status()
            res_data = resp.json()
            q_data = res_data.get("data", {}).get("question")
            if not q_data:
                logger.error(f"LeetCode returned empty question data for slug: {slug}")
                return None

            raw_content = q_data.get("content", "")
            cleaned_statement = clean_html(raw_content)

            # Find python3 starter code snippet
            starter_code = None
            snippets = q_data.get("codeSnippets") or []
            for s in snippets:
                if s.get("langSlug") == "python3":
                    starter_code = s.get("code")
                    break

            class_name = "Solution"
            method_name = None
            if starter_code:
                c_match = re.search(r"class\s+([A-Za-z0-9_]+)", starter_code)
                if c_match:
                    class_name = c_match.group(1)
                m_match = re.search(r"def\s+([A-Za-z0-9_]+)\s*\(", starter_code)
                if m_match:
                    method_name = m_match.group(1)

            parsed_data = {
                "slug": slug,
                "title": q_data.get("title"),
                "question_id": q_data.get("questionFrontendId"),
                "difficulty": q_data.get("difficulty"),
                "statement": cleaned_statement,
                "starter_code": starter_code,
                "class_name": class_name,
                "method_name": method_name,
                "sample_test_case": q_data.get("sampleTestCase"),
                "example_testcases": q_data.get("exampleTestcaseList") or [],
                "meta_data": q_data.get("metaData"),
            }

            self.save_cache(slug, parsed_data)
            return parsed_data

        except Exception as e:
            logger.error(f"Failed to fetch details for problem '{slug}' from LeetCode GraphQL: {e}")
            # Fallback to local cache if available even if stale
            return self.get_cached_problem(slug)

    def import_all_manifest_problems(self) -> int:
        """Loads problems from manifest and populates the database."""
        manifest = self.load_manifest()
        count = 0
        for item in manifest:
            slug = item["slug"]
            cached = self.get_cached_problem(slug)
            statement = cached.get("statement") if cached else None
            starter_code = cached.get("starter_code") if cached else None
            sample_test_case = cached.get("sample_test_case") if cached else None
            example_testcases = cached.get("example_testcases") if cached else None

            DatabaseManager.upsert_problem(
                slug=slug,
                title=item["title"],
                url=item["url"],
                category=item["category"],
                difficulty=item["difficulty"],
                order_index=item.get("order", 0),
                class_name=item.get("class_name", "Solution"),
                method_name=item.get("method_name"),
                statement=statement,
                starter_code=starter_code,
                sample_test_case=sample_test_case,
                example_testcases=example_testcases
            )
            count += 1
        logger.info(f"Imported {count} NeetCode 150 problems into the database.")
        return count
