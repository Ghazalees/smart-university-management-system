"""Ranks authorized document passages for grounded answer generation."""

import math
import re
from abc import ABC, abstractmethod
from collections import Counter
from difflib import SequenceMatcher

from django.conf import settings

from apps.documents.repositories import DocumentRepositoryFactory

from .security import TextNormalizer

TOKEN_PATTERN = re.compile(r"[^\W_]+", re.UNICODE)
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?؟؛:])\s+|\n{2,}")
STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "what",
    "how",
    "can",
    "are",
    "is",
    "to",
    "of",
    "a",
    "an",
    "from",
    "about",
    "please",
    "از",
    "به",
    "در",
    "برای",
    "که",
    "این",
    "آن",
    "را",
    "با",
    "یا",
    "چه",
    "چگونه",
    "است",
    "هست",
    "لطفا",
    "لطفاً",
}


def tokenize(text):
    normalized = TextNormalizer.normalize(text).lower()
    return [
        token
        for token in TOKEN_PATTERN.findall(normalized)
        if len(token) > 1 and token not in STOP_WORDS
    ]


def cosine_similarity(left, right):
    left_counts, right_counts = Counter(left), Counter(right)
    common = set(left_counts) & set(right_counts)
    numerator = sum(left_counts[token] * right_counts[token] for token in common)
    left_norm = math.sqrt(sum(value * value for value in left_counts.values()))
    right_norm = math.sqrt(sum(value * value for value in right_counts.values()))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0


def split_knowledge_chunks(text, max_chars=1800, overlap_chars=220):
    """Split long uploaded sources into searchable passages without losing headings."""

    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    paragraphs = [
        part.strip() for part in re.split(r"\n{2,}", normalized) if part.strip()
    ]
    if not paragraphs:
        paragraphs = [normalized]

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        # A single very large Word paragraph is split on sentence boundaries first.
        pieces = [paragraph]
        if len(paragraph) > max_chars:
            pieces = [
                part.strip()
                for part in SENTENCE_BOUNDARY.split(paragraph)
                if part.strip()
            ]
        for piece in pieces:
            if len(piece) > max_chars:
                start = 0
                while start < len(piece):
                    end = min(len(piece), start + max_chars)
                    chunks.append(piece[start:end].strip())
                    if end >= len(piece):
                        break
                    start = max(start + 1, end - overlap_chars)
                continue

            candidate = f"{current}\n\n{piece}".strip() if current else piece
            if len(candidate) <= max_chars:
                current = candidate
                continue
            if current:
                chunks.append(current)
                tail = current[-overlap_chars:].strip() if overlap_chars else ""
                current = f"{tail}\n\n{piece}".strip() if tail else piece
            else:
                current = piece
    if current:
        chunks.append(current)
    return [chunk for chunk in chunks if chunk]


def _fuzzy_token_overlap(query_tokens, chunk_tokens):
    """Small typo/inflection tolerance for English and Persian words."""

    if not query_tokens or not chunk_tokens:
        return 0
    unique_chunk_tokens = set(chunk_tokens)
    matched = 0
    for query_token in set(query_tokens):
        if query_token in unique_chunk_tokens:
            matched += 1
            continue
        if len(query_token) < 5:
            continue
        for candidate in unique_chunk_tokens:
            if abs(len(candidate) - len(query_token)) > 2 or len(candidate) < 4:
                continue
            if SequenceMatcher(None, query_token, candidate).ratio() >= 0.84:
                matched += 1
                break
    return matched


def score_knowledge_chunk(question, query_tokens, chunk):
    chunk_tokens = tokenize(chunk)
    if not chunk_tokens:
        return 0.0, 0
    exact_overlap = len(set(query_tokens) & set(chunk_tokens))
    fuzzy_overlap = _fuzzy_token_overlap(query_tokens, chunk_tokens)
    overlap = max(exact_overlap, fuzzy_overlap)
    coverage = overlap / max(1, len(set(query_tokens)))
    density = overlap / max(1, min(len(set(chunk_tokens)), 60))
    semantic = cosine_similarity(query_tokens, chunk_tokens)
    normalized_question = TextNormalizer.normalize(question).lower()
    normalized_chunk = TextNormalizer.normalize(chunk).lower()
    phrase_bonus = (
        0.35 if normalized_question and normalized_question in normalized_chunk else 0.0
    )
    return coverage * 2.4 + semantic * 1.8 + density * 0.8 + phrase_bonus, overlap


