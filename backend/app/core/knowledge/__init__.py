"""
FTS5 knowledge base. Reads documents from data/kb/ directory.
"""
import json
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "kb"
DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "knowledge.db"

COLLECTIONS = {"kb_patient", "kb_professional"}


def _scan_files() -> dict[str, list[tuple[str, str, dict]]]:
    result: dict[str, list[tuple[str, str, dict]]] = {}
    for coll in COLLECTIONS:
        coll_dir = DATA_DIR / coll
        if not coll_dir.exists():
            logger.warning(f"Directory not found: {coll_dir}")
            continue
        docs = []
        for fpath in sorted(coll_dir.iterdir()):
            if fpath.suffix.lower() not in (".txt", ".md"):
                continue
            content = fpath.read_text(encoding="utf-8").strip()
            if not content:
                continue
            title = fpath.stem.replace("_", " ").replace("-", " ")
            doc_type = "education" if coll == "kb_patient" else "guideline"
            docs.append((fpath.stem, content, {"title": title, "type": doc_type}))
        result[coll] = docs
        logger.info(f"Scanned {len(docs)} files in {coll}")
    return result


def _get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init():
    docs = _scan_files()
    if not docs:
        logger.warning("No documents found in data/kb/")
        return 0
    conn = _get_conn()
    try:
        conn.execute("DROP TABLE IF EXISTS kb_fts")
        conn.execute("CREATE VIRTUAL TABLE kb_fts USING fts5(content, collection, metadata_raw)")
        total = 0
        for coll, items in docs.items():
            for fname, content, meta in items:
                conn.execute(
                    "INSERT INTO kb_fts(content, collection, metadata_raw) VALUES (?,?,?)",
                    (content, coll, json.dumps(meta, ensure_ascii=False)),
                )
                total += 1
        conn.commit()
        logger.info(f"KB rebuilt: {total} docs across {len(docs)} collections")
        return total
    finally:
        conn.close()


def search(query: str, collection: str, top_k: int = 5) -> list[dict]:
    conn = _get_conn()
    try:
        # LIKE search first (better for Chinese text)
        like_pattern = f"%{query}%"
        cursor = conn.execute(
            "SELECT content, collection, metadata_raw FROM kb_fts "
            "WHERE content LIKE ? AND collection = ? LIMIT ?",
            (like_pattern, collection, top_k),
        )
        results = []
        for row in cursor.fetchall():
            meta = json.loads(row[2]) if row[2] else {}
            results.append({
                "id": f"like_{abs(hash(row[0]))}",
                "content": row[0],
                "metadata": meta,
                "rrf_score": 0.5,
            })
        if results:
            return results

        # Fallback: FTS5 match
        try:
            cursor = conn.execute(
                "SELECT content, collection, metadata_raw, rank FROM kb_fts "
                "WHERE kb_fts MATCH ? AND collection = ? ORDER BY rank LIMIT ?",
                (query, collection, top_k),
            )
            for row in cursor.fetchall():
                meta = json.loads(row[2]) if row[2] else {}
                results.append({
                    "id": f"fts_{abs(hash(row[0]))}",
                    "content": row[0],
                    "metadata": meta,
                    "rrf_score": max(0.0, 1.0 - abs(float(row[3]) if row[3] else 0) / 10.0),
                })
        except Exception:
            pass
        return results
    finally:
        conn.close()
