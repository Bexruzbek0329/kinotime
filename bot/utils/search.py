"""Search helpers — query normalisation, fuzzy scoring, code detection."""
import re


def normalize_query(q: str) -> str:
    """Strip and collapse whitespace, lower-case the query."""
    return re.sub(r"\s+", " ", q.strip().lower())


def fuzzy_search_score(query: str, title: str) -> int:
    """
    Simple fuzzy relevance score.

    Returns an integer 0–100 where higher means a better match.
    The result is used only for in-memory re-ranking when the DB
    cannot apply full-text scoring.
    """
    q = normalize_query(query)
    t = normalize_query(title)
    if q == t:
        return 100
    if t.startswith(q):
        return 80
    if q in t:
        return 60
    # Word-overlap heuristic
    q_words = set(q.split())
    t_words = set(t.split())
    overlap = len(q_words & t_words)
    if overlap:
        return 40 + overlap * 5
    return 0


def is_movie_code(text: str) -> bool:
    """Return True when *text* looks like a numeric movie code (1–10 digits)."""
    stripped = text.strip()
    return stripped.isdigit() and 1 <= len(stripped) <= 10
