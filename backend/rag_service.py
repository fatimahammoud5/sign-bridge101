from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception:  # optional dependency
    TfidfVectorizer = None
    cosine_similarity = None


@dataclass
class KnowledgeChunk:
    source: str
    title: str
    text: str


class SignBridgeRAG:
    """Small, reliable local RAG index for SignBridge project knowledge.

    Primary retriever: TF-IDF vector similarity (if scikit-learn is available).
    Fallback: deterministic lexical scoring, so the project still runs without
    installing another package.
    """

    SUPPORTED_SUFFIXES = {".txt", ".md", ".json", ".pdf", ".docx"}

    def __init__(self, knowledge_dir: str | Path | None = None) -> None:
        base = Path(__file__).resolve().parent
        self.knowledge_dir = Path(knowledge_dir) if knowledge_dir else base / "knowledge"
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

        self.chunks: list[KnowledgeChunk] = []
        self._vectorizer = None
        self._matrix = None
        self.reload()

    def reload(self) -> int:
        self.chunks = []

        for path in sorted(self.knowledge_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in self.SUPPORTED_SUFFIXES:
                continue
            try:
                text = self._read_file(path)
            except Exception as exc:
                print(f"RAG SKIP [{path.name}]: {exc!r}")
                continue

            if not text.strip():
                continue

            title = path.stem.replace("_", " ").strip()
            for chunk in self._chunk_text(text):
                self.chunks.append(
                    KnowledgeChunk(
                        source=path.name,
                        title=title,
                        text=chunk,
                    )
                )

        self._build_vector_index()
        print(f"SIGNBRIDGE RAG: loaded {len(self.chunks)} chunks")
        return len(self.chunks)

    def _read_file(self, path: Path) -> str:
        suffix = path.suffix.lower()

        if suffix in {".txt", ".md"}:
            return path.read_text(encoding="utf-8", errors="ignore")

        if suffix == ".json":
            obj = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
            return json.dumps(obj, ensure_ascii=False, indent=2)

        if suffix == ".pdf":
            try:
                from pypdf import PdfReader
            except Exception as exc:
                raise RuntimeError("Install pypdf to index PDF files") from exc
            reader = PdfReader(str(path))
            return "\n".join((page.extract_text() or "") for page in reader.pages)

        if suffix == ".docx":
            try:
                from docx import Document
            except Exception as exc:
                raise RuntimeError("Install python-docx to index DOCX files") from exc
            document = Document(str(path))
            return "\n".join(p.text for p in document.paragraphs)

        return ""

    @staticmethod
    def _chunk_text(text: str, max_chars: int = 1100, overlap_chars: int = 160) -> Iterable[str]:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
        paragraphs = [p for p in paragraphs if p]

        current = ""
        for paragraph in paragraphs:
            if not current:
                current = paragraph
                continue

            candidate = current + "\n" + paragraph
            if len(candidate) <= max_chars:
                current = candidate
                continue

            yield current.strip()
            tail = current[-overlap_chars:].strip() if overlap_chars else ""
            current = (tail + "\n" + paragraph).strip() if tail else paragraph

            while len(current) > max_chars:
                yield current[:max_chars].strip()
                current = current[max_chars - overlap_chars :].strip()

        if current.strip():
            yield current.strip()

    def _build_vector_index(self) -> None:
        self._vectorizer = None
        self._matrix = None

        if not self.chunks or TfidfVectorizer is None:
            return

        corpus = [f"{c.title}\n{c.text}" for c in self.chunks]
        try:
            vectorizer = TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                min_df=1,
                sublinear_tf=True,
                strip_accents="unicode",
            )
            matrix = vectorizer.fit_transform(corpus)
            self._vectorizer = vectorizer
            self._matrix = matrix
        except Exception as exc:
            print("RAG VECTOR INDEX ERROR:", repr(exc))

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return re.findall(r"[\w\u0600-\u06FF]+", text.lower())

    def _lexical_score(self, query: str, chunk: KnowledgeChunk) -> float:
        q_tokens = self._tokens(query)
        if not q_tokens:
            return 0.0

        doc = f"{chunk.title} {chunk.text}".lower()
        doc_tokens = self._tokens(doc)
        if not doc_tokens:
            return 0.0

        doc_set = set(doc_tokens)
        overlap = sum(1 for token in q_tokens if token in doc_set)
        unique_overlap = len(set(q_tokens) & doc_set)
        phrase_bonus = 0.0

        normalized_query = " ".join(q_tokens)
        normalized_doc = " ".join(doc_tokens)
        if normalized_query and normalized_query in normalized_doc:
            phrase_bonus += 4.0

        title_tokens = set(self._tokens(chunk.title))
        title_overlap = len(set(q_tokens) & title_tokens)

        return (
            overlap * 1.0
            + unique_overlap * 1.5
            + title_overlap * 2.0
            + phrase_bonus
        ) / max(1.0, math.sqrt(len(doc_tokens)))

    def retrieve(self, query: str, k: int = 5) -> list[dict]:
        query = str(query).strip()
        if not query or not self.chunks:
            return []

        scored: list[tuple[float, int]] = []

        if self._vectorizer is not None and self._matrix is not None and cosine_similarity is not None:
            try:
                q_vec = self._vectorizer.transform([query])
                sims = cosine_similarity(q_vec, self._matrix).ravel()
                for i, sim in enumerate(sims):
                    lexical = self._lexical_score(query, self.chunks[i])
                    # Hybrid score: semantic-ish TF-IDF + exact keyword boost.
                    score = float(sim) * 0.82 + min(lexical, 1.0) * 0.18
                    if score > 0:
                        scored.append((score, i))
            except Exception as exc:
                print("RAG VECTOR SEARCH ERROR:", repr(exc))

        if not scored:
            for i, chunk in enumerate(self.chunks):
                score = self._lexical_score(query, chunk)
                if score > 0:
                    scored.append((score, i))

        scored.sort(key=lambda item: item[0], reverse=True)

        results: list[dict] = []
        seen_texts: set[str] = set()
        for score, index in scored:
            chunk = self.chunks[index]
            if chunk.text in seen_texts:
                continue
            seen_texts.add(chunk.text)
            results.append(
                {
                    "source": chunk.source,
                    "title": chunk.title,
                    "text": chunk.text,
                    "score": round(float(score), 5),
                }
            )
            if len(results) >= k:
                break

        return results

    def build_context(self, query: str, k: int = 5, max_chars: int = 5200) -> tuple[str, list[dict]]:
        results = self.retrieve(query, k=k)
        if not results:
            return "", []

        sections: list[str] = []
        used = 0
        for idx, item in enumerate(results, start=1):
            section = (
                f"[Knowledge {idx} | source={item['source']}]\n"
                f"{item['text'].strip()}"
            )
            if used + len(section) > max_chars:
                remaining = max_chars - used
                if remaining > 120:
                    sections.append(section[:remaining])
                break
            sections.append(section)
            used += len(section)

        return "\n\n".join(sections), results