def build_relevant_excerpt(document, question, max_chars=9000):
    """Return the most relevant passages, including content beyond the first 12k chars."""

    query_tokens = tokenize(question)
    if not query_tokens:
        return "", 0.0, 0

    chunks = split_knowledge_chunks(document.content)
    ranked = []
    for index, chunk in enumerate(chunks):
        score, overlap = score_knowledge_chunk(question, query_tokens, chunk)
        if overlap:
            ranked.append((score, overlap, index, chunk))
    if not ranked:
        return "", 0.0, 0

    ranked.sort(key=lambda row: (row[0], row[1], -row[2]), reverse=True)
    selected = []
    selected_indexes = set()
    total = 0
    for score, overlap, index, chunk in ranked:
        if index in selected_indexes:
            continue
        # Add the preceding short chunk when it appears to be a section heading/context.
        candidates = []
        if index > 0 and len(chunks[index - 1]) <= 500:
            candidates.append((index - 1, chunks[index - 1]))
        candidates.append((index, chunk))
        for candidate_index, candidate in candidates:
            if candidate_index in selected_indexes:
                continue
            remaining = max_chars - total
            if remaining <= 0:
                break
            value = candidate[:remaining].strip()
            if value:
                selected.append((candidate_index, value))
                selected_indexes.add(candidate_index)
                total += len(value) + 2
        if len(selected_indexes) >= 5 or total >= max_chars:
            break

    selected.sort(key=lambda row: row[0])
    return "\n\n".join(value for _, value in selected), ranked[0][0], ranked[0][1]


def document_context(document):
    """Get the retrieval-selected passage, falling back to the original content."""

    return getattr(document, "_rag_excerpt", "") or document.content


class KnowledgeRetrievalStrategy(ABC):
    @abstractmethod
    def retrieve(self, user, question, limit=5): ...


class KeywordKnowledgeRetrievalStrategy(KnowledgeRetrievalStrategy):
    def retrieve(self, user, question, limit=5):
        tokens = tokenize(question)[:30]
        if not tokens:
            return []
        documents = DocumentRepositoryFactory.create().accessible_to(
            user, knowledge_only=True
        )
        ranked = []
        for document in documents:
            excerpt, chunk_score, overlap = build_relevant_excerpt(document, question)
            title_tokens = tokenize(document.title)
            tag_tokens = tokenize(" ".join(document.tags or []))
            title_overlap = len(set(tokens) & set(title_tokens))
            tag_overlap = len(set(tokens) & set(tag_tokens))
            score = chunk_score + title_overlap * 3.0 + tag_overlap * 1.8
            if overlap or title_overlap or tag_overlap:
                document._rag_excerpt = excerpt or document.content[:9000]
                document._rag_score = score
                ranked.append((score, document.updated_at, document))
        ranked.sort(key=lambda row: (row[0], row[1]), reverse=True)
        return [row[2] for row in ranked[:limit]]


class SemanticKnowledgeRetrievalStrategy(KnowledgeRetrievalStrategy):
    """Chunk-aware semantic approximation based on normalized token vectors."""

    def retrieve(self, user, question, limit=5):
        query_tokens = tokenize(question)
        if not query_tokens:
            return []
        documents = DocumentRepositoryFactory.create().accessible_to(
            user, knowledge_only=True
        )
        ranked = []
        for document in documents:
            excerpt, chunk_score, overlap = build_relevant_excerpt(document, question)
            title_score = cosine_similarity(query_tokens, tokenize(document.title))
            score = chunk_score + title_score * 1.5
            if overlap and score >= 0.05:
                document._rag_excerpt = excerpt
                document._rag_score = score
                ranked.append((score, document.updated_at, document))
        ranked.sort(key=lambda row: (row[0], row[1]), reverse=True)
        return [row[2] for row in ranked[:limit]]


class HybridKnowledgeRetrievalStrategy(KnowledgeRetrievalStrategy):
    def __init__(self):
        self.keyword = KeywordKnowledgeRetrievalStrategy()
        self.semantic = SemanticKnowledgeRetrievalStrategy()

    def retrieve(self, user, question, limit=5):
        keyword_docs = self.keyword.retrieve(user, question, limit=limit * 2)
        semantic_docs = self.semantic.retrieve(user, question, limit=limit * 2)
        scores = {}
        by_id = {}
        excerpts = {}
        for index, document in enumerate(keyword_docs):
            scores[document.pk] = scores.get(document.pk, 0) + (limit * 2 - index) * 2
            scores[document.pk] += float(getattr(document, "_rag_score", 0))
            by_id[document.pk] = document
            excerpts[document.pk] = document_context(document)
        for index, document in enumerate(semantic_docs):
            scores[document.pk] = scores.get(document.pk, 0) + (limit * 2 - index)
            scores[document.pk] += float(getattr(document, "_rag_score", 0))
            by_id[document.pk] = document
            excerpts.setdefault(document.pk, document_context(document))
        ranked_ids = sorted(scores, key=scores.get, reverse=True)[:limit]
        results = []
        for document_id in ranked_ids:
            document = by_id[document_id]
            document._rag_excerpt = excerpts[document_id]
            results.append(document)
        return results


class RetrievalStrategyFactory:
    @staticmethod
    def create(name=None):
        strategy = (
            name or getattr(settings, "AI_RETRIEVAL_STRATEGY", "hybrid")
        ).lower()
        return {
            "keyword": KeywordKnowledgeRetrievalStrategy,
            "semantic": SemanticKnowledgeRetrievalStrategy,
            "hybrid": HybridKnowledgeRetrievalStrategy,
        }.get(strategy, HybridKnowledgeRetrievalStrategy)()
