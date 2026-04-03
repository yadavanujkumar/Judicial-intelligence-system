import re
import logging
from typing import List

logger = logging.getLogger(__name__)

LEGAL_KEYWORDS = [
    "court", "held", "petition", "appeal", "order", "judgment", "decision",
    "plaintiff", "defendant", "petitioner", "respondent", "accused", "evidence",
    "section", "act", "law", "rights", "relief", "dismissed", "allowed",
    "convicted", "acquitted", "bail", "sentence", "compensation", "damages",
    "injunction", "decree", "writ", "constitution", "statutory", "jurisdiction",
]

SIGNAL_WORDS = {
    "high": [
        "held", "court held", "accordingly", "therefore", "thus", "ordered",
        "directed", "judgment", "decision", "concluded",
    ],
    "low": ["whereas", "whereas the", "submitted", "contended", "argued"],
}


class JudgmentSummarizer:
    """Lightweight extractive summarizer for Indian court judgments."""

    def summarize(self, text: str) -> dict:
        """
        Summarize a judgment text into structured sections.
        Returns: summary, key_facts, legal_issues, final_decision, reasoning.
        """
        if not text or len(text.strip()) < 50:
            return self._empty_response()

        sentences = self._split_sentences(text)
        if not sentences:
            return self._empty_response()

        scored = self._score_sentences(sentences)
        sorted_sents = sorted(scored, key=lambda x: x[1], reverse=True)

        top_n = max(3, min(6, len(sentences) // 3))
        top_sentences = [s for s, _ in sorted_sents[:top_n]]

        summary = self._build_summary(sentences, top_sentences)
        key_facts = self._extract_key_facts(sentences)
        legal_issues = self._extract_legal_issues(sentences)
        final_decision = self._extract_final_decision(sentences)
        reasoning = self._extract_reasoning(sentences)

        return {
            "summary": summary,
            "key_facts": key_facts,
            "legal_issues": legal_issues,
            "final_decision": final_decision,
            "reasoning": reasoning,
        }

    def _split_sentences(self, text: str) -> List[str]:
        raw = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s.strip() for s in raw if len(s.strip()) > 20]

    def _score_sentences(self, sentences: List[str]) -> List[tuple]:
        scores = []
        for i, sent in enumerate(sentences):
            score = 0.0
            lower = sent.lower()
            for kw in LEGAL_KEYWORDS:
                if kw in lower:
                    score += 1.5
            for hw in SIGNAL_WORDS["high"]:
                if hw in lower:
                    score += 2.0
            for lw in SIGNAL_WORDS["low"]:
                if lw in lower:
                    score -= 0.5
            word_count = len(sent.split())
            if 15 <= word_count <= 40:
                score += 1.0
            if i == 0:
                score += 1.5
            if i == len(sentences) - 1:
                score += 1.0
            scores.append((sent, score))
        return scores

    def _build_summary(self, all_sentences: List[str], top_sentences: List[str]) -> str:
        ordered = [s for s in all_sentences if s in top_sentences]
        return " ".join(ordered[:4])

    def _extract_key_facts(self, sentences: List[str]) -> str:
        keywords = ["filed", "case", "alleged", "petitioner", "respondent", "plaintiff", "defendant", "date", "amount", "rs."]
        matching = [s for s in sentences if any(kw in s.lower() for kw in keywords)]
        return " ".join(matching[:2]) if matching else sentences[0] if sentences else "Not available."

    def _extract_legal_issues(self, sentences: List[str]) -> str:
        keywords = ["issue", "question", "whether", "section", "act", "provision", "law", "right", "jurisdiction"]
        matching = [s for s in sentences if any(kw in s.lower() for kw in keywords)]
        return " ".join(matching[:2]) if matching else "Legal issues as described in the judgment."

    def _extract_final_decision(self, sentences: List[str]) -> str:
        keywords = ["dismissed", "allowed", "convicted", "acquitted", "granted", "rejected",
                    "ordered", "directed", "decreed", "upheld", "set aside", "remanded"]
        matching = [s for s in reversed(sentences) if any(kw in s.lower() for kw in keywords)]
        return matching[0] if matching else sentences[-1] if sentences else "Decision not clearly stated."

    def _extract_reasoning(self, sentences: List[str]) -> str:
        keywords = ["held", "found", "observed", "noted", "considered", "examined", "relied", "relied on"]
        matching = [s for s in sentences if any(kw in s.lower() for kw in keywords)]
        return " ".join(matching[:2]) if matching else "Reasoning as stated in the judgment text."

    def _empty_response(self) -> dict:
        return {
            "summary": "Insufficient text provided for summarization.",
            "key_facts": "Not available.",
            "legal_issues": "Not available.",
            "final_decision": "Not available.",
            "reasoning": "Not available.",
        }
