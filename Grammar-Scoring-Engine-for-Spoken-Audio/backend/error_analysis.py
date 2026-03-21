"""
Error detection, classification, and explanation for grammar corrections.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


class ErrorAnalyzer:
    """Analyzes differences between original and corrected text."""

    # Common articles
    ARTICLES = {"a", "an", "the"}

    # Common prepositions
    PREPOSITIONS = {
        "in", "on", "at", "to", "from", "by", "for", "with", "about",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "up", "down", "out", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "when", "where",
        "why", "how", "all", "both", "each", "few", "more", "most",
        "other", "some", "such", "no", "nor", "not", "only", "same",
        "so", "than", "too", "very", "can", "just", "should", "now"
    }

    # Common auxiliary and linking verbs
    AUXILIARY_VERBS = {
        "is", "are", "am", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would",
        "shall", "should", "can", "could", "may", "might", "must",
        "ought"
    }

    # Common past tense irregular verbs (simple patterns)
    PAST_TENSE_MAP = {
        "go": "went", "is": "was", "are": "were", "am": "was",
        "have": "had", "has": "had", "do": "did", "does": "did",
        "eat": "ate", "see": "saw", "get": "got", "make": "made",
        "come": "came", "know": "knew", "think": "thought",
        "give": "gave", "find": "found", "tell": "told",
        "become": "became", "leave": "left", "feel": "felt",
        "bring": "brought", "begin": "began", "seem": "seemed",
        "help": "helped", "talk": "talked", "turn": "turned",
        "start": "started", "show": "showed", "hear": "heard",
        "play": "played", "run": "ran", "move": "moved",
        "like": "liked", "live": "lived", "believe": "believed",
        "hold": "held", "bring": "brought", "happen": "happened",
        "write": "wrote", "provide": "provided", "say": "said",
        "use": "used", "work": "worked", "call": "called",
    }

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return text.lower().split()

    @staticmethod
    def _lcs_diff(source: List[str], target: List[str]) -> Tuple[List[str], List[str]]:
        """Compute longest common subsequence based diff."""
        n, m = len(source), len(target)
        dp: List[List[int]] = [[0] * (m + 1) for _ in range(n + 1)]

        for i in range(n - 1, -1, -1):
            for j in range(m - 1, -1, -1):
                if source[i] == target[j]:
                    dp[i][j] = 1 + dp[i + 1][j + 1]
                else:
                    dp[i][j] = max(dp[i + 1][j], dp[i][j + 1])

        left_tokens = []
        right_tokens = []
        i, j = 0, 0

        while i < n and j < m:
            if source[i] == target[j]:
                left_tokens.append(source[i])
                right_tokens.append(target[j])
                i += 1
                j += 1
            elif j < m and (i == n or dp[i + 1][j] >= dp[i][j + 1]):
                left_tokens.append(source[i])
                i += 1
            else:
                right_tokens.append(target[j])
                j += 1

        while i < n:
            left_tokens.append(source[i])
            i += 1

        while j < m:
            right_tokens.append(target[j])
            j += 1

        return left_tokens, right_tokens

    @classmethod
    def _classify_error(cls, original: str, corrected: str) -> Tuple[str, str]:
        """Classify error type and generate explanation."""
        orig_lower = original.lower()
        corr_lower = corrected.lower()

        if orig_lower in cls.ARTICLES and corr_lower not in cls.ARTICLES:
            return "article_error", f"Removed article '{original}'."
        if orig_lower not in cls.ARTICLES and corr_lower in cls.ARTICLES:
            return "article_error", f"Added article '{corrected}'."
        if orig_lower in cls.ARTICLES and corr_lower in cls.ARTICLES:
            return "article_error", f"Changed article from '{original}' to '{corrected}'."

        if orig_lower in cls.PREPOSITIONS and corr_lower not in cls.PREPOSITIONS:
            return "preposition_error", f"Removed preposition '{original}'."
        if orig_lower not in cls.PREPOSITIONS and corr_lower in cls.PREPOSITIONS:
            return "preposition_error", f"Added preposition '{corrected}'."
        if orig_lower in cls.PREPOSITIONS and corr_lower in cls.PREPOSITIONS:
            return "preposition_error", f"Changed preposition from '{original}' to '{corrected}'."

        if orig_lower in cls.PAST_TENSE_MAP:
            expected_past = cls.PAST_TENSE_MAP[orig_lower]
            if corr_lower == expected_past:
                return "tense_error", f"Incorrect verb tense. Use '{corrected}' (past tense)."

        if orig_lower in cls.AUXILIARY_VERBS or corr_lower in cls.AUXILIARY_VERBS:
            if orig_lower == "is" and corr_lower == "are":
                return "verb_agreement_error", "Subject-verb agreement: 'are' for plural subjects."
            if orig_lower == "are" and corr_lower == "is":
                return "verb_agreement_error", "Subject-verb agreement: 'is' for singular subjects."
            if orig_lower in cls.AUXILIARY_VERBS:
                return "verb_error", f"Verb form corrected from '{original}' to '{corrected}'."

        if orig_lower.endswith("s") and not corr_lower.endswith("s"):
            return "verb_agreement_error", "Subject-verb agreement issue."
        if not orig_lower.endswith("s") and corr_lower.endswith("s"):
            return "verb_agreement_error", "Added subject-verb agreement."

        return "other_error", f"Changed '{original}' to '{corrected}'."

    @classmethod
    def detect_errors(cls, original: str, corrected: str) -> List[Dict[str, Any]]:
        """Detect errors by comparing original and corrected text."""
        if original.lower() == corrected.lower():
            return []

        original_tokens = cls._tokenize(original)
        corrected_tokens = cls._tokenize(corrected)

        errors: List[Dict[str, Any]] = []
        seen_pairs = set()

        left_tokens, right_tokens = cls._lcs_diff(original_tokens, corrected_tokens)

        i, j = 0, 0
        while i < len(left_tokens) and j < len(right_tokens):
            if left_tokens[i] == right_tokens[j]:
                i += 1
                j += 1
            else:
                error_type, explanation = cls._classify_error(left_tokens[i], right_tokens[j])
                pair = (left_tokens[i], right_tokens[j], error_type)

                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    errors.append({
                        "original": left_tokens[i],
                        "corrected": right_tokens[j],
                        "type": error_type,
                        "explanation": explanation,
                    })
                i += 1
                j += 1

        i_remain = i
        while i_remain < len(left_tokens):
            error_type = "extra_word"
            explanation = f"Unnecessary word '{left_tokens[i_remain]}' removed."
            pair = (left_tokens[i_remain], None, error_type)

            if pair not in seen_pairs:
                seen_pairs.add(pair)
                errors.append({
                    "original": left_tokens[i_remain],
                    "corrected": None,
                    "type": error_type,
                    "explanation": explanation,
                })
            i_remain += 1

        j_remain = j
        while j_remain < len(right_tokens):
            error_type = "missing_word"
            explanation = f"Missing word '{right_tokens[j_remain]}' added."
            pair = (None, right_tokens[j_remain], error_type)

            if pair not in seen_pairs:
                seen_pairs.add(pair)
                errors.append({
                    "original": None,
                    "corrected": right_tokens[j_remain],
                    "type": error_type,
                    "explanation": explanation,
                })
            j_remain += 1

        return errors

    @staticmethod
    def generate_suggestions(errors: List[Dict[str, Any]]) -> List[str]:
        """Generate overall improvement suggestions based on errors."""
        suggestions = []
        error_types = set()

        for error in errors:
            error_types.add(error.get("type", "other_error"))

        if "tense_error" in error_types:
            suggestions.append("Work on verb tense consistency (use past, present, or future tense consistently).")
        if "article_error" in error_types:
            suggestions.append("Use articles correctly (a, an, the) before nouns.")
        if "preposition_error" in error_types:
            suggestions.append("Use correct prepositions (in, on, at, etc.) with context.")
        if "verb_agreement_error" in error_types:
            suggestions.append("Ensure subject-verb agreement (singular/plural matching).")
        if "extra_word" in error_types or "missing_word" in error_types:
            suggestions.append("Avoid unnecessary filler words and ensure complete sentence structure.")
        if "verb_error" in error_types:
            suggestions.append("Use appropriate verb forms and tenses.")
        if "other_error" in error_types:
            suggestions.append("Review overall sentence structure and grammar.")

        return suggestions[:5]  # Return top 5 suggestions

    @staticmethod
    def calculate_summary(errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics of errors."""
        summary: Dict[str, int] = {"total_errors": len(errors)}
        error_types = [err.get("type", "other_error") for err in errors]

        for error_type in set(error_types):
            count = error_types.count(error_type)
            summary[f"{error_type}"] = count

        return summary


def analyze_correction(
    original: str, corrected: str
) -> Dict[str, Any]:
    """Comprehensive error analysis."""
    analyzer = ErrorAnalyzer()
    errors = analyzer.detect_errors(original, corrected)
    suggestions = analyzer.generate_suggestions(errors)
    summary = analyzer.calculate_summary(errors)

    return {
        "errors": errors,
        "suggestions": suggestions,
        "summary": summary,
    }
