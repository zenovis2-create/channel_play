"""Session and artifact search index."""

from __future__ import annotations

import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .errors import CompanyError
from .paths import rel
from .state import CompanyPaths

TEXT_SUFFIXES = {
    ".asmdef",
    ".cs",
    ".css",
    ".html",
    ".json",
    ".log",
    ".md",
    ".meta",
    ".py",
    ".shader",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
SCREENSHOT_SUFFIXES = {".gif", ".jpeg", ".jpg", ".png", ".webp"}
SEARCH_ROOTS = ("memory/sessions", "runs", "reviews", "docs")
SEARCH_FILES = (
    "memory/company/task_board.json",
    "memory/company/jobs.json",
    "memory/company/jobs/jobs.json",
)
MAX_TEXT_BYTES = 240_000
DEFAULT_LIMIT = 20


@dataclass(frozen=True)
class IndexedDocument:
    path: str
    source_type: str
    title: str
    content: str
    preview: str
    modified_at: str
    size: int


def search_index_path(root: Path) -> Path:
    return CompanyPaths(root).memory_dir / "session_search.sqlite"


def rebuild_search_index(root: Path) -> dict[str, Any]:
    docs = list(_iter_documents(root))
    path = search_index_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as conn:
        _ensure_fts5(conn)
        conn.execute("DROP TABLE IF EXISTS session_search")
        conn.execute("DROP TABLE IF EXISTS search_meta")
        conn.execute(
            """
            CREATE VIRTUAL TABLE session_search USING fts5(
                path,
                source_type UNINDEXED,
                title,
                content,
                preview UNINDEXED,
                modified_at UNINDEXED,
                size UNINDEXED,
                tokenize='unicode61'
            )
            """
        )
        conn.execute("CREATE TABLE search_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.executemany(
            """
            INSERT INTO session_search(path, source_type, title, content, preview, modified_at, size)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (doc.path, doc.source_type, doc.title, doc.content, doc.preview, doc.modified_at, doc.size)
                for doc in docs
            ],
        )
        conn.execute(
            "INSERT INTO search_meta(key, value) VALUES ('indexed_at', ?)",
            (datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),),
        )
        conn.execute("INSERT INTO search_meta(key, value) VALUES ('document_count', ?)", (str(len(docs)),))
        conn.commit()
    return {"indexPath": rel(root, path), "documentCount": len(docs)}


def search_sessions(root: Path, query: str, limit: int = DEFAULT_LIMIT, rebuild: bool = False) -> dict[str, Any]:
    clean = query.strip()
    if not clean:
        raise CompanyError("Search query is required.")
    path = search_index_path(root)
    if rebuild or not path.exists():
        rebuild_search_index(root)
    fts_query = _fts_query(clean)
    with closing(sqlite3.connect(path)) as conn:
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT path, source_type, title, preview, modified_at, size, bm25(session_search) AS score
                FROM session_search
                WHERE session_search MATCH ?
                ORDER BY score
                LIMIT ?
                """,
                (fts_query, max(1, min(limit, 50))),
            ).fetchall()
        except sqlite3.OperationalError as exc:
            raise CompanyError(f"Search query failed: {exc}") from exc
        meta = _search_meta(conn)
    results = [
        {
            "path": str(row["path"]),
            "sourceType": str(row["source_type"]),
            "title": str(row["title"]),
            "preview": str(row["preview"]),
            "modifiedAt": str(row["modified_at"]),
            "size": int(row["size"] or 0),
            "score": float(row["score"] or 0),
        }
        for row in rows
    ]
    return {
        "query": clean,
        "ftsQuery": fts_query,
        "indexPath": rel(root, path),
        "indexedAt": meta.get("indexed_at", ""),
        "documentCount": int(meta.get("document_count", "0") or 0),
        "count": len(results),
        "results": results,
    }


def render_search_results(root: Path, query: str, limit: int = DEFAULT_LIMIT, rebuild: bool = False) -> str:
    result = search_sessions(root, query, limit=limit, rebuild=rebuild)
    lines = [
        f"Search: {result['query']}",
        f"Index: {result['indexPath']} ({result['documentCount']} docs, indexed {result['indexedAt'] or 'unknown'})",
        f"Results: {result['count']}",
        "",
    ]
    for index, row in enumerate(result["results"], start=1):
        lines.extend(
            [
                f"{index}. [{row['sourceType']}] {row['path']}",
                f"   {row['title']}",
                f"   {row['preview']}",
                "",
            ]
        )
    if not result["results"]:
        lines.append("- no matches")
    return "\n".join(lines).rstrip()


def _ensure_fts5(conn: sqlite3.Connection) -> None:
    try:
        conn.execute("CREATE VIRTUAL TABLE temp._fts5_probe USING fts5(value)")
        conn.execute("DROP TABLE temp._fts5_probe")
    except sqlite3.OperationalError as exc:
        raise CompanyError("SQLite FTS5 is not available in this Python runtime.") from exc


def _iter_documents(root: Path) -> Iterable[IndexedDocument]:
    for raw_root in SEARCH_ROOTS:
        base = root / raw_root
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or _skip_path(path):
                continue
            doc = _document_for_path(root, path)
            if doc:
                yield doc
    for raw_path in SEARCH_FILES:
        path = root / raw_path
        if path.exists() and path.is_file():
            doc = _document_for_path(root, path)
            if doc:
                yield doc


def _document_for_path(root: Path, path: Path) -> IndexedDocument | None:
    relative = rel(root, path)
    stat = path.stat()
    source_type = _source_type(relative, path)
    modified_at = datetime.fromtimestamp(stat.st_mtime, timezone.utc).astimezone().isoformat(timespec="seconds")
    title = _title(relative, source_type)
    if path.suffix.lower() in SCREENSHOT_SUFFIXES:
        content = f"{relative}\n{path.stem}\nscreenshot image capture visual feedback {source_type}"
        preview = f"screenshot file: {relative}"
        return IndexedDocument(relative, source_type, title, content, preview, modified_at, stat.st_size)
    if path.suffix.lower() not in TEXT_SUFFIXES or stat.st_size > MAX_TEXT_BYTES:
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    normalized = _normalize_text(text)
    content = "\n".join([relative, title, source_type, normalized])
    preview = _preview(normalized)
    return IndexedDocument(relative, source_type, title, content, preview, modified_at, stat.st_size)


def _skip_path(path: Path) -> bool:
    parts = set(path.parts)
    return "__pycache__" in parts or ".git" in parts or path.suffix.lower() in {".sqlite", ".db", ".pyc"}


def _source_type(relative: str, path: Path) -> str:
    if path.suffix.lower() in SCREENSHOT_SUFFIXES:
        return "screenshot"
    if relative.startswith("memory/sessions/"):
        return "session"
    if relative.startswith("runs/"):
        return "run"
    if relative.startswith("reviews/"):
        return "review"
    if relative.startswith("docs/"):
        return "doc"
    if relative.endswith("task_board.json"):
        return "task_board"
    if relative.endswith("jobs.json"):
        return "jobs"
    return "file"


def _title(relative: str, source_type: str) -> str:
    name = Path(relative).name
    if source_type == "task_board":
        return "Company Task Board"
    if source_type == "jobs":
        return "Job Ledger"
    return name


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\x00", " ")).strip()


def _preview(text: str, limit: int = 240) -> str:
    clean = _normalize_text(text)
    if len(clean) <= limit:
        return clean
    return clean[:limit].rstrip() + "..."


def _fts_query(query: str) -> str:
    tokens = re.findall(r"[0-9A-Za-z_가-힣]+", query)
    if not tokens:
        raise CompanyError("Search query needs at least one searchable term.")
    return " AND ".join(f'"{token}"' for token in tokens[:10])


def _search_meta(conn: sqlite3.Connection) -> dict[str, str]:
    try:
        rows = conn.execute("SELECT key, value FROM search_meta").fetchall()
    except sqlite3.OperationalError:
        return {}
    return {str(row[0]): str(row[1]) for row in rows}
