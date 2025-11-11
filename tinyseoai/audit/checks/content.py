"""
Content quality checks including readability, keyword analysis, and duplicate content detection.
"""
from __future__ import annotations

import hashlib
import re
from collections import Counter
from typing import Dict, List, Set

from bs4 import BeautifulSoup
from loguru import logger

from ...data.models import Issue


class ContentAnalyzer:
    """Analyze content quality for SEO."""

    def __init__(self, html: str, url: str):
        """
        Initialize content analyzer.

        Args:
            html: HTML content to analyze
            url: URL of the page
        """
        self.html = html
        self.url = url
        self.soup = BeautifulSoup(html, "lxml")
        self.text = self._extract_text()

    def _extract_text(self) -> str:
        """Extract clean text from HTML."""
        # Remove script and style elements
        for element in self.soup.find_all(["script", "style", "nav", "header", "footer"]):
            element.decompose()

        # Get text
        text = self.soup.get_text(separator=" ", strip=True)
        return text

    def check_all(self) -> List[Issue]:
        """
        Run all content checks.

        Returns:
            List of content issues
        """
        issues = []

        issues.extend(self.check_content_length())
        issues.extend(self.check_readability())
        issues.extend(self.check_heading_content_ratio())
        issues.extend(self.check_keyword_stuffing())

        return issues

    def check_content_length(self) -> List[Issue]:
        """
        Check if content has sufficient length.

        Returns:
            List of content length issues
        """
        issues = []

        word_count = len(self.text.split())

        if word_count < 300:
            issues.append(
                Issue(
                    url=self.url,
                    type="thin_content",
                    severity="medium",
                    detail=f"Page has only {word_count} words. Aim for at least 300 words.",
                )
            )
        elif word_count < 100:
            issues.append(
                Issue(
                    url=self.url,
                    type="very_thin_content",
                    severity="high",
                    detail=f"Page has only {word_count} words. Very thin content may be penalized.",
                )
            )

        return issues

    def check_readability(self) -> List[Issue]:
        """
        Check content readability using simple metrics.

        Returns:
            List of readability issues
        """
        issues = []

        # Calculate average sentence length
        sentences = re.split(r'[.!?]+', self.text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return issues

        words = self.text.split()
        avg_sentence_length = len(words) / len(sentences) if sentences else 0

        # Check for very long sentences
        if avg_sentence_length > 25:
            issues.append(
                Issue(
                    url=self.url,
                    type="long_sentences",
                    severity="low",
                    detail=f"Average sentence length is {avg_sentence_length:.1f} words. "
                    "Consider shorter sentences for better readability.",
                )
            )

        # Calculate average word length
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0

        if avg_word_length > 6:
            issues.append(
                Issue(
                    url=self.url,
                    type="complex_vocabulary",
                    severity="info",
                    detail=f"Average word length is {avg_word_length:.1f} characters. "
                    "Consider simpler words for broader accessibility.",
                )
            )

        return issues

    def calculate_flesch_reading_ease(self) -> float:
        """
        Calculate Flesch Reading Ease score.

        Returns:
            Reading ease score (0-100, higher is easier)
        """
        words = self.text.split()
        sentences = re.split(r'[.!?]+', self.text)
        sentences = [s for s in sentences if s.strip()]

        if not words or not sentences:
            return 0.0

        # Count syllables (simplified)
        syllable_count = sum(self._count_syllables(word) for word in words)

        total_words = len(words)
        total_sentences = len(sentences)

        # Flesch Reading Ease = 206.835 - 1.015(total words/total sentences) - 84.6(total syllables/total words)
        score = (
            206.835
            - 1.015 * (total_words / total_sentences)
            - 84.6 * (syllable_count / total_words)
        )

        return max(0, min(100, score))  # Clamp between 0-100

    def _count_syllables(self, word: str) -> int:
        """
        Count syllables in a word (simplified method).

        Args:
            word: Word to count syllables in

        Returns:
            Estimated syllable count
        """
        word = word.lower().strip(".,!?;:")
        vowels = "aeiouy"

        syllable_count = 0
        previous_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel

        # Adjust for silent 'e'
        if word.endswith("e"):
            syllable_count -= 1

        # Every word has at least one syllable
        return max(1, syllable_count)

    def check_heading_content_ratio(self) -> List[Issue]:
        """
        Check ratio of heading text to body text.

        Returns:
            List of heading ratio issues
        """
        issues = []

        # Get all heading text
        headings = self.soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        heading_text = " ".join(h.get_text() for h in headings)
        heading_words = len(heading_text.split())

        total_words = len(self.text.split())

        if total_words > 0:
            heading_ratio = heading_words / total_words

            # If more than 30% of content is headings, might be thin
            if heading_ratio > 0.3:
                issues.append(
                    Issue(
                        url=self.url,
                        type="high_heading_ratio",
                        severity="low",
                        detail=f"{heading_ratio * 100:.1f}% of content is headings. "
                        "Ensure sufficient body content.",
                    )
                )

        return issues

    def check_keyword_stuffing(self) -> List[Issue]:
        """
        Check for potential keyword stuffing.

        Returns:
            List of keyword stuffing issues
        """
        issues = []

        words = [
            word.lower().strip(".,!?;:")
            for word in self.text.split()
            if len(word) > 3  # Ignore very short words
        ]

        if not words:
            return issues

        # Get word frequency
        word_freq = Counter(words)
        total_words = len(words)

        # Check for overly frequent words
        for word, count in word_freq.most_common(10):
            frequency = count / total_words

            # If any single word appears more than 5% of the time, might be stuffing
            if frequency > 0.05:
                issues.append(
                    Issue(
                        url=self.url,
                        type="potential_keyword_stuffing",
                        severity="medium",
                        detail=f"Word '{word}' appears {count} times ({frequency * 100:.1f}% of content). "
                        "May be keyword stuffing.",
                    )
                )

        return issues

    def extract_top_keywords(self, n: int = 10) -> List[Tuple[str, int]]:
        """
        Extract top keywords from content.

        Args:
            n: Number of keywords to return

        Returns:
            List of (keyword, frequency) tuples
        """
        # Common English stop words to exclude
        stop_words = {
            "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
            "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
            "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
            "or", "an", "will", "my", "one", "all", "would", "there", "their",
            "what", "so", "up", "out", "if", "about", "who", "get", "which", "go",
            "me", "when", "make", "can", "like", "time", "no", "just", "him", "know",
            "take", "people", "into", "year", "your", "good", "some", "could", "them",
            "see", "other", "than", "then", "now", "look", "only", "come", "its", "over",
            "think", "also", "back", "after", "use", "two", "how", "our", "work",
            "first", "well", "way", "even", "new", "want", "because", "any", "these",
            "give", "day", "most", "us"
        }

        words = [
            word.lower().strip(".,!?;:")
            for word in self.text.split()
            if len(word) > 3 and word.lower() not in stop_words
        ]

        word_freq = Counter(words)
        return word_freq.most_common(n)

    def get_content_metrics(self) -> Dict[str, any]:
        """
        Get comprehensive content metrics.

        Returns:
            Dictionary with content metrics
        """
        words = self.text.split()
        sentences = re.split(r'[.!?]+', self.text)
        sentences = [s for s in sentences if s.strip()]

        return {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "avg_sentence_length": len(words) / len(sentences) if sentences else 0,
            "avg_word_length": sum(len(w) for w in words) / len(words) if words else 0,
            "flesch_reading_ease": self.calculate_flesch_reading_ease(),
            "top_keywords": self.extract_top_keywords(5),
        }


class DuplicateContentDetector:
    """Detect duplicate and near-duplicate content across pages."""

    def __init__(self):
        """Initialize duplicate content detector."""
        self.content_hashes: Dict[str, List[str]] = {}  # hash -> URLs
        self.content_fingerprints: Dict[str, Set[str]] = {}  # URL -> shingles

    def add_page(self, url: str, text: str) -> None:
        """
        Add a page for duplicate detection.

        Args:
            url: URL of the page
            text: Text content of the page
        """
        # Calculate exact duplicate hash
        content_hash = hashlib.md5(text.encode()).hexdigest()
        if content_hash not in self.content_hashes:
            self.content_hashes[content_hash] = []
        self.content_hashes[content_hash].append(url)

        # Calculate content fingerprint (shingles) for near-duplicate detection
        shingles = self._create_shingles(text, k=5)
        self.content_fingerprints[url] = shingles

    def _create_shingles(self, text: str, k: int = 5) -> Set[str]:
        """
        Create k-shingles from text for similarity comparison.

        Args:
            text: Text to create shingles from
            k: Shingle size (number of words)

        Returns:
            Set of shingles
        """
        words = text.lower().split()
        shingles = set()

        for i in range(len(words) - k + 1):
            shingle = " ".join(words[i:i + k])
            shingles.add(shingle)

        return shingles

    def find_duplicates(self) -> List[Issue]:
        """
        Find duplicate content issues.

        Returns:
            List of duplicate content issues
        """
        issues = []

        # Find exact duplicates
        for content_hash, urls in self.content_hashes.items():
            if len(urls) > 1:
                for url in urls:
                    issues.append(
                        Issue(
                            url=url,
                            type="duplicate_content",
                            severity="high",
                            detail=f"Exact duplicate of {len(urls) - 1} other page(s): "
                            f"{', '.join(u for u in urls if u != url)[:200]}",
                        )
                    )

        return issues

    def find_near_duplicates(self, threshold: float = 0.8) -> List[Issue]:
        """
        Find near-duplicate content using Jaccard similarity.

        Args:
            threshold: Similarity threshold (0-1)

        Returns:
            List of near-duplicate issues
        """
        issues = []
        urls = list(self.content_fingerprints.keys())

        # Compare all pairs
        for i, url1 in enumerate(urls):
            for url2 in urls[i + 1:]:
                similarity = self._jaccard_similarity(
                    self.content_fingerprints[url1],
                    self.content_fingerprints[url2],
                )

                if similarity >= threshold:
                    issues.append(
                        Issue(
                            url=url1,
                            type="near_duplicate_content",
                            severity="medium",
                            detail=f"Near-duplicate ({similarity * 100:.1f}% similar) to: {url2}",
                        )
                    )

        return issues

    def _jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        """
        Calculate Jaccard similarity between two sets.

        Args:
            set1: First set
            set2: Second set

        Returns:
            Similarity score (0-1)
        """
        if not set1 and not set2:
            return 1.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0